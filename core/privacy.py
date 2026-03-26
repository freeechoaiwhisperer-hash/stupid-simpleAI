# ============================================================
#  FreedomForge AI — core/privacy.py
#  Privacy module — encryption keys, VPN detection,
#  network kill switch, and connection monitoring.
#  Everything stays local. Nothing leaves your machine.
# ============================================================

import hashlib
import os
import subprocess
import threading
from typing import Callable, Optional

from core.network_monitor import (
    kill_network, restore_network, is_kill_active, get_connections,
    check_vpn_installed,
)

try:
    from cryptography.fernet import Fernet
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False

KEY_FILE = ".forge_key"

# ── VPN tool catalog ─────────────────────────────────────────

VPN_TOOLS = {
    "mullvad": {
        "name":       "Mullvad VPN",
        "note":       "No-logs, anonymous accounts. ~$5/month.",
        "free":       False,
        "install":    "https://mullvad.net/download",
        "connect":    ["mullvad", "connect"],
        "disconnect": ["mullvad", "disconnect"],
    },
    "protonvpn": {
        "name":       "ProtonVPN",
        "note":       "Swiss-based, free tier available.",
        "free":       True,
        "install":    "https://protonvpn.com/download",
        "connect":    ["protonvpn-cli", "connect", "--fastest"],
        "disconnect": ["protonvpn-cli", "disconnect"],
    },
    "wireguard": {
        "name":       "WireGuard",
        "note":       "Fast, modern VPN protocol. Free & open source.",
        "free":       True,
        "install":    "https://www.wireguard.com/install/",
        "connect":    None,
        "disconnect": None,
    },
    "openvpn": {
        "name":       "OpenVPN",
        "note":       "Widely supported. Free & open source.",
        "free":       True,
        "install":    "https://openvpn.net/community-downloads/",
        "connect":    None,
        "disconnect": None,
    },
}

# ── Encryption key helpers ───────────────────────────────────

def load_key() -> Optional[bytes]:
    """Load existing key from .forge_key, or return None."""
    if not CRYPTO_AVAILABLE:
        return None
    if os.path.exists(KEY_FILE):
        try:
            with open(KEY_FILE, "rb") as f:
                return f.read().strip()
        except Exception:
            pass
    return None


def generate_key() -> bytes:
    """Generate a new random Fernet key."""
    if not CRYPTO_AVAILABLE:
        return b""
    return Fernet.generate_key()


def save_key(key: bytes) -> None:
    """Save key bytes to .forge_key."""
    try:
        with open(KEY_FILE, "wb") as f:
            f.write(key)
        try:
            os.chmod(KEY_FILE, 0o600)
        except Exception:
            pass
    except Exception:
        pass


def get_key_fingerprint(key: bytes) -> str:
    """Return the first 16 hex chars of the key's SHA-256 hash."""
    return hashlib.sha256(key).hexdigest()[:16]


def get_or_create_key(custom_key: Optional[str] = None) -> Optional[bytes]:
    """
    Return existing key or create a new one.
    If custom_key passphrase is supplied, derive a key from it.
    """
    from core import encryption
    if custom_key:
        encryption.init_encryption(manual_key=custom_key)
    else:
        key = generate_key()
        save_key(key)
        encryption.init_encryption()
    return load_key()


# ── VPN helpers ──────────────────────────────────────────────

def detect_vpn() -> Optional[str]:
    """
    Check which VPN clients are installed.
    Returns the key of the first detected VPN, or None.
    """
    installed = check_vpn_installed()
    for key in VPN_TOOLS:
        if installed.get(key):
            return key
    return None


def vpn_connect(on_result: Callable[[bool, str], None] = None) -> None:
    """Connect to the first detected VPN."""
    detected = detect_vpn()
    if not detected:
        if on_result:
            on_result(False, "No supported VPN found.")
        return
    cmd = VPN_TOOLS[detected].get("connect")
    if not cmd:
        if on_result:
            on_result(
                False,
                f"Auto-connect not supported for "
                f"{VPN_TOOLS[detected]['name']}. Use its app.")
        return

    def _connect():
        try:
            r = subprocess.run(
                cmd, capture_output=True, timeout=15)
            ok = r.returncode == 0
            if on_result:
                on_result(ok, "Connected!" if ok
                          else r.stderr.decode()[:120])
        except Exception as e:
            if on_result:
                on_result(False, str(e))

    threading.Thread(target=_connect, daemon=True).start()


def vpn_disconnect(on_result: Callable[[bool, str], None] = None) -> None:
    """Disconnect from the detected VPN."""
    detected = detect_vpn()
    if not detected:
        if on_result:
            on_result(False, "No supported VPN found.")
        return
    cmd = VPN_TOOLS[detected].get("disconnect")
    if not cmd:
        if on_result:
            on_result(False, "Auto-disconnect not supported. Use its app.")
        return

    def _disconnect():
        try:
            r = subprocess.run(
                cmd, capture_output=True, timeout=10)
            ok = r.returncode == 0
            if on_result:
                on_result(ok, "Disconnected." if ok
                          else r.stderr.decode()[:120])
        except Exception as e:
            if on_result:
                on_result(False, str(e))

    threading.Thread(target=_disconnect, daemon=True).start()


# ── Kill switch wrappers ─────────────────────────────────────

def network_kill(on_result: Callable[[bool, str], None] = None) -> None:
    """Activate the network kill switch."""
    kill_network(on_done=on_result)


def network_restore(on_result: Callable[[bool, str], None] = None) -> None:
    """Restore normal network access."""
    restore_network(on_done=on_result)


# ── Connection monitor ───────────────────────────────────────

def get_active_connections() -> list:
    """
    Returns list of active connections with a 'process' field
    (mapped from the 'name' field in network_monitor).
    """
    conns = get_connections()
    for c in conns:
        c["process"] = c.get("name", "")
    return conns
