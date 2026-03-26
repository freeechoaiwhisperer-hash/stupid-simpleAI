# FreedomForge AI

> **Early Prototype — Alpha**  
> Planning began in late September/early October 2025.

FreedomForge AI is a local, privacy-first AI assistant that runs completely offline on your machine.  
No data leaves your computer. Ever.

---

## Quick Start (One-Click Install)

### Linux / macOS

```bash
# 1. Download or unzip the project, then open a terminal in the folder
# 2. Run the installer (creates a virtual environment and installs all deps)
bash setup.sh

# 3. Launch the app
bash launch.sh
```

### Windows

```powershell
# Run the installer script from the project folder
python -m pip install -r requirements.txt
python main.py
```

---

## Requirements

| Requirement | Version |
|-------------|---------|
| Python | 3.8+ |
| RAM | 4 GB minimum (8 GB+ recommended) |
| Storage | 2–10 GB for models |
| GPU | Optional — NVIDIA CUDA for faster inference |

---

## Features (v0.1 Alpha)

- 🤖 **Local AI Chat** — run Llama, Mistral, TinyLlama and more, fully offline
- 🔒 **Privacy-First** — all data encrypted and stored locally
- 🌍 **15 Languages** — automatic system language detection
- 🎨 **5 Themes** — Midnight, Arctic, Forest, Sunset, Cyberpunk
- 🎤 **Voice I/O** — speech recognition + text-to-speech
- 🛡️ **Network Kill Switch** — cut all internet with one button
- 🔑 **Encryption** — Fernet/AES encryption for local data
- ⚡ **Agent Mode** — execute shell commands safely
- 🪄 **Setup Wizard** — guided first-run experience

---

## Project Structure

```
stupid-simpleAI/
├── main.py           ← entry point
├── setup.sh          ← one-click installer
├── requirements.txt
├── core/             ← back-end logic
│   ├── config.py
│   ├── hardware.py
│   ├── model_manager.py
│   ├── encryption.py
│   ├── privacy.py
│   ├── network_monitor.py
│   ├── tts.py
│   ├── logger.py
│   ├── crash_reporter.py
│   └── metadata_stamp.py
├── ui/               ← GUI panels (CustomTkinter)
│   ├── app.py
│   ├── chat.py
│   ├── wizard.py
│   ├── models_tab.py
│   ├── settings.py
│   ├── privacy_tab.py
│   ├── terms_tab.py
│   ├── about.py
│   └── splash.py
├── assets/           ← themes & translations
│   ├── i18n.py
│   └── themes.py
└── modules/          ← pluggable feature modules
    ├── __init__.py
    ├── agent.py
    └── video.py
```

---

## License

AGPL-3.0 + Commons Clause — see [LICENSE.md](LICENSE.md)

*Dedicated to Miranda. She will never be forgotten.*  
*Built by Ryan Dennison for his son and the world.*
