# ============================================================
#  FreedomForge AI — utils/paths.py
#  Application path helpers
# ============================================================

import os
from pathlib import Path

# Root of the application
APP_ROOT = Path(__file__).resolve().parent.parent

MODELS_DIR   = APP_ROOT / "models"
LOGS_DIR     = APP_ROOT / "logs"
CONFIG_FILE  = APP_ROOT / "config.json"
CRASH_DIR    = APP_ROOT / "crash_reports"
ASSETS_DIR   = APP_ROOT / "assets"
ICONS_DIR    = ASSETS_DIR / "icons"
THEMES_DIR   = ASSETS_DIR / "themes"
I18N_DIR     = ASSETS_DIR / "i18n"


def ensure_dirs() -> None:
    """Create all required application directories."""
    for d in [MODELS_DIR, LOGS_DIR, CRASH_DIR, ASSETS_DIR, ICONS_DIR, THEMES_DIR, I18N_DIR]:
        d.mkdir(parents=True, exist_ok=True)
