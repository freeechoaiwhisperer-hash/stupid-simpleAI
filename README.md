# FreedomForge AI

FreedomForge AI is a local-first desktop AI assistant written in Python.
It is designed to run models on your own machine, keep data private, and
provide a simple GUI for chat, model management, settings, privacy controls,
and add-on features like video generation.

This README is a quick guide to help you understand how the repository is
organized today.

## What this project does

- Runs local LLMs through `llama-cpp-python`
- Provides a desktop UI built with `customtkinter`
- Supports voice input/output
- Detects hardware and recommends model sizes
- Adds optional modules for features like video generation and command execution
- Includes local encryption, logging, and crash reporting

## Key technologies used

- **Python** — main application language
- **customtkinter** — desktop UI framework
- **llama-cpp-python** — local GGUF model inference
- **psutil** and **gputil** — hardware and system monitoring
- **SpeechRecognition**, **pyaudio**, and **pyttsx3** — voice input/output
- **cryptography** — local encryption support
- **requests** — integrations such as ComfyUI and Hugging Face queries
- **Pillow** — image and asset handling

See `requirements.txt` for the dependency list currently used by the app.

## How the app starts

The main entry point is:

- `main.py`

Startup flow:

1. `main.py` bootstraps config, logging, crash handling, and encryption
2. It imports and creates `App`
3. `app.py` shows the splash screen
4. The app checks terms acceptance and whether models are installed
5. If no models exist, the setup wizard appears
6. Otherwise the main UI is built and the last-used model can be auto-loaded

In short: `main.py` keeps startup minimal, while `app.py` coordinates the UI
and the main runtime flow.

## How the code is organized

The repository is logically split into a few areas of responsibility.

### 1. Application entry and orchestration

- `main.py` — minimal bootstrap and app launch
- `app.py` — main window, navigation, panel switching, startup flow

### 2. Core services

These files contain the app's underlying services and state management:

- `config.py` — reads and writes persistent settings
- `logger.py` — app logging
- `encryption.py` — local encryption support
- `crash_reporter.py` — global error/crash handling
- `hardware.py` — RAM/GPU detection and recommendations
- `model_manager.py` — model discovery, loading, unloading, and streaming inference
- `network_monitor.py` — privacy/network checks
- `tts.py` — text-to-speech support
- `metadata_stamp.py` — metadata stamping helpers

### 3. UI panels and windows

These files define what the user sees:

- `chat.py` — main chat experience
- `models_tab.py` — browse and manage models
- `settings.py` — theme, voice, language, and behavior settings
- `privacy_tab.py` — privacy and security information
- `terms_tab.py` — terms dialog/tab
- `about.py` — about screen and credits
- `wizard.py` — first-run setup wizard
- `splash.py` — startup splash screen
- `themes.py` — theme definitions
- `i18n.py` — translations and language strings

### 4. Feature modules

The app can route certain user prompts into feature-specific modules:

- `__init__.py` — module registry and message router
- `agent.py` — command/agent execution support
- `video.py` — video generation integration via ComfyUI

The routing pattern is simple:

1. A chat message arrives
2. The module router checks for known trigger patterns
3. If matched, the message is handled by a module
4. Otherwise the request goes through normal LLM chat inference

## Important note about structure

Some docs and file headers refer to directories like `core/`, `ui/`,
`modules/`, and `assets/`. Those names reflect the **logical structure** of the
project, but in this checkout most Python files currently live at the repository
root.

So there are really two ways to think about the project:

- **Logical organization** — core services, UI, modules, and assets
- **Current physical layout** — mostly flat files in the top-level directory

When navigating the codebase, it helps to group files mentally by responsibility
even though many of them are not yet stored in matching folders.

## A practical mental model

If you want to understand the repository quickly, start here:

1. `main.py` — startup
2. `app.py` — overall UI flow
3. `chat.py` — the main user interaction path
4. `model_manager.py` — how models are loaded and used
5. `__init__.py`, `agent.py`, and `video.py` — how feature routing works
6. `config.py`, `hardware.py`, and `encryption.py` — core support systems

## Other useful repository docs

- `CONTRIBUTING.md` — contribution guidelines and intended project structure
- `CHANGELOG.md` — release notes and feature history
- `ROADMAP.md` — planned direction of the project
- `setup.sh` — Linux setup flow

## Current state

This project is still early, but the code already has a clear separation of
responsibilities:

- startup/bootstrap
- local model management
- UI panels
- optional modules
- privacy and system support features

If you are new to the repository, think of it as a Python desktop app with a
local-LLM core and a modular feature layer on top.
