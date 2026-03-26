#!/usr/bin/env python3
# ============================================================
#  FreedomForge AI — app.py
#  Main entry point
#  Copyright (c) 2026 Ryan Dennison
#  Licensed under AGPL-3.0 + Commons Clause (see LICENSE.md)
# ============================================================

import sys
import os

# Pin the working directory to the folder containing app.py.
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

    try:
        from modules.security_guard import get_integrity_checker
        checker = get_integrity_checker()
        if not config.get("integrity_manifest_built", False) or not checker.manifest_exists:
            if config.get("integrity_manifest_built", False) and not checker.manifest_exists:
                logger.warning(
                    "IntegrityChecker: manifest was deleted since last install — "
                    "rebuilding from current files (no tampering can be confirmed)"
                )
            checker.build_or_update()
            config.set("integrity_manifest_built", True)
            logger.info("IntegrityChecker: baseline manifest created")
        else:
            ok, changed = checker.verify()
            if not ok:
                logger.warning(
                    f"Startup integrity check: {len(changed)} file(s) "
                    f"have changed since last verified install: {changed}"
                )
    except Exception as _exc:
        logger.error(f"IntegrityChecker setup failed: {_exc}")


def main():
    _bootstrap()

    from ui.app_window import App

    app = App()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()


if __name__ == "__main__":
    main()
