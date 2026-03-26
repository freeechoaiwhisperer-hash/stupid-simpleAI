# ============================================================
#  FreedomForge AI — core/settings_manager.py
#  High-level settings facade (delegates to core/config.py)
# ============================================================

from __future__ import annotations

from core.config import get, set, load_config, save_config  # noqa: F401

# Default values for all user-facing settings
DEFAULTS: dict = {
    # Appearance
    "theme": "Midnight",
    "dark_mode": True,
    "font_size": 14,
    "language": "en",
    # Voice
    "voice_in": False,
    "voice_out": False,
    # AI
    "context_window": 4096,
    "system_prompt": "",
    # Privacy
    "analytics_opt_in": False,
    "crash_reports": True,
    # Misc
    "first_run": True,
}


def get_setting(key: str):
    """Return the stored setting value, falling back to DEFAULTS."""
    value = get(key, None)
    if value is None:
        return DEFAULTS.get(key)
    return value


def set_setting(key: str, value) -> None:
    """Persist a setting value."""
    set(key, value)


def reset_to_defaults() -> None:
    """Reset all settings to their default values."""
    for key, value in DEFAULTS.items():
        set(key, value)
    save_config()
