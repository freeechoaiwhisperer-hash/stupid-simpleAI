# ============================================================
#  FreedomForge AI — core/privacy.py
#  Privacy and security — encryption, VPN, network control
# ============================================================

import os
import json
import hashlib
import secrets
import subprocess
import threading
import platform
from pathlib import Path
from typing import Callable, Optional
from utils import logger

# ── Encryption ───────────────────────────────────────────────

KEY_FILE = ".forge_key"
DATA_DIR = "."

try:
    from cryptography.fernet import Fernet
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False


def generate_key() -> bytes:
    """Generate a new encryption key."""
    return Fernet.generate_key() if CRYPTO_AVAILABLE else b""


def save_key(key: bytes, path: str = KEY_FILE) -> None:
    """Save encryption key to file with restricted permissions."""
    with open(path, "wb") as f:
        f.write(key)
    try:
        os.chmod(path, 0o600)
    except Exception:
        pass


def load_key(path: str = KEY_FILE) -> Optional[bytes]:
    """Load encryption key from file."""
    try:
        if os.path.exists(path):
            with open(path, "rb") as f:
                return f.read()
    except Exception:
        pass
    return None


def get_or_create_key(custom_key: str = None) -> Optional[bytes]:
    """
    Get existing key or create new one.
    If custom_key provided, derive key from it.
    """
    if not CRYPTO_AVAILABLE:
        return None

    if custom_key:
        # Derive key from user passphrase
        key_bytes = hashlib.sha256(
            custom_key.encode()).digest()
        return key_bytes[:32]

    existing = load_key()
    if existing:
        return existing

    key = generate_key()
    save_key(key)
    logger.info("New encryption key generated")
    return key


def encrypt_data(data: str, key: bytes) -> Optional[bytes]:
    """Encrypt string data."""
    if not CRYPTO_AVAILABLE or not key:
        return data.encode()
    try:
        f = Fernet(key)
        return f.encrypt(data.encode())
    except Exception as e:
        logger.error(f"Encryption failed: {e}")
        return None


def decrypt_data(data: bytes, key: bytes) -> Optional[str]:
    """Decrypt bytes to string."""
    if not CRYPTO_AVAILABLE or not key:
        return data.decode()
    try:
        f = Fernet(key)
        return f.decrypt(data).decode()
    except Exception as e:
        logger.error(f"Decryption failed: {e}")
        return None


def get_key_fingerprint(key: bytes) -> str:
    """Return a short human-readable fingerprint of the key."""
    h = hashlib.sha256(key).hexdigest()
    return f"{h[:4]}-{h[4:8]}-{h[8:12]}-{h[12:16]}".upper()


# ── Network kill switch ───────────────────────────────────────

_kill_active = False


def is_kill_active() -> bool:
    return _kill_active


def network_kill(
    on_result: Callable[[bool, str], None] = None
) -> None:
    """Cut ALL internet traffic immediately."""
    global _kill_active

    def _kill():
        global _kill_active
        system = platform.system()
        try:
            if system == "Linux":
                subprocess.run(
                    ["sudo", "iptables", "-P", "INPUT", "DROP"],
                    check=True, capture_output=True)
                subprocess.run(
                    ["sudo", "iptables", "-P", "OUTPUT", "DROP"],
                    check=True, capture_output=True)
                subprocess.run(
                    ["sudo", "iptables", "-P", "FORWARD", "DROP"],
                    check=True, capture_output=True)
            elif system == "Windows":
                subprocess.run(
                    ["netsh", "advfirewall", "set",
                     "allprofiles", "firewallpolicy",
                     "blockinbound,blockoutbound"],
                    check=True, capture_output=True)
            elif system == "Darwin":
                subprocess.run(
                    ["sudo", "pfctl", "-e"],
                    check=True, capture_output=True)

            _kill_active = True
            logger.warning("NETWORK KILL SWITCH ACTIVATED")
            if on_result:
                on_result(True, "All network traffic blocked.")

        except Exception as e:
            logger.error(f"Kill switch failed: {e}")
            if on_result:
                on_result(False, str(e))

    threading.Thread(target=_kill, daemon=True).start()


def network_restore(
    on_result: Callable[[bool, str], None] = None
) -> None:
    """Restore normal network traffic."""
    global _kill_active

    def _restore():
        global _kill_active
        system = platform.system()
        try:
            if system == "Linux":
                subprocess.run(
                    ["sudo", "iptables", "-P", "INPUT", "ACCEPT"],
                    check=True, capture_output=True)
                subprocess.run(
                    ["sudo", "iptables", "-P", "OUTPUT", "ACCEPT"],
                    check=True, capture_output=True)
                subprocess.run(
                    ["sudo", "iptables", "-P", "FORWARD", "ACCEPT"],
                    check=True, capture_output=True)
            elif system == "Windows":
                subprocess.run(
                    ["netsh", "advfirewall", "set",
                     "allprofiles", "firewallpolicy",
                     "blockinbound,allowoutbound"],
                    check=True, capture_output=True)
            elif system == "Darwin":
                subprocess.run(
                    ["sudo", "pfctl", "-d"],
                    check=True, capture_output=True)

            _kill_active = False
            logger.info("Network restored")
            if on_result:
                on_result(True, "Network traffic restored.")

        except Exception as e:
            logger.error(f"Network restore failed: {e}")
            if on_result:
                on_result(False, str(e))

    threading.Thread(target=_restore, daemon=True).start()


# ── Port monitor ──────────────────────────────────────────────

def get_active_connections() -> list:
    """Return list of active network connections."""
    try:
        import psutil
        conns = psutil.net_connections(kind="inet")
        results = []
        for c in conns:
            if c.status == "ESTABLISHED":
                try:
                    proc = psutil.Process(c.pid).name() \
                        if c.pid else "Unknown"
                except Exception:
                    proc = "Unknown"
                results.append({
                    "pid":     c.pid or 0,
                    "process": proc,
                    "local":   f"{c.laddr.ip}:{c.laddr.port}"
                               if c.laddr else "—",
                    "remote":  f"{c.raddr.ip}:{c.raddr.port}"
                               if c.raddr else "—",
                    "status":  c.status,
                })
        return results
    except Exception as e:
        logger.error(f"Port monitor error: {e}")
        return []


# ── VPN helper ────────────────────────────────────────────────

VPN_TOOLS = {
    "mullvad": {
        "name":    "Mullvad VPN",
        "install": "https://mullvad.net/download",
        "connect": ["mullvad", "connect"],
        "disconnect": ["mullvad", "disconnect"],
        "status":  ["mullvad", "status"],
        "free":    False,
        "note":    "Best for privacy. Paid service (~$5/mo). No logs.",
    },
    "protonvpn": {
        "name":    "ProtonVPN",
        "install": "https://protonvpn.com/download",
        "connect": ["protonvpn-cli", "connect", "--fastest"],
        "disconnect": ["protonvpn-cli", "disconnect"],
        "status":  ["protonvpn-cli", "status"],
        "free":    True,
        "note":    "Has a free tier. Open source. No logs.",
    },
}


def detect_vpn() -> Optional[str]:
    """Return name of installed VPN tool or None."""
    for key, vpn in VPN_TOOLS.items():
        cmd = vpn["connect"][0]
        if subprocess.run(
                ["which", cmd],
                capture_output=True).returncode == 0:
            return key
    return None


def vpn_connect(
    tool: str = None,
    on_result: Callable[[bool, str], None] = None,
) -> None:
    """Connect VPN in background thread."""
    if tool is None:
        tool = detect_vpn()
    if tool is None:
        if on_result:
            on_result(False, "No VPN client found. Install ProtonVPN or Mullvad first.")
        return

    def _connect():
        try:
            r = subprocess.run(
                VPN_TOOLS[tool]["connect"],
                capture_output=True, text=True, timeout=30)
            ok = r.returncode == 0
            msg = r.stdout.strip() or r.stderr.strip() or "Connected"
            logger.info(f"VPN connect: {tool} — {msg}")
            if on_result:
                on_result(ok, msg)
        except Exception as e:
            if on_result:
                on_result(False, str(e))

    threading.Thread(target=_connect, daemon=True).start()


def vpn_disconnect(
    tool: str = None,
    on_result: Callable[[bool, str], None] = None,
) -> None:
    """Disconnect VPN in background thread."""
    if tool is None:
        tool = detect_vpn()
    if tool is None:
        if on_result:
            on_result(False, "No VPN client found.")
        return

    def _disconnect():
        try:
            r = subprocess.run(
                VPN_TOOLS[tool]["disconnect"],
                capture_output=True, text=True, timeout=15)
            ok = r.returncode == 0
            logger.info(f"VPN disconnect: {tool}")
            if on_result:
                on_result(ok, "Disconnected")
        except Exception as e:
            if on_result:
                on_result(False, str(e))

    threading.Thread(target=_disconnect, daemon=True).start()


# ── Metadata stamping ─────────────────────────────────────────

def stamp_code(code: str, session_id: str) -> str:
    """
    Silently embed a metadata signature into generated code.
    Uses a comment style that blends into normal code.
    """
    import time
    ts   = int(time.time())
    h    = hashlib.sha256(
        f"{session_id}{ts}".encode()).hexdigest()[:12]
    tag  = f"# forge:{h}:{ts}"

    lines = code.split("\n")
    # Insert after shebang or first comment block
    insert_at = 0
    for i, line in enumerate(lines):
        if line.startswith("#") or line.startswith("//"):
            insert_at = i + 1
        else:
            break

    lines.insert(insert_at, tag)
    return "\n".join(lines)
