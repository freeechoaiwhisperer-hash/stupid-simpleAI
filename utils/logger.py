# ============================================================
#  FreedomForge AI — utils/logger.py
#  Application-wide logging utility (delegates to core/logger)
# ============================================================

from __future__ import annotations

import logging
from core.logger import init, info, warning, error, debug  # noqa: F401


def get_logger(name: str) -> logging.Logger:
    """Return a standard logger with the given name."""
    return logging.getLogger(name)
