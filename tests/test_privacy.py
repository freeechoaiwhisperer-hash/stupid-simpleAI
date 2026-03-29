"""Tests for core/privacy.py"""

import sys
import os
import pytest
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import core.privacy as privacy


@pytest.fixture(autouse=True)
def clean_state(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    privacy._kill_active = False
    yield
    privacy._kill_active = False


class TestGenerateKey:
    def test_returns_bytes(self):
        key = privacy.generate_key()
        assert isinstance(key, bytes)

    def test_returns_non_empty(self):
        key = privacy.generate_key()
        assert len(key) > 0

    def test_keys_are_unique(self):
        assert privacy.generate_key() != privacy.generate_key()


class TestSaveAndLoadKey:
    def test_save_and_load_roundtrip(self, tmp_path):
        path = str(tmp_path / "test_key")
        key = privacy.generate_key()
        privacy.save_key(key, path)
        loaded = privacy.load_key(path)
        assert loaded == key

    def test_load_missing_file_returns_none(self, tmp_path):
        result = privacy.load_key(str(tmp_path / "nonexistent_key"))
        assert result is None

    def test_save_restricts_permissions_on_unix(self, tmp_path):
        path = str(tmp_path / "key_file")
        key = privacy.generate_key()
        privacy.save_key(key, path)
        import stat
        mode = os.stat(path).st_mode
        # Owner read/write, group and others have no permissions
        assert not (mode & stat.S_IRGRP)
        assert not (mode & stat.S_IROTH)


class TestGetOrCreateKey:
    def test_creates_key_file_on_first_run(self, tmp_path):
        result = privacy.get_or_create_key()
        assert result is not None
        assert os.path.exists(privacy.KEY_FILE)

    def test_returns_same_key_on_second_call(self, tmp_path):
        k1 = privacy.get_or_create_key()
        k2 = privacy.get_or_create_key()
        assert k1 == k2

    def test_custom_key_derivation(self):
        k1 = privacy.get_or_create_key("my-passphrase")
        k2 = privacy.get_or_create_key("my-passphrase")
        assert k1 == k2

    def test_different_passphrases_give_different_keys(self):
        k1 = privacy.get_or_create_key("passphrase-a")
        k2 = privacy.get_or_create_key("passphrase-b")
        assert k1 != k2


class TestEncryptDecryptData:
    def setup_method(self):
        self.key = privacy.generate_key()

    def test_encrypt_returns_bytes(self):
        result = privacy.encrypt_data("hello", self.key)
        assert isinstance(result, bytes)

    def test_decrypt_recovers_original(self):
        plaintext = "Hello, Privacy!"
        ciphertext = privacy.encrypt_data(plaintext, self.key)
        recovered = privacy.decrypt_data(ciphertext, self.key)
        assert recovered == plaintext

    def test_encrypt_with_empty_key_passthrough(self):
        result = privacy.encrypt_data("test", b"")
        # With empty key crypto is skipped — passthrough as bytes
        assert result == b"test"

    def test_decrypt_with_empty_key_passthrough(self):
        result = privacy.decrypt_data(b"hello", b"")
        assert result == "hello"

    def test_wrong_key_returns_none(self):
        ciphertext = privacy.encrypt_data("secret", self.key)
        wrong_key = privacy.generate_key()
        result = privacy.decrypt_data(ciphertext, wrong_key)
        assert result is None

    def test_encrypt_unicode(self):
        text = "Héllo Wörld 🌍"
        ciphertext = privacy.encrypt_data(text, self.key)
        recovered = privacy.decrypt_data(ciphertext, self.key)
        assert recovered == text


class TestGetKeyFingerprint:
    def test_returns_string(self):
        key = privacy.generate_key()
        fp = privacy.get_key_fingerprint(key)
        assert isinstance(fp, str)

    def test_format_is_four_groups(self):
        key = privacy.generate_key()
        fp = privacy.get_key_fingerprint(key)
        # Expected pattern: XXXX-XXXX-XXXX-XXXX (uppercase hex)
        parts = fp.split("-")
        assert len(parts) == 4
        assert all(len(p) == 4 for p in parts)

    def test_same_key_same_fingerprint(self):
        key = privacy.generate_key()
        assert privacy.get_key_fingerprint(key) == privacy.get_key_fingerprint(key)

    def test_different_keys_different_fingerprints(self):
        k1 = privacy.generate_key()
        k2 = privacy.generate_key()
        assert privacy.get_key_fingerprint(k1) != privacy.get_key_fingerprint(k2)


class TestIsKillActive:
    def test_not_active_by_default(self):
        assert privacy.is_kill_active() is False


class TestVpnTools:
    def test_vpn_tools_defined(self):
        assert isinstance(privacy.VPN_TOOLS, dict)
        assert len(privacy.VPN_TOOLS) > 0

    def test_mullvad_defined(self):
        assert "mullvad" in privacy.VPN_TOOLS

    def test_protonvpn_defined(self):
        assert "protonvpn" in privacy.VPN_TOOLS

    def test_each_vpn_has_required_fields(self):
        required = {"name", "install", "connect", "disconnect", "status"}
        for key, vpn in privacy.VPN_TOOLS.items():
            missing = required - set(vpn.keys())
            assert not missing, f"VPN '{key}' missing: {missing}"

    def test_vpn_connect_commands_are_lists(self):
        for key, vpn in privacy.VPN_TOOLS.items():
            assert isinstance(vpn["connect"], list)
            assert isinstance(vpn["disconnect"], list)


class TestStampCode:
    def test_stamp_code_basic(self):
        result = privacy.stamp_code("print('hi')", "session-abc")
        assert "forge:" in result
        assert "print('hi')" in result

    def test_stamp_preserves_shebang_first(self):
        code = "#!/usr/bin/env python\nprint('hello')"
        stamped = privacy.stamp_code(code, "sess")
        lines = stamped.split("\n")
        assert lines[0] == "#!/usr/bin/env python"

    def test_stamp_inserts_tag(self):
        stamped = privacy.stamp_code("x = 1\ny = 2", "mysession")
        assert "forge:" in stamped
