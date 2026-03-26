# ============================================================
#  FreedomForge AI — modules/comfyui.py
#  ComfyUI integration stub
# ============================================================

from __future__ import annotations

import json
import urllib.request
import urllib.error
from typing import Any

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8188


def is_running(host: str = DEFAULT_HOST, port: int = DEFAULT_PORT) -> bool:
    """Return True if a ComfyUI server is reachable."""
    try:
        with urllib.request.urlopen(f"http://{host}:{port}/system_stats", timeout=2):
            return True
    except Exception:
        return False


def queue_prompt(workflow: dict[str, Any], host: str = DEFAULT_HOST, port: int = DEFAULT_PORT) -> str:
    """Submit a workflow prompt to ComfyUI and return the prompt_id.

    Args:
        workflow: ComfyUI API workflow dict.
        host: ComfyUI server host.
        port: ComfyUI server port.

    Returns:
        prompt_id string, or empty string on failure.
    """
    url = f"http://{host}:{port}/prompt"
    payload = json.dumps({"prompt": workflow}).encode("utf-8")
    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
            return data.get("prompt_id", "")
    except Exception:
        return ""


def get_history(prompt_id: str, host: str = DEFAULT_HOST, port: int = DEFAULT_PORT) -> dict:
    """Fetch the output history for a given prompt_id."""
    url = f"http://{host}:{port}/history/{prompt_id}"
    try:
        with urllib.request.urlopen(url, timeout=10) as resp:
            return json.loads(resp.read())
    except Exception:
        return {}
