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

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils import logger
from core import settings_manager as config
from core import encryption, crash_reporter


def _bootstrap():
    config.load_config()
    logger.init()
    logger.info("FreedomForge AI starting")

    crash_reporter.install_handler()
    manual_key = config.get("manual_encryption_key", None)
    encryption.init_encryption(manual_key=manual_key)


_bootstrap()

from ui.app_window import App


def main():
    app = App()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()


if __name__ == "__main__":
    main()
