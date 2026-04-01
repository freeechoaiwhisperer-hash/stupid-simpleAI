# ============================================================
#  FreedomForge AI — core/config.py
#  Configuration management
# ============================================================

import os
import json

CONFIG_FILE = "config.json"

DEFAULTS = {
    "last_model":     None,
    "n_ctx":          4096,
    "voice_in":       False,
    "voice_out":      False,
    "dark_mode":      True,
    "font_size":      13,
    "unlocked":       False,
    "personality":    "normal",
    "agent_enabled":  False,
    "terms_accepted": False,
}

_config: dict = {}


def load_config() -> dict:
    global _config
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "r") as f:
                saved = json.load(f)
            _config = {**DEFAULTS, **saved}
        else:
            _config = dict(DEFAULTS)
    except Exception:
        _config = dict(DEFAULTS)
    return _config


def save_config() -> None:
    try:
        with open(CONFIG_FILE, "w") as f:
            json.dump(_config, f, indent=2)
    except Exception:
        pass


def get(key: str, fallback=None):
    return _config.get(key, DEFAULTS.get(key, fallback))


def set(key: str, value) -> None:
    _config[key] = value
    save_config()


def get_all() -> dict:
    return dict(_config)
