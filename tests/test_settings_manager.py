"""Tests for core/settings_manager.py (config module)"""

import sys
import os
import json
import tempfile
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import core.settings_manager as config


@pytest.fixture(autouse=True)
def reset_config(tmp_path, monkeypatch):
    """Run each test with a temporary working directory and a fresh config state."""
    monkeypatch.chdir(tmp_path)
    config._config = {}
    yield
    config._config = {}


class TestDefaults:
    def test_defaults_defined(self):
        assert "last_model" in config.DEFAULTS
        assert "n_ctx" in config.DEFAULTS
        assert "dark_mode" in config.DEFAULTS

    def test_n_ctx_default(self):
        assert config.DEFAULTS["n_ctx"] == 4096

    def test_dark_mode_default_true(self):
        assert config.DEFAULTS["dark_mode"] is True


class TestLoadConfig:
    def test_returns_defaults_when_no_file(self):
        result = config.load_config()
        assert result["n_ctx"] == config.DEFAULTS["n_ctx"]
        assert result["dark_mode"] == config.DEFAULTS["dark_mode"]

    def test_loads_saved_values(self, tmp_path):
        cfg = {"n_ctx": 2048, "dark_mode": False}
        with open("config.json", "w") as f:
            json.dump(cfg, f)
        result = config.load_config()
        assert result["n_ctx"] == 2048
        assert result["dark_mode"] is False

    def test_merges_saved_with_defaults(self, tmp_path):
        cfg = {"n_ctx": 1024}
        with open("config.json", "w") as f:
            json.dump(cfg, f)
        result = config.load_config()
        # custom value applied
        assert result["n_ctx"] == 1024
        # default still present
        assert result["font_size"] == config.DEFAULTS["font_size"]

    def test_bad_json_falls_back_to_defaults(self, tmp_path):
        with open("config.json", "w") as f:
            f.write("not valid json {{")
        result = config.load_config()
        assert result == config.DEFAULTS

    def test_returns_dict(self):
        result = config.load_config()
        assert isinstance(result, dict)


class TestSaveConfig:
    def test_save_creates_file(self):
        config.load_config()
        config.save_config()
        assert os.path.exists("config.json")

    def test_save_and_reload(self):
        config.load_config()
        config._config["n_ctx"] = 8192
        config.save_config()

        config._config = {}
        loaded = config.load_config()
        assert loaded["n_ctx"] == 8192


class TestGet:
    def test_get_known_default_key(self):
        config.load_config()
        assert config.get("n_ctx") == config.DEFAULTS["n_ctx"]

    def test_get_unknown_key_with_fallback(self):
        config.load_config()
        assert config.get("nonexistent_key", "fallback") == "fallback"

    def test_get_unknown_key_no_fallback_returns_none(self):
        config.load_config()
        assert config.get("nonexistent_key") is None

    def test_get_returns_set_value(self):
        config.load_config()
        config._config["n_ctx"] = 512
        assert config.get("n_ctx") == 512


class TestSet:
    def test_set_updates_value(self):
        config.load_config()
        config.set("n_ctx", 2048)
        assert config.get("n_ctx") == 2048

    def test_set_persists_to_file(self):
        config.load_config()
        config.set("font_size", 20)
        config._config = {}
        config.load_config()
        assert config.get("font_size") == 20

    def test_set_new_key(self):
        config.load_config()
        config.set("custom_key", "custom_value")
        assert config.get("custom_key") == "custom_value"


class TestGetAll:
    def test_get_all_returns_dict(self):
        config.load_config()
        result = config.get_all()
        assert isinstance(result, dict)

    def test_get_all_is_copy(self):
        config.load_config()
        result = config.get_all()
        result["n_ctx"] = 9999
        assert config.get("n_ctx") != 9999
