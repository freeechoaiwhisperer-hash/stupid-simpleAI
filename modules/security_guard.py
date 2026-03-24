# ============================================================
#  FreedomForge AI — modules/security_guard.py
#  Control key, integrity checks, and network kill-switch
#
#  Vision:
#  A lightweight but real security layer that:
#  - Lets the user set a personal control key that locks
#    sensitive operations (agent mode, file writes, etc.).
#  - Keeps a SHA-256 manifest of critical app files so
#    tampering is detected immediately on startup.
#  - Provides a one-call network kill-switch stub that
#    delegates to core.network_monitor when triggered.
#
#  All data is stored locally.  Nothing is sent anywhere.
# ============================================================

import hashlib
import json
import os
import secrets
import time
from pathlib import Path
from typing import Dict, Optional, Tuple

from core import logger, network_monitor

_GUARD_DIR: Path  = Path.home() / ".free_echo" / "security"
_MANIFEST_FILE    = "integrity_manifest.json"
_CONTROL_KEY_FILE = "control_key.json"

# Files checked in the integrity manifest (paths relative to project root).
# Add any files whose tampering you care about detecting.
_MONITORED_FILES = [
    "core/config.py",
    "core/encryption.py",
    "core/metadata_stamp.py",
    "core/model_manager.py",
    "core/privacy.py",
    "core/tool_repo.py",
    "core/memory_manager.py",
    "modules/__init__.py",
    "modules/agent.py",
    "modules/security_guard.py",
    "main.py",
]

# ── Control key ──────────────────────────────────────────────

class ControlKey:
    """
    A salted, hashed control key stored on disk.

    The plaintext key is never saved — only a bcrypt-style PBKDF2
    digest.  If cryptography is not installed we fall back to a
    plain SHA-256 (still useful for casual protection).
    """

    def __init__(self, guard_dir: Optional[Path] = None):
        self._guard_dir  = guard_dir or _GUARD_DIR
        self._guard_dir.mkdir(parents=True, exist_ok=True)
        self._key_path   = self._guard_dir / _CONTROL_KEY_FILE
        self._is_set     = self._key_path.exists()

    @property
    def is_set(self) -> bool:
        return self._is_set

    def set_key(self, plaintext: str) -> None:
        """Hash and persist a new control key."""
        salt   = secrets.token_hex(16)
        digest = _hash_key(plaintext, salt)
        data   = {"salt": salt, "digest": digest, "set_at": time.time()}
        self._key_path.write_text(json.dumps(data), encoding="utf-8")
        self._is_set = True
        logger.info("SecurityGuard: control key set")

    def verify(self, plaintext: str) -> bool:
        """Return True if plaintext matches the stored key."""
        if not self._is_set:
            return True          # no key set → always allow
        try:
            data   = json.loads(self._key_path.read_text(encoding="utf-8"))
            digest = _hash_key(plaintext, data["salt"])
            ok     = secrets.compare_digest(digest, data["digest"])
            if not ok:
                logger.warning("SecurityGuard: control key verification failed")
            return ok
        except Exception as exc:
            logger.error(f"SecurityGuard: verify error: {exc}")
            return False

    def clear_key(self, plaintext: str) -> bool:
        """Remove the stored key (requires current key to confirm)."""
        if not self.verify(plaintext):
            return False
        try:
            self._key_path.unlink(missing_ok=True)
        except Exception as exc:
            logger.error(f"SecurityGuard: clear_key error: {exc}")
            return False
        self._is_set = False
        logger.info("SecurityGuard: control key cleared")
        return True


def _hash_key(plaintext: str, salt: str) -> str:
    """PBKDF2-SHA256 or plain SHA-256 fallback."""
    try:
        from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
        from cryptography.hazmat.primitives import hashes
        import base64
        kdf = PBKDF2HMAC(
            algorithm  = hashes.SHA256(),
            length     = 32,
            salt       = salt.encode(),
            iterations = 260_000,
        )
        return base64.urlsafe_b64encode(
            kdf.derive(plaintext.encode())
        ).decode()
    except ImportError:
        # Fallback: simple salted SHA-256
        raw = hashlib.sha256(f"{salt}{plaintext}".encode()).hexdigest()
        return raw


# ── Integrity manifest ───────────────────────────────────────

class IntegrityChecker:
    """
    Builds a SHA-256 manifest of monitored files and checks
    that they match on subsequent runs.

    Usage (in main.py or at startup):
        checker = IntegrityChecker(project_root)
        checker.build_or_update()          # first run: creates manifest
        ok, tampered = checker.verify()    # later: checks for changes
    """

    def __init__(
        self,
        project_root: Optional[Path] = None,
        guard_dir:    Optional[Path] = None,
    ):
        self._root      = project_root or Path(os.getcwd())
        self._guard_dir = guard_dir or _GUARD_DIR
        self._guard_dir.mkdir(parents=True, exist_ok=True)
        self._manifest_path = self._guard_dir / _MANIFEST_FILE

    def build_or_update(self) -> Dict[str, str]:
        """
        Hash all monitored files and save the manifest.
        Call this on first run or after a trusted update.
        """
        manifest: Dict[str, str] = {}
        for rel in _MONITORED_FILES:
            path = self._root / rel
            if path.exists():
                manifest[rel] = _sha256(path)
        self._manifest_path.write_text(
            json.dumps(manifest, indent=2), encoding="utf-8"
        )
        logger.info(
            f"IntegrityChecker: manifest built for "
            f"{len(manifest)} file(s)"
        )
        return manifest

    @property
    def manifest_exists(self) -> bool:
        """True if a baseline manifest has been written to disk."""
        return self._manifest_path.exists()

    def verify(self) -> Tuple[bool, list]:
        """
        Compare current file hashes against the saved manifest.

        Returns (all_ok, list_of_changed_paths).

        Special cases:
        - If the manifest does not exist, returns (False, ["(no manifest)"])
          so the caller can distinguish "clean" from "never initialised / deleted".
        """
        if not self._manifest_path.exists():
            logger.info(
                "IntegrityChecker: no manifest yet — "
                "run build_or_update() first"
            )
            return False, ["(no manifest)"]

        try:
            saved = json.loads(
                self._manifest_path.read_text(encoding="utf-8")
            )
        except Exception as exc:
            logger.error(f"IntegrityChecker: load manifest error: {exc}")
            return False, ["(could not read manifest)"]

        changed = []
        for rel, expected_hash in saved.items():
            path = self._root / rel
            if not path.exists():
                changed.append(f"{rel} (missing)")
                continue
            actual = _sha256(path)
            if actual != expected_hash:
                changed.append(f"{rel} (hash mismatch)")

        if changed:
            logger.warning(
                f"IntegrityChecker: {len(changed)} file(s) changed: "
                + ", ".join(changed)
            )
        return len(changed) == 0, changed


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


# ── Network kill-switch convenience wrapper ──────────────────

def emergency_kill_network(on_done=None) -> None:
    """
    Immediately block all network traffic via core.network_monitor.

    Logs the event and then delegates to the platform-level kill
    switch.  Intended for use if the app detects unexpected
    external connections or the user hits the panic button.
    """
    logger.warning(
        "SecurityGuard: EMERGENCY NETWORK KILL triggered"
    )
    network_monitor.kill_network(on_done=on_done)


def restore_network(on_done=None) -> None:
    """Restore network access (counterpart to emergency_kill_network)."""
    network_monitor.restore_network(on_done=on_done)


# ── Singletons ───────────────────────────────────────────────

_control_key_instance:     Optional[ControlKey]      = None
_integrity_checker_instance: Optional[IntegrityChecker] = None


def get_control_key() -> ControlKey:
    """Return the process-wide singleton ControlKey instance."""
    global _control_key_instance
    if _control_key_instance is None:
        _control_key_instance = ControlKey()
    return _control_key_instance


def get_integrity_checker(project_root: Optional[Path] = None) -> IntegrityChecker:
    """Return the process-wide singleton IntegrityChecker instance."""
    global _integrity_checker_instance
    if _integrity_checker_instance is None:
        _integrity_checker_instance = IntegrityChecker(
            project_root=project_root
        )
    return _integrity_checker_instance
