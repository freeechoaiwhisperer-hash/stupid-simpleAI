"""Tests for core/encryption.py"""

import sys
import os
import json
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import core.encryption as enc


@pytest.fixture(autouse=True)
def reset_encryption(tmp_path, monkeypatch):
    """Run each test in a clean tmp dir with reset encryption state."""
    monkeypatch.chdir(tmp_path)
    enc._fernet = None
    enc._key_hash = None
    yield
    enc._fernet = None
    enc._key_hash = None


class TestGenerateAutoKey:
    def test_returns_string(self):
        key = enc.generate_auto_key()
        assert isinstance(key, str)

    def test_returns_non_empty(self):
        assert len(enc.generate_auto_key()) > 0

    def test_unique_keys(self):
        k1 = enc.generate_auto_key()
        k2 = enc.generate_auto_key()
        assert k1 != k2


class TestInitEncryption:
    def test_init_with_manual_key(self):
        result = enc.init_encryption(manual_key="my-secret-passphrase")
        assert result is True

    def test_sets_fernet_after_init(self):
        enc.init_encryption(manual_key="test-pass")
        assert enc._fernet is not None

    def test_sets_key_hash_after_init(self):
        enc.init_encryption(manual_key="test-pass")
        assert enc._key_hash is not None

    def test_auto_key_creates_key_file(self):
        enc.init_encryption()
        assert os.path.exists(enc.KEY_FILE)

    def test_loads_existing_key_file(self, tmp_path):
        # First init creates key
        enc.init_encryption()
        first_hash = enc._key_hash
        # Reset and re-init — should load same key
        enc._fernet = None
        enc._key_hash = None
        enc.init_encryption()
        assert enc._key_hash == first_hash

    def test_returns_true_on_success(self):
        assert enc.init_encryption(manual_key="pass") is True


class TestIsEnabled:
    def test_disabled_before_init(self):
        assert enc.is_enabled() is False

    def test_enabled_after_init(self):
        enc.init_encryption(manual_key="pass")
        assert enc.is_enabled() is True


class TestGetKeyFingerprint:
    def test_none_before_init(self):
        assert enc.get_key_fingerprint() is None

    def test_returns_string_after_init(self):
        enc.init_encryption(manual_key="pass")
        fp = enc.get_key_fingerprint()
        assert isinstance(fp, str)
        assert len(fp) == 16


class TestEncryptDecrypt:
    def setup_method(self):
        enc.init_encryption(manual_key="test-key-123")

    def test_encrypt_returns_string(self):
        result = enc.encrypt("hello")
        assert isinstance(result, str)

    def test_decrypt_recovers_original(self):
        plaintext = "Hello, FreedomForge!"
        ciphertext = enc.encrypt(plaintext)
        assert enc.decrypt(ciphertext) == plaintext

    def test_encrypt_changes_data(self):
        data = "secret data"
        assert enc.encrypt(data) != data

    def test_passthrough_when_not_enabled(self):
        enc._fernet = None
        data = "plain text"
        assert enc.encrypt(data) == data

    def test_decrypt_passthrough_when_not_enabled(self):
        enc._fernet = None
        data = "plain text"
        assert enc.decrypt(data) == data

    def test_round_trip_unicode(self):
        text = "Hello 🌍 Unicode: 中文 Ñoño"
        assert enc.decrypt(enc.encrypt(text)) == text

    def test_round_trip_empty_string(self):
        assert enc.decrypt(enc.encrypt("")) == ""


class TestEncryptDecryptDict:
    def setup_method(self):
        enc.init_encryption(manual_key="dict-key")

    def test_encrypt_dict_returns_string(self):
        result = enc.encrypt_dict({"key": "value"})
        assert isinstance(result, str)

    def test_decrypt_dict_recovers_original(self):
        d = {"name": "test", "value": 42, "flag": True}
        encrypted = enc.encrypt_dict(d)
        recovered = enc.decrypt_dict(encrypted)
        assert recovered == d

    def test_decrypt_dict_invalid_returns_none(self):
        result = enc.decrypt_dict("not_valid_base64_or_encrypted_string")
        assert result is None

    def test_nested_dict(self):
        d = {"outer": {"inner": [1, 2, 3]}}
        assert enc.decrypt_dict(enc.encrypt_dict(d)) == d


class TestEncryptDecryptFile:
    def setup_method(self):
        enc.init_encryption(manual_key="file-key")

    def test_encrypt_file_modifies_content(self, tmp_path):
        f = tmp_path / "test.txt"
        original = b"secret file content"
        f.write_bytes(original)
        enc.encrypt_file(str(f))
        assert f.read_bytes() != original

    def test_decrypt_file_recovers_content(self, tmp_path):
        f = tmp_path / "test.txt"
        original = b"secret file content"
        f.write_bytes(original)
        enc.encrypt_file(str(f))
        recovered = enc.decrypt_file(str(f))
        assert recovered == original

    def test_encrypt_file_returns_false_when_disabled(self, tmp_path):
        enc._fernet = None
        f = tmp_path / "test.txt"
        f.write_bytes(b"data")
        assert enc.encrypt_file(str(f)) is False

    def test_decrypt_file_passthrough_when_disabled(self, tmp_path):
        enc._fernet = None
        f = tmp_path / "test.txt"
        original = b"raw data"
        f.write_bytes(original)
        assert enc.decrypt_file(str(f)) == original

    def test_encrypt_nonexistent_file_returns_false(self):
        assert enc.encrypt_file("/nonexistent/path/file.txt") is False

    def test_decrypt_nonexistent_file_returns_none(self):
        assert enc.decrypt_file("/nonexistent/path/file.txt") is None
