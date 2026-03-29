"""Tests for utils/paths.py"""

import sys
import os
import pytest
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.paths import (
    APP_ROOT,
    MODELS_DIR,
    LOGS_DIR,
    CONFIG_FILE,
    CRASH_DIR,
    ASSETS_DIR,
    ICONS_DIR,
    THEMES_DIR,
    I18N_DIR,
    ensure_dirs,
)


class TestPathConstants:
    def test_app_root_is_path(self):
        assert isinstance(APP_ROOT, Path)

    def test_models_dir_is_under_app_root(self):
        assert str(MODELS_DIR).startswith(str(APP_ROOT))

    def test_logs_dir_is_under_app_root(self):
        assert str(LOGS_DIR).startswith(str(APP_ROOT))

    def test_config_file_is_under_app_root(self):
        assert str(CONFIG_FILE).startswith(str(APP_ROOT))

    def test_crash_dir_is_under_app_root(self):
        assert str(CRASH_DIR).startswith(str(APP_ROOT))

    def test_assets_dir_is_under_app_root(self):
        assert str(ASSETS_DIR).startswith(str(APP_ROOT))

    def test_icons_dir_is_under_assets_dir(self):
        assert str(ICONS_DIR).startswith(str(ASSETS_DIR))

    def test_themes_dir_is_under_assets_dir(self):
        assert str(THEMES_DIR).startswith(str(ASSETS_DIR))

    def test_i18n_dir_is_under_assets_dir(self):
        assert str(I18N_DIR).startswith(str(ASSETS_DIR))

    def test_config_file_named_config_json(self):
        assert CONFIG_FILE.name == "config.json"


class TestEnsureDirs:
    def test_creates_all_required_dirs(self, tmp_path, monkeypatch):
        import utils.paths as paths_module

        # Temporarily redirect paths to tmp_path
        fake_models = tmp_path / "models"
        fake_logs = tmp_path / "logs"
        fake_crash = tmp_path / "crash_reports"
        fake_assets = tmp_path / "assets"
        fake_icons = fake_assets / "icons"
        fake_themes = fake_assets / "themes"
        fake_i18n = fake_assets / "i18n"

        monkeypatch.setattr(paths_module, "MODELS_DIR", fake_models)
        monkeypatch.setattr(paths_module, "LOGS_DIR", fake_logs)
        monkeypatch.setattr(paths_module, "CRASH_DIR", fake_crash)
        monkeypatch.setattr(paths_module, "ASSETS_DIR", fake_assets)
        monkeypatch.setattr(paths_module, "ICONS_DIR", fake_icons)
        monkeypatch.setattr(paths_module, "THEMES_DIR", fake_themes)
        monkeypatch.setattr(paths_module, "I18N_DIR", fake_i18n)

        paths_module.ensure_dirs()

        for d in [fake_models, fake_logs, fake_crash,
                  fake_assets, fake_icons, fake_themes, fake_i18n]:
            assert d.is_dir(), f"Directory not created: {d}"

    def test_ensure_dirs_idempotent(self, tmp_path, monkeypatch):
        import utils.paths as paths_module

        fake_models = tmp_path / "models"
        monkeypatch.setattr(paths_module, "MODELS_DIR", fake_models)
        monkeypatch.setattr(paths_module, "LOGS_DIR", tmp_path / "logs")
        monkeypatch.setattr(paths_module, "CRASH_DIR", tmp_path / "crash_reports")
        monkeypatch.setattr(paths_module, "ASSETS_DIR", tmp_path / "assets")
        monkeypatch.setattr(paths_module, "ICONS_DIR", tmp_path / "assets" / "icons")
        monkeypatch.setattr(paths_module, "THEMES_DIR", tmp_path / "assets" / "themes")
        monkeypatch.setattr(paths_module, "I18N_DIR", tmp_path / "assets" / "i18n")

        # Calling twice should not raise
        paths_module.ensure_dirs()
        paths_module.ensure_dirs()
