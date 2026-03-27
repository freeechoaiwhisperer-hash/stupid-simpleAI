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
import platform

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

def _import_app():
    try:
        from ui.app_window import App as AppWindow
        return AppWindow
    except ModuleNotFoundError as exc:
        if exc.name in {"tkinter", "customtkinter"}:
            system = platform.system()
            lines = [
                "FreedomForge AI could not start because the GUI dependencies are missing.",
                "",
            ]
            if system == "Linux":
                lines.extend([
                    "Linux fix:",
                    "  Run: bash setup.sh",
                    "  Or install tkinter manually: sudo apt-get install python3-tk",
                ])
            elif system == "Darwin":
                lines.extend([
                    "macOS fix:",
                    "  Run: bash setup.sh",
                    "  Or install Python from python.org / Homebrew with tkinter support.",
                ])
            else:
                lines.extend([
                    "Windows fix:",
                    "  Double-click setup.bat",
                    "  Or reinstall Python from python.org with the standard Tk components.",
                ])
            lines.extend([
                "",
                f"Missing module: {exc.name}",
            ])
            message = "\n".join(lines)
            logger.error(message)
            print(message, file=sys.stderr)
            raise SystemExit(1) from exc
        raise


App = _import_app()
_bootstrap()


def main():
    app = App()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()


if __name__ == "__main__":
    main()
