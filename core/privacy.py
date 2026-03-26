# ============================================================
#  FreedomForge AI — core/privacy.py
#  Privacy façade: wraps encryption key management +
#  network monitoring / VPN / kill-switch.
# ============================================================

import os
import base64
import hashlib
import secrets
import threading
from typing import Optional, Callable

from core import logger

# ── Crypto availability ──────────────────────────────────────

try:
    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False

KEY_FILE = ".forge_key"

# ── Key management ───────────────────────────────────────────

def generate_key() -> bytes:
    """Generate a new random Fernet key."""
    if not CRYPTO_AVAILABLE:
        return b""
    return Fernet.generate_key()


def save_key(key: bytes) -> None:
    """Save a Fernet key to the key file."""
    try:
        with open(KEY_FILE, "wb") as f:
            f.write(key)
        try:
            os.chmod(KEY_FILE, 0o600)
        except Exception:
            pass
        logger.info("Encryption key saved")
    except Exception as e:
        logger.error(f"save_key error: {e}")


def load_key() -> Optional[bytes]:
    """Load the key from the key file; returns None if not found."""
    if not CRYPTO_AVAILABLE:
        return None
    try:
        if os.path.exists(KEY_FILE):
            with open(KEY_FILE, "rb") as f:
                return f.read().strip()
    except Exception as e:
        logger.error(f"load_key error: {e}")
    return None


def get_key_fingerprint(key: bytes) -> str:
    """Return a short fingerprint for display."""
    return hashlib.sha256(key).hexdigest()[:16]


def get_or_create_key(custom_key: Optional[str] = None) -> bytes:
    """
    Returns the current key, or creates one.
    If custom_key provided, derives a Fernet key from it via PBKDF2.
    """
    if not CRYPTO_AVAILABLE:
        return b""
    if custom_key:
        salt = b"FreedomForgeAI_v1_salt_2026"
        kdf  = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=480_000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(custom_key.encode()))
        save_key(key)
        return key
    key = load_key()
    if key is None:
        key = generate_key()
        save_key(key)
    return key


# ── VPN helpers ──────────────────────────────────────────────

VPN_TOOLS: dict = {
    "mullvad": {
        "name":    "Mullvad VPN",
        "note":    "No-logs, anonymous accounts, open source.",
        "free":    False,
        "install": "https://mullvad.net/download",
        "cmd_connect":    ["mullvad", "connect"],
        "cmd_disconnect": ["mullvad", "disconnect"],
        "cmd_status":     ["mullvad", "status"],
        "status_word":    "Connected",
    },
    "protonvpn": {
        "name":    "ProtonVPN",
        "note":    "Free tier available, strong privacy policy.",
        "free":    True,
        "install": "https://protonvpn.com/download",
        "cmd_connect":    ["protonvpn-cli", "connect", "--fastest"],
        "cmd_disconnect": ["protonvpn-cli", "disconnect"],
        "cmd_status":     ["protonvpn-cli", "s"],
        "status_word":    "Connected",
    },
    "wireguard": {
        "name":    "WireGuard",
        "note":    "Fastest, modern protocol. Needs manual server setup.",
        "free":    True,
        "install": "https://www.wireguard.com/install/",
        "cmd_connect":    None,
        "cmd_disconnect": None,
        "cmd_status":     ["wg", "show"],
        "status_word":    "interface",
    },
    "openvpn": {
        "name":    "OpenVPN",
        "note":    "Open source, widely supported.",
        "free":    True,
        "install": "https://openvpn.net/community-downloads/",
        "cmd_connect":    None,
        "cmd_disconnect": None,
        "cmd_status":     None,
        "status_word":    None,
    },
}


def detect_vpn() -> Optional[str]:
    """
    Check which VPN client is installed and connected.
    Returns VPN key string or None.
    """
    import subprocess
    for key, info in VPN_TOOLS.items():
        status_cmd = info.get("cmd_status")
        status_word = info.get("status_word")
        if not status_cmd or not status_word:
            continue
        try:
            r = subprocess.run(
                status_cmd,
                capture_output=True, text=True, timeout=5)
            if r.returncode == 0 and status_word in r.stdout:
                return key
        except Exception:
            pass
    return None


def vpn_connect(on_result: Optional[Callable[[bool, str], None]] = None) -> None:
    """Connect using the detected VPN provider."""
    import subprocess

    def _run():
        detected = detect_vpn()
        if detected is None:
            # Try to find an installed client even if not connected
            detected = _find_installed_vpn()
        if detected is None:
            if on_result:
                on_result(False, "No VPN client found.")
            return
        cmd = VPN_TOOLS[detected].get("cmd_connect")
        if not cmd:
            if on_result:
                on_result(
                    False,
                    f"{VPN_TOOLS[detected]['name']} does not support "
                    "automatic connect. Please connect manually.")
            return
        try:
            r = subprocess.run(cmd, capture_output=True,
                               text=True, timeout=30)
            ok  = r.returncode == 0
            msg = r.stdout.strip() or r.stderr.strip() or \
                  ("Connected!" if ok else "Failed to connect.")
            if on_result:
                on_result(ok, msg)
        except Exception as e:
            if on_result:
                on_result(False, str(e))

    threading.Thread(target=_run, daemon=True).start()


def vpn_disconnect(
    on_result: Optional[Callable[[bool, str], None]] = None
) -> None:
    """Disconnect the active VPN."""
    import subprocess

    def _run():
        detected = detect_vpn()
        if detected is None:
            detected = _find_installed_vpn()
        if detected is None:
            if on_result:
                on_result(False, "No VPN client found.")
            return
        cmd = VPN_TOOLS[detected].get("cmd_disconnect")
        if not cmd:
            if on_result:
                on_result(
                    False,
                    f"{VPN_TOOLS[detected]['name']} does not support "
                    "automatic disconnect. Please disconnect manually.")
            return
        try:
            r = subprocess.run(cmd, capture_output=True,
                               text=True, timeout=30)
            ok  = r.returncode == 0
            msg = r.stdout.strip() or r.stderr.strip() or \
                  ("Disconnected." if ok else "Failed to disconnect.")
            if on_result:
                on_result(ok, msg)
        except Exception as e:
            if on_result:
                on_result(False, str(e))

    threading.Thread(target=_run, daemon=True).start()


def _find_installed_vpn() -> Optional[str]:
    """Return the first VPN tool whose binary exists."""
    import subprocess
    for key, info in VPN_TOOLS.items():
        cmd = info.get("cmd_status")
        if not cmd:
            continue
        try:
            subprocess.run(cmd, capture_output=True, timeout=3)
            return key
        except FileNotFoundError:
            continue
        except Exception:
            return key
    return None


# ── Network kill switch ──────────────────────────────────────

_kill_active = False


def is_kill_active() -> bool:
    return _kill_active


def network_kill(
    on_result: Optional[Callable[[bool, str], None]] = None
) -> None:
    """Cut all internet traffic immediately."""
    from core.network_monitor import kill_network
    kill_network(on_done=on_result)

    global _kill_active
    _kill_active = True


def network_restore(
    on_result: Optional[Callable[[bool, str], None]] = None
) -> None:
    """Restore normal network access."""
    from core.network_monitor import restore_network
    restore_network(on_done=on_result)

    global _kill_active
    _kill_active = False


# ── Active connections ───────────────────────────────────────

def get_active_connections() -> list:
    """
    Returns list of active connections.
    Each item: {process, local, remote, status}
    """
    from core.network_monitor import get_connections
    raw = get_connections()
    return [
        {
            "process": c.get("name", ""),
            "local":   c.get("local", "—"),
            "remote":  c.get("remote", "—"),
            "status":  c.get("status", ""),
        }
        for c in raw
    ]
