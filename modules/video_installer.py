# ============================================================
#  FreedomForge AI — modules/video_installer.py
#  5-step ComfyUI + LTX-Video installer
# ============================================================

import os
import sys
import subprocess
import threading
from typing import Callable

# ── Paths ─────────────────────────────────────────────────────

COMFY_DIR      = os.path.expanduser("~/ComfyUI")
CUSTOM_NODES   = os.path.join(COMFY_DIR, "custom_nodes")
MODELS_DIR     = os.path.join(COMFY_DIR, "models", "checkpoints")
WORKFLOW_DIR   = os.path.join(COMFY_DIR, "workflows")
WORKFLOW_FILE  = os.path.join(WORKFLOW_DIR, "ltxvideo_forge.json")
COMFY_REPO     = "https://github.com/comfyanonymous/ComfyUI.git"

# ── Custom nodes (git clone — more reliable than zip download) ─
CUSTOM_NODES_REPOS = [
    {
        "name":   "ComfyUI-LTXVideo",
        "url":    "https://github.com/Lightricks/ComfyUI-LTXVideo.git",
    },
    {
        "name":   "ComfyUI-VideoHelperSuite",
        "url":    "https://github.com/Kosinkadink/ComfyUI-VideoHelperSuite.git",
    },
]

# ── LTX-Video model variants ──────────────────────────────────
LTX_MODELS = [
    {
        "vram_min": 8,
        "label":    "LTX-Video 13b (~8 GB VRAM)",
        "filename": "ltx-video-2b-v0.9.1.safetensors",
        "url": (
            "https://huggingface.co/Lightricks/LTX-Video/resolve/main/"
            "ltx-video-2b-v0.9.1.safetensors"
        ),
    },
    {
        "vram_min": 4,
        "label":    "LTX-Video 2b (~4 GB VRAM)",
        "filename": "ltx-video-2b-v0.9.1.safetensors",
        "url": (
            "https://huggingface.co/Lightricks/LTX-Video/resolve/main/"
            "ltx-video-2b-v0.9.1.safetensors"
        ),
    },
    {
        "vram_min": 0,
        "label":    "LTX-Video 2b (quantised, ~4 GB VRAM)",
        "filename": "ltx-video-2b-v0.9.1_fp8_e4m3fn.safetensors",
        "url": (
            "https://huggingface.co/Lightricks/LTX-Video/resolve/main/"
            "ltx-video-2b-v0.9.1_fp8_e4m3fn.safetensors"
        ),
    },
]

# ── Minimal LTX-Video workflow ────────────────────────────────
WORKFLOW_JSON = """{
  "1": {"class_type": "LTXVLoader",
        "inputs": {"ckpt_name": "ltx-video-2b-v0.9.1.safetensors"}},
  "2": {"class_type": "CLIPTextEncodeVideo",
        "inputs": {"text": "PROMPT_PLACEHOLDER", "clip": ["1", 1]}},
  "3": {"class_type": "LTXVSampler",
        "inputs": {"model": ["1", 0], "conditioning": ["2", 0],
                   "steps": 30, "cfg": 3.5,
                   "width": 704, "height": 480, "length": 97}},
  "4": {"class_type": "VHS_VideoCombine",
        "inputs": {"images": ["3", 0], "frame_rate": 24,
                   "filename_prefix": "forge_video"}}
}
"""


def _detect_vram() -> float:
    """Return GPU VRAM in GB, or 0.0 if no GPU detected."""
    try:
        r = subprocess.run(
            ["nvidia-smi", "--query-gpu=memory.total",
             "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=5,
        )
        if r.returncode == 0:
            return int(r.stdout.strip()) / 1024
    except Exception:
        pass
    return 0.0


def _select_model(vram_gb: float) -> dict:
    for m in LTX_MODELS:
        if vram_gb >= m["vram_min"]:
            return m
    return LTX_MODELS[-1]


def _clone_or_skip(name: str, url: str, dest: str,
                   log: Callable[[str], None]) -> bool:
    """Clone a git repo into dest; skip if already present. Returns True on success."""
    if os.path.isdir(dest):
        log(f"  {name} already installed, skipping.")
        return True
    log(f"Downloading {name}…")
    try:
        r = subprocess.run(
            ["git", "clone", "--depth=1", url, dest],
            capture_output=True, text=True, timeout=120,
        )
        if r.returncode != 0:
            log(f"❌ Failed to clone {name}: {r.stderr.strip()}")
            return False
        return True
    except FileNotFoundError:
        log(f"❌ 'git' not found — install git and retry.")
        return False
    except Exception as e:
        log(f"❌ Failed to download {name}: {e}")
        return False


def _download_model(model: dict, dest_path: str,
                    log: Callable[[str], None]) -> bool:
    """Stream-download a model file. Returns True on success."""
    if os.path.exists(dest_path):
        log("  Model already downloaded, skipping.")
        return True
    log(f"  Downloading {model['label']} …")
    try:
        import requests  # type: ignore
        os.makedirs(os.path.dirname(dest_path), exist_ok=True)
        with requests.get(model["url"], stream=True, timeout=60) as r:
            r.raise_for_status()
            total = int(r.headers.get("content-length", 0))
            done  = 0
            with open(dest_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=65536):
                    f.write(chunk)
                    done += len(chunk)
                    if total:
                        pct = done / total * 100
                        log(f"  {done // (1024**2)} MB / "
                            f"{total // (1024**2)} MB  ({pct:.1f}%)")
        return True
    except Exception as e:
        log(f"❌ Model download failed: {e}")
        return False


def install(
    on_log:      Callable[[str], None],
    on_complete: Callable[[bool, str], None],
) -> None:
    """
    Run the 5-step installation in a background thread.

    on_log(msg)              — called for each status line
    on_complete(ok, message) — called when finished
    """
    def _run():
        try:
            on_log("🎬 Starting video module installation…")

            # ── Step 1: ComfyUI ───────────────────────────────
            on_log("Step 1/5 — Checking ComfyUI…")
            if os.path.isdir(COMFY_DIR):
                on_log("  ComfyUI already present, skipping download.")
            else:
                on_log("  Cloning ComfyUI…")
                r = subprocess.run(
                    ["git", "clone", "--depth=1", COMFY_REPO, COMFY_DIR],
                    capture_output=True, text=True, timeout=300,
                )
                if r.returncode != 0:
                    on_complete(False, f"ComfyUI clone failed: {r.stderr.strip()}")
                    return
                on_log("  ✅ ComfyUI cloned.")

            # ── Step 2: ComfyUI deps ──────────────────────────
            on_log("Step 2/5 — Installing ComfyUI dependencies…")
            req_file = os.path.join(COMFY_DIR, "requirements.txt")
            if os.path.exists(req_file):
                r = subprocess.run(
                    [sys.executable, "-m", "pip", "install", "-r", req_file,
                     "--quiet", "--disable-pip-version-check"],
                    capture_output=True, text=True, timeout=300,
                )
                if r.returncode != 0:
                    on_log(f"⚠️  Dep install warning: {r.stderr.strip()[:200]}")
                else:
                    on_log("✅ ComfyUI deps installed.")
            else:
                on_log("  No requirements.txt found, skipping.")

            # ── Step 3: Custom nodes ──────────────────────────
            on_log("Step 3/5 — Installing custom nodes…")
            os.makedirs(CUSTOM_NODES, exist_ok=True)
            for node in CUSTOM_NODES_REPOS:
                dest = os.path.join(CUSTOM_NODES, node["name"])
                ok   = _clone_or_skip(node["name"], node["url"], dest, on_log)
                if not ok:
                    on_log(f"⚠️  Could not install {node['name']} (continuing).")

                # Install any node-level requirements
                node_req = os.path.join(dest, "requirements.txt")
                if ok and os.path.exists(node_req):
                    subprocess.run(
                        [sys.executable, "-m", "pip", "install", "-r", node_req,
                         "--quiet", "--disable-pip-version-check"],
                        capture_output=True, timeout=120,
                    )

            # ── Step 4: GPU + model ───────────────────────────
            on_log("Step 4/5 — Detecting GPU and selecting model…")
            vram  = _detect_vram()
            on_log(f"  Detected VRAM: {vram:.1f} GB → ", )
            model = _select_model(vram)
            on_log(f"using {model['label']}")
            os.makedirs(MODELS_DIR, exist_ok=True)
            dest_model = os.path.join(MODELS_DIR, model["filename"])
            _download_model(model, dest_model, on_log)

            # ── Step 5: Workflow + config ─────────────────────
            on_log("Step 5/5 — Writing workflow and updating config…")
            os.makedirs(WORKFLOW_DIR, exist_ok=True)
            with open(WORKFLOW_FILE, "w") as f:
                f.write(WORKFLOW_JSON)

            try:
                from core import settings_manager as config
                config.set("comfyui_dir",      COMFY_DIR)
                config.set("comfyui_workflow",  WORKFLOW_FILE)
                config.set("video_model",       model["filename"])
                on_log("✅ Configuration saved.")
            except Exception as e:
                on_log(f"⚠️  Config save warning: {e}")

            on_log("\n✅ Video module installed! Restart FreedomForge to activate it.")
            on_complete(True, "Installation complete.")

        except Exception as e:
            on_complete(False, str(e))

    threading.Thread(target=_run, daemon=True).start()
