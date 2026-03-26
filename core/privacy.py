# ============================================================
#  FreedomForge AI — core/privacy.py
#  Privacy facade — encryption, VPN detection, network kill
#  Used by ui/privacy_tab.py
# ============================================================

import os
import hashlib
import subprocess
import threading
from typing import Callable, Optional

# ── Crypto availability ──────────────────────────────────────

try:
    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    import base64
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False

KEY_FILE = ".forge_key"

# ── Key management ───────────────────────────────────────────

def generate_key() -> bytes:
    """Generate a new Fernet encryption key."""
    if not CRYPTO_AVAILABLE:
        return b""
    return Fernet.generate_key()


def save_key(key: bytes) -> None:
    """Save encryption key to disk."""
    try:
        with open(KEY_FILE, "wb") as f:
            f.write(key)
        try:
            os.chmod(KEY_FILE, 0o600)
        except Exception:
            pass
    except Exception:
        pass


def load_key() -> Optional[bytes]:
    """Load encryption key from disk. Returns None if not found."""
    if not CRYPTO_AVAILABLE:
        return None
    if not os.path.exists(KEY_FILE):
        return None
    try:
        with open(KEY_FILE, "rb") as f:
            return f.read().strip()
    except Exception:
        return None


def get_key_fingerprint(key: bytes) -> str:
    """Return a short fingerprint of the key for display."""
    return hashlib.sha256(key).hexdigest()[:16]


def get_or_create_key(custom_key: Optional[str] = None) -> Optional[bytes]:
    """
    Get existing key or create a new one.
    If custom_key provided, derive a key from it.
    """
    if not CRYPTO_AVAILABLE:
        return None
    if custom_key:
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b"FreedomForgeAI_v1_salt_2026",
            iterations=480000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(custom_key.encode()))
        save_key(key)
        return key
    key = load_key()
    if key:
        return key
    key = generate_key()
    save_key(key)
    return key


# ── VPN detection ─────────────────────────────────────────────

VPN_TOOLS = {
    "mullvad": {
        "name":    "Mullvad VPN",
        "note":    "No-logs, privacy-first VPN",
        "free":    False,
        "install": "https://mullvad.net/download",
        "cmd":     ["mullvad", "connect"],
        "dis_cmd": ["mullvad", "disconnect"],
    },
    "protonvpn": {
        "name":    "ProtonVPN",
        "note":    "Swiss-based, free tier available",
        "free":    True,
        "install": "https://protonvpn.com/download",
        "cmd":     ["protonvpn-cli", "c", "--fastest"],
        "dis_cmd": ["protonvpn-cli", "d"],
    },
    "wireguard": {
        "name":    "WireGuard",
        "note":    "Fast, modern VPN protocol",
        "free":    True,
        "install": "https://www.wireguard.com/install/",
        "cmd":     ["wg-quick", "up", "wg0"],
        "dis_cmd": ["wg-quick", "down", "wg0"],
    },
    "openvpn": {
        "name":    "OpenVPN",
        "note":    "Open-source, widely supported",
        "free":    True,
        "install": "https://openvpn.net/vpn-client/",
        "cmd":     ["openvpn", "--connect"],
        "dis_cmd": ["openvpn", "--disconnect"],
    },
}


def detect_vpn() -> Optional[str]:
    """
    Returns the key of the first installed VPN tool, or None.
    """
    checks = {
        "mullvad":   ["mullvad", "version"],
        "protonvpn": ["protonvpn-cli", "--version"],
        "wireguard": ["wg", "--version"],
        "openvpn":   ["openvpn", "--version"],
    }
    for name, cmd in checks.items():
        try:
            r = subprocess.run(
                cmd, capture_output=True, timeout=3)
            if r.returncode == 0:
                return name
        except Exception:
            pass
    return None


def vpn_connect(on_result: Callable[[bool, str], None] = None) -> None:
    """Attempt to connect the detected VPN."""
    def _connect():
        vpn = detect_vpn()
        if not vpn:
            if on_result:
                on_result(False, "No VPN client found.")
            return
        cmd = VPN_TOOLS[vpn]["cmd"]
        try:
            r = subprocess.run(
                cmd, capture_output=True, text=True, timeout=30)
            ok = r.returncode == 0
            msg = "Connected." if ok else (r.stderr.strip() or "Failed to connect.")
            if on_result:
                on_result(ok, msg)
        except Exception as e:
            if on_result:
                on_result(False, str(e))
    threading.Thread(target=_connect, daemon=True).start()


def vpn_disconnect(on_result: Callable[[bool, str], None] = None) -> None:
    """Attempt to disconnect the detected VPN."""
    def _disconnect():
        vpn = detect_vpn()
        if not vpn:
            if on_result:
                on_result(False, "No VPN client found.")
            return
        cmd = VPN_TOOLS[vpn]["dis_cmd"]
        try:
            r = subprocess.run(
                cmd, capture_output=True, text=True, timeout=30)
            ok = r.returncode == 0
            msg = "Disconnected." if ok else (r.stderr.strip() or "Failed to disconnect.")
            if on_result:
                on_result(ok, msg)
        except Exception as e:
            if on_result:
                on_result(False, str(e))
    threading.Thread(target=_disconnect, daemon=True).start()


# ── Network kill switch ──────────────────────────────────────

def is_kill_active() -> bool:
    from core.network_monitor import is_kill_active as _is_kill
    return _is_kill()


def network_kill(on_result: Callable[[bool, str], None] = None) -> None:
    from core.network_monitor import kill_network
    kill_network(on_done=on_result)


def network_restore(on_result: Callable[[bool, str], None] = None) -> None:
    from core.network_monitor import restore_network
    restore_network(on_done=on_result)


# ── Active connections ────────────────────────────────────────

def get_active_connections() -> list:
    """
    Returns active network connections as a list of dicts
    with keys: process, local, remote
    """
    from core.network_monitor import get_connections
    raw = get_connections()
    return [
        {
            "process": c.get("name", "unknown"),
            "local":   c.get("local", "—"),
            "remote":  c.get("remote", "—"),
        }
        for c in raw
        if c.get("remote", "—") != "—"
    ]
