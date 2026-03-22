# Changelog

All notable changes to FreedomForge AI will be documented here.

---

## [0.1.0-alpha] — 2026-03-21

### First public release

**Core**
- Local AI chat interface — no cloud, no account, no subscription
- Hardware auto-detection — recommends the right model for your machine
- Model loading and unloading with GPU acceleration (NVIDIA CUDA)
- Multi-turn conversation memory (last 30 messages)
- Configuration system with persistent settings

**Model Library**
- 14 curated models across categories: chat, coding, uncensored, vision, multilingual
- One-click download with real-time progress
- Live HuggingFace search — find any GGUF model ever published
- Filter by category: Popular, Small, Large, Coding, Uncensored, Vision, Multilingual
- Paste URL or add local .gguf file

**Voice**
- Voice input via microphone (requires SpeechRecognition + pyaudio)
- Voice output — AI speaks responses (requires pyttsx3)
- Both toggleable on/off from the top bar

**Agent Mode**
- Toggle to allow AI to run commands on your computer
- Instant kill switch — toggle off at any time
- Blocked dangerous commands regardless of mode

**Video Module**
- Integration with ComfyUI + Wan2.1
- Route video requests from chat automatically
- Graceful fallback when ComfyUI is not running

**UI**
- Dark/light mode
- Adjustable font size
- CPU and GPU usage monitor
- Clean sidebar navigation
- Proper structured project layout

**Special**
- Miranda — first run wizard with hardware detection
- Miranda quotes — random popups dedicated to her memory
- Unlock system — enter code in Settings to access personality modes
- Three personalities: Normal, Chaos Mode (unhinged), Focus Mode
- Logo easter egg — click 5 times to cycle personalities (when unlocked)
- Full credits in About page

**Install**
- Linux: `bash setup.sh` — handles everything automatically
- Windows/Mac: manual install via `pip install -r requirements.txt`

---

*Every version will be documented here.*
*Development is slow sometimes — I'm a single father doing this in spare time.*
*But it will never stop.*
