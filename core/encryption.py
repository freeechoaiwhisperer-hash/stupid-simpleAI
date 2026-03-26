# ============================================================
#  FreedomForge AI — core/encryption.py
#  Local data encryption — auto key for everyone,
#  manual key option for power users.
#  Nothing leaves your machine. Ever.
# ============================================================

import os
import json
import base64
import hashlib
import secrets
from typing import Optional
from utils import logger

KEY_FILE = ".forge_key"

try:
    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False

_fernet = None
_key_hash: Optional[str] = None


# ── Key management ───────────────────────────────────────────

def _derive_key(password: str, salt: bytes) -> bytes:
    """Derive a Fernet key from a password using PBKDF2."""
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=480000,
    )
    return base64.urlsafe_b64encode(
        kdf.derive(password.encode()))


def generate_auto_key() -> str:
    """Generate a random key string for auto mode."""
    return secrets.token_urlsafe(32)


def init_encryption(manual_key: Optional[str] = None) -> bool:
    """
    Initialize encryption.
    - If manual_key provided: use it (power user mode)
    - If .forge_key exists: load it (returning user)
    - Otherwise: generate new key (first run)
    Returns True if encryption is available and initialized.
    """
    global _fernet, _key_hash

    if not CRYPTO_AVAILABLE:
        logger.warning(
            "cryptography not installed — encryption disabled. "
            "Run: pip install cryptography")
        return False

    try:
        if manual_key:
            # Power user mode — derive key from their passphrase
            salt = b"FreedomForgeAI_v1_salt_2026"
            key  = _derive_key(manual_key, salt)
        elif os.path.exists(KEY_FILE):
            # Load existing auto key
            with open(KEY_FILE, "rb") as f:
                key = f.read().strip()
        else:
            # First run — generate and save auto key
            key = Fernet.generate_key()
            with open(KEY_FILE, "wb") as f:
                f.write(key)
            # Restrict file permissions on Unix
            try:
                os.chmod(KEY_FILE, 0o600)
            except Exception:
                pass
            logger.info("Encryption key generated and saved")

        _fernet   = Fernet(key)
        _key_hash = hashlib.sha256(key).hexdigest()[:16]
        logger.info(
            f"Encryption initialized (key fingerprint: {_key_hash})")
        return True

    except Exception as e:
        logger.error(f"Encryption init failed: {e}")
        return False


def get_key_fingerprint() -> Optional[str]:
    """Returns first 16 chars of key hash for display."""
    return _key_hash


def is_enabled() -> bool:
    return _fernet is not None


# ── Encrypt / Decrypt ────────────────────────────────────────

def encrypt(data: str) -> Optional[str]:
    """Encrypt a string. Returns base64 string or None on failure."""
    if not _fernet:
        return data  # Passthrough if encryption not available
    try:
        return _fernet.encrypt(data.encode()).decode()
    except Exception as e:
        logger.error(f"Encrypt error: {e}")
        return data


def decrypt(data: str) -> Optional[str]:
    """Decrypt a string. Returns plaintext or original on failure."""
    if not _fernet:
        return data
    try:
        return _fernet.decrypt(data.encode()).decode()
    except Exception as e:
        logger.error(f"Decrypt error: {e}")
        return data


def encrypt_file(path: str) -> bool:
    """Encrypt a file in place."""
    if not _fernet:
        return False
    try:
        with open(path, "rb") as f:
            data = f.read()
        encrypted = _fernet.encrypt(data)
        with open(path, "wb") as f:
            f.write(encrypted)
        return True
    except Exception as e:
        logger.error(f"File encrypt error {path}: {e}")
        return False


def decrypt_file(path: str) -> Optional[bytes]:
    """Decrypt a file and return contents without modifying file."""
    if not _fernet:
        try:
            with open(path, "rb") as f:
                return f.read()
        except Exception:
            return None
    try:
        with open(path, "rb") as f:
            data = f.read()
        return _fernet.decrypt(data)
    except Exception as e:
        logger.error(f"File decrypt error {path}: {e}")
        return None


def encrypt_dict(d: dict) -> str:
    """Encrypt a dictionary to a string."""
    return encrypt(json.dumps(d))


def decrypt_dict(s: str) -> Optional[dict]:
    """Decrypt a string back to a dictionary."""
    try:
        return json.loads(decrypt(s))
    except Exception:
        return None
