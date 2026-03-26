# ============================================================
#  FreedomForge AI — core/model_downloader.py
#  Model download manager — HuggingFace and direct URL support
# ============================================================

# TODO: Extract download logic from ui/models_tab.py into this module

import os
import threading
from typing import Callable, Optional

MODELS_DIR = "./models"


def download_model(
    url: str,
    filename: str,
    on_progress: Optional[Callable[[float], None]] = None,
    on_complete: Optional[Callable[[str], None]] = None,
    on_error: Optional[Callable[[str], None]] = None,
) -> None:
    """
    Download a model file from a URL into MODELS_DIR.
    Runs in a background thread.
    """
    raise NotImplementedError("model_downloader stub — not yet implemented")


def cancel_download() -> None:
    """Cancel any in-progress download."""
    raise NotImplementedError("model_downloader stub — not yet implemented")


def list_downloaded() -> list:
    """Return list of downloaded model filenames."""
    try:
        return [
            f for f in os.listdir(MODELS_DIR)
            if f.endswith((".gguf", ".bin", ".ggml"))
        ]
    except FileNotFoundError:
        return []
