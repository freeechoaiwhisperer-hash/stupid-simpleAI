# ============================================================
#  FreedomForge AI — core/tts.py
#  Backward-compatible shim — re-exports from voice_engine
# ============================================================
from core.voice_engine import (  # noqa: F401
    init_tts,
    speak,
    tts_available,
    listen,
    sr_available,
)
