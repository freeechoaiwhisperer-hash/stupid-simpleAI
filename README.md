# FreedomForge AI

**FreedomForge AI** is a local AI assistant — no cloud, no account, no subscription.  
It runs entirely on your machine using open-source models.

---

## Quick Start

```bash
pip install -e .
freedomforgeai
```

Or run directly:

```bash
python app.py
```

## Project Structure

```
FreedomForgeAI/
├── app.py                    # Entry point
├── requirements.txt
├── pyproject.toml
│
├── core/                     # Business logic
│   ├── model_manager.py      # LLM loading and inference
│   ├── hardware.py           # GPU/CPU detection
│   ├── model_downloader.py   # Model download manager (stub)
│   ├── settings_manager.py   # Configuration (config.json)
│   ├── voice_engine.py       # TTS / speech recognition
│   ├── crash_reporter.py     # Crash capture and reporting
│   ├── encryption.py         # Local data encryption
│   ├── metadata_stamp.py     # AI-generated code stamping
│   ├── network_monitor.py    # Network monitoring and kill switch
│   └── privacy.py            # Privacy and VPN helpers
│
├── ui/                       # GUI (CustomTkinter)
│   ├── app_window.py         # Main application window
│   ├── wizard.py             # First-run setup wizard
│   ├── chat.py               # Chat panel
│   ├── models_tab.py         # Model browser and downloader
│   ├── settings_tab.py       # Settings panel
│   ├── about_tab.py          # About panel
│   ├── privacy_tab.py        # Privacy and security panel
│   ├── terms_tab.py          # Terms of service panel
│   ├── splash.py             # Splash screen
│   └── components/           # Reusable widgets (stubs)
│       ├── message_bubble.py
│       ├── sidebar.py
│       └── toolbar.py
│
├── modules/                  # Optional feature modules
│   ├── agent.py              # Computer-control agent
│   ├── tools.py              # Tool registry
│   └── comfyui.py            # Video generation (ComfyUI/Wan2.1)
│
├── assets/                   # Static resources
│   ├── themes.py             # Theme definitions (Python)
│   ├── i18n.py               # Translations (Python, 15 languages)
│   ├── themes/               # Theme JSON exports
│   │   ├── light.json
│   │   └── dark.json
│   ├── icons/
│   └── i18n/                 # i18n JSON exports
│       ├── en.json
│       └── es.json
│
├── models/                   # Downloaded GGUF models go here
├── utils/                    # Shared utilities
│   ├── logger.py
│   └── paths.py
│
└── _archive/                 # Preserved original files
    ├── originals/            # Flat-layout originals pre-restructure
    ├── setup.sh
    └── installer/
```

## Requirements

- Python 3.10+
- See `requirements.txt` for package dependencies

## License

AGPL-3.0 + Commons Clause — see `LICENSE.md`

---