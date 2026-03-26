# ============================================================
#  FreedomForge AI — core/model_downloader.py
#  Handles model download logic (stub — see ui/models_tab.py)
# ============================================================

from __future__ import annotations

import os
import threading
import requests
from typing import Callable, Optional

from utils.paths import MODELS_DIR
from utils.logger import get_logger

logger = get_logger(__name__)


def download_model(
    url: str,
    dest_filename: str,
    progress_cb: Optional[Callable[[int, int], None]] = None,
    done_cb: Optional[Callable[[str], None]] = None,
) -> threading.Thread:
    """Download a model file to MODELS_DIR in a background thread.

    Args:
        url: Direct download URL for the .gguf file.
        dest_filename: Filename to save as inside MODELS_DIR.
        progress_cb: Optional callback(bytes_done, total_bytes).
        done_cb: Optional callback(filepath) called on completion.

    Returns:
        The background Thread (already started).
    """

    def _worker():
        os.makedirs(MODELS_DIR, exist_ok=True)
        dest = os.path.join(MODELS_DIR, dest_filename)
        try:
            with requests.get(url, stream=True, timeout=30) as resp:
                resp.raise_for_status()
                total = int(resp.headers.get("content-length", 0))
                done = 0
                with open(dest, "wb") as fh:
                    for chunk in resp.iter_content(chunk_size=65536):
                        if chunk:
                            fh.write(chunk)
                            done += len(chunk)
                            if progress_cb:
                                progress_cb(done, total)
            logger.info(f"Model downloaded: {dest}")
            if done_cb:
                done_cb(dest)
        except Exception as exc:
            logger.error(f"Model download failed: {exc}")
            if done_cb:
                done_cb("")

    t = threading.Thread(target=_worker, daemon=True)
    t.start()
    return t
