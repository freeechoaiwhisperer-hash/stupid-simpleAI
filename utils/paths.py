# ============================================================
#  FreedomForge AI — utils/paths.py
#  Canonical path constants for the application
# ============================================================

from __future__ import annotations

import os

# Root of the installed/source package
APP_ROOT: str = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Data directories
MODELS_DIR:        str = os.path.join(APP_ROOT, "models")
LOGS_DIR:          str = os.path.join(APP_ROOT, "logs")
CRASH_REPORTS_DIR: str = os.path.join(APP_ROOT, "crash_reports")
BACKUPS_DIR:       str = os.path.join(APP_ROOT, "backups")
ASSETS_DIR:        str = os.path.join(APP_ROOT, "assets")
THEMES_DIR:        str = os.path.join(ASSETS_DIR, "themes")
ICONS_DIR:         str = os.path.join(ASSETS_DIR, "icons")
I18N_DIR:          str = os.path.join(ASSETS_DIR, "i18n")

# Config file
CONFIG_FILE: str = os.path.join(APP_ROOT, "config.json")

# Encryption key file
FORGE_KEY_FILE: str = os.path.join(APP_ROOT, ".forge_key")


def ensure_dirs() -> None:
    """Create all required runtime directories if they do not exist."""
    for d in (MODELS_DIR, LOGS_DIR, CRASH_REPORTS_DIR, BACKUPS_DIR):
        os.makedirs(d, exist_ok=True)
