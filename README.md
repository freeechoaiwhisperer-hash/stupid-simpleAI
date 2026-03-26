# FreedomForge AI ⚒️

**Free. Local. Private. For Everyone.**

A fully local AI assistant that runs 100% on your machine — no cloud, no subscription, no data leaving your computer. Dedicated to Miranda. She will never be forgotten.

---

## Quick Install (Linux / macOS)

```bash
git clone https://github.com/freeechoaiwhisperer-hash/stupid-simpleAI.git
cd stupid-simpleAI
chmod +x setup.sh
bash setup.sh
```

The installer will:
- Check Python 3.8+ and install system dependencies
- Create a virtual environment
- Install all Python packages (customtkinter, llama-cpp-python, etc.)
- Detect your GPU and build with CUDA if available
- Create a desktop shortcut and `launch.sh`

---

## Manual Install

```bash
# 1. Install system deps (Ubuntu/Debian)
sudo apt install python3-tk portaudio19-dev python3-pyaudio

# 2. Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 3. Install Python packages
pip install -r requirements.txt

# 4. Install AI engine
pip install llama-cpp-python     # CPU
# OR for NVIDIA GPU:
CMAKE_ARGS="-DLLAMA_CUBLAS=on" FORCE_CMAKE=1 pip install llama-cpp-python

# 5. Run
python3 main.py
```

---

## Requirements

- Python 3.8+
- 2 GB+ RAM (8 GB+ recommended)
- No GPU required — optional for speed

---

## Features

- 💬 **Local AI Chat** — runs GGUF models via llama-cpp-python
- 📦 **Model Manager** — download curated models or search HuggingFace
- 🔒 **Privacy Panel** — encryption, VPN detection, network kill switch, port monitor
- 🎤 **Voice I/O** — speech recognition + text-to-speech
- 🎬 **Video Module** — ComfyUI/Wan2.1 integration
- 🤖 **Agent Mode** — execute shell commands from chat
- 🌍 **15 Languages** — full UI internationalization
- 🎨 **5 Themes** — Midnight, Forge, Aurora, Ghost, Matrix
- ⚒️ **Easter eggs** — click the logo 5 times

---

*Built by Ryan Dennison. Early Prototype — v0.1.0-alpha*
*Note: Planning for this project began in late September/early October 2025.*
