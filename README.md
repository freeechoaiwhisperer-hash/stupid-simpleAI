# ⚒️ FreedomForge AI

> **Free. Local. Private. For Everyone.**

![Version](https://img.shields.io/badge/version-0.1.0--alpha-gold)
![License](https://img.shields.io/badge/license-AGPL--3.0%20%2B%20Commons%20Clause-purple)
![Platform](https://img.shields.io/badge/platform-Linux%20%7C%20Windows%20%7C%20Mac-blue)
![Status](https://img.shields.io/badge/status-Early%20Alpha-orange)

---

Installs so stupidly simple even grandma can do it.

Full access to the full power of local AI. No computer skills required.
No more paywalls. No more paying $20 a month just to ask a question.
No more being left behind because you don't speak computer.

**Plug in. Play. Save.**

This interface is free. For everyone. Forever.

---

## What it does

- 🧠 **Runs AI completely on your computer** — nothing leaves your machine
- 📦 **One-click model downloads** — browse a library of the best open source models
- 🔍 **Live HuggingFace search** — find and install any model ever published
- 🔄 **Instant model swap** — switch AI brains in one click
- 🎤 **Voice input** — speak instead of type
- 🔊 **Voice output** — AI speaks responses back to you
- 🖥️ **Hardware auto-detect** — recommends the best model for YOUR machine
- 🤖 **Agent mode** — let the AI do things on your computer (with instant kill switch)
- 🎬 **Video generation** — integrates with ComfyUI + Wan2.1
- 🔒 **100% private** — no accounts, no cloud, no tracking

---

## Install

### Linux (recommended)

```bash
git clone https://github.com/ryandennison/FreedomForgeAI
cd FreedomForgeAI
bash setup.sh
```

The installer handles everything — Python packages, system dependencies,
desktop shortcut, and launches the app. One command.

### Windows / Mac

```bash
pip install -r requirements.txt
python3 main.py
```

Windows `.exe` installer and Mac `.dmg` coming soon.

---

## Models

FreedomForge AI includes a built-in library of the best open source models,
plus live search across all of HuggingFace.

| Model | Size | RAM | Best For |
|-------|------|-----|----------|
| TinyLlama 1.1B | 670 MB | 2 GB+ | Low-end PCs |
| Phi-2 2.7B | 1.6 GB | 4 GB+ | Writing & reasoning |
| Llama 3.2 3B | 2.0 GB | 4 GB+ | General use |
| Mistral 7B | 4.1 GB | 8 GB+ | Best all-rounder |
| Dolphin Mistral 7B | 4.1 GB | 8 GB+ | Uncensored |
| Dolphin Llama 3 8B | 4.9 GB | 10 GB+ | Powerful + uncensored |
| Llama 3.1 8B | 4.9 GB | 10 GB+ | Most powerful |
| CodeLlama 7B | 3.8 GB | 8 GB+ | Coding |
| DeepSeek Coder 6.7B | 3.8 GB | 8 GB+ | Best for code |
| Gemma 2 2B | 1.6 GB | 4 GB+ | Google model |
| Qwen2.5 7B | 4.7 GB | 8 GB+ | Multilingual |
| OpenHermes 2.5 | 4.1 GB | 8 GB+ | Smart assistant |
| Mixtral 8x7B | 19 GB | 24 GB+ | GPT-4 level |
| Llava 1.6 | 4.4 GB | 8 GB+ | Can see images |

Or search HuggingFace directly from inside the app — millions of models available.

---

## Roadmap

- [ ] One-click sandbox VM — AI plays in a safe isolated box
- [ ] Phone tunnel — access your home AI from your phone securely  
- [ ] One-click modules — image gen, voice cloning, document reader
- [ ] Windows `.exe` installer wizard
- [ ] Mac `.dmg` installer
- [ ] Multi-model conversations — models working together
- [ ] Help build and train your own model

---

## Project structure

```
FreedomForgeAI/
├── main.py                    Entry point — bootstraps and launches
├── core/                      AI engine, hardware, config, voice, privacy
│   ├── config.py              Settings load/save
│   ├── hardware.py            GPU/RAM detection and model recommendations
│   ├── model_manager.py       Model loading, unloading, streaming inference
│   ├── logger.py              Rotating file logger
│   ├── encryption.py          Local data encryption (Fernet)
│   ├── privacy.py             Privacy facade — VPN, kill switch, connections
│   ├── network_monitor.py     Network connections and kill switch internals
│   ├── tts.py                 Voice input (speech recognition) and output (TTS)
│   ├── metadata_stamp.py      Silent code-generation audit stamps
│   └── crash_reporter.py      Local crash capture and optional anonymous send
├── ui/                        Every screen and panel
│   ├── app.py                 Main application window
│   ├── splash.py              Startup splash screen
│   ├── wizard.py              First-run setup wizard
│   ├── chat.py                Chat panel with streaming
│   ├── models_tab.py          Model browser and downloader
│   ├── settings.py            Settings panel (theme, voice, AI)
│   ├── privacy_tab.py         Privacy & Security panel
│   ├── terms_tab.py           Terms of Service
│   └── about.py               About panel
├── modules/                   Feature add-ons (video, agent, more coming)
│   ├── __init__.py            Module registry and message router
│   ├── video.py               Video generation via ComfyUI / Wan2.1
│   └── agent.py               Computer control / agent module
└── assets/                    Icons, translations, and themes
    ├── i18n.py                Translations (English + more coming)
    ├── themes.py              UI theme definitions
    └── icon.png               App icon
```

Clean, modular, contributor-friendly.
Each feature lives in its own file.
Adding a new capability means adding one file to `modules/`.

---

## Contributing

Everyone is welcome. You don't need to be a developer.

See [CONTRIBUTING.md](CONTRIBUTING.md) for how to help.

---

## ⚠️ Early Prototype

This is version 0.1.0-alpha. Things may break.

I am not a professional developer. I am a single father
building this in spare time, learning as I go.
Development will be slow sometimes but it will never stop.
Bear with me. File bugs. Suggest things. This is yours too.

---

## License

Free for personal use, family use, education, and small organizations.

Large commercial organizations (over $250,000 annual revenue) must
contact me for a commercial license.

See [LICENSE.md](LICENSE.md) for full terms.

---

## Built with open source

- [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter) — UI framework
- [llama-cpp-python](https://github.com/abetlen/llama-cpp-python) — AI engine
- [SpeechRecognition](https://github.com/Uberi/speech_recognition) — Voice input
- [pyttsx3](https://github.com/nateshmbhat/pyttsx3) — Voice output
- [psutil](https://github.com/giampaolo/psutil) — System monitoring
- [HuggingFace](https://huggingface.co) — Model hosting
- [TheBloke](https://huggingface.co/TheBloke) / [bartowski](https://huggingface.co/bartowski) — GGUF conversions

---

## 🪄 Dedicated to Miranda

She was a friend. A light. A reason.

She never got to see what AI would become.
She is the reason this is free, and the reason it always will be.

**She will never be forgotten.**

---

> *"I built this because I watched AI become the most powerful tool*
> *in human history — and then watched companies build walls around it*
> *so only people with money could use it.*
>
> *I don't think that's okay.*
>
> *This is free. It will always be free. Use it kindly."*

**Built by Ryan Dennison for his son and the world. Utilizing AI assistance.**
