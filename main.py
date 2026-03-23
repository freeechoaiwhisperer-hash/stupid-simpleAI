#!/usr/bin/env python3
# ============================================================
#  FreedomForge AI
#  Copyright (c) 2026 Ryan Dennison
#  Licensed under AGPL-3.0 + Commons Clause (see LICENSE.md)
#
#  Dedicated to Miranda.
#  She will never be forgotten.
#
#  Built by Ryan Dennison for his son and the world.
#  Utilizing AI assistance.
# ============================================================

import sys
import os

# Pin the working directory to the folder containing main.py.
# This ensures config.json, logs/, models/, crash_reports/, and .forge_key
# always resolve to the right place regardless of *how* the app is launched
# (terminal, desktop shortcut, double-click, etc.).
_APP_ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(_APP_ROOT)
sys.path.insert(0, _APP_ROOT)

from core import logger, config
from core import encryption, crash_reporter


def _bootstrap():
    config.load_config()
    logger.init()
    logger.info("FreedomForge AI starting")

    crash_reporter.install_global_handler()
    manual_key = config.get("manual_encryption_key", None)
    encryption.init_encryption(manual_key=manual_key)


if __name__ == "__main__":
    _bootstrap()

    from ui.app import App

    app = App()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()
