# ============================================================
#  FreedomForge AI — build_windows.spec
#  PyInstaller spec for a one-folder Windows build.
#
#  Usage:
#    pip install pyinstaller
#    pyinstaller build_windows.spec
#
#  Output:  dist/FreedomForgeAI/  (folder — zip and distribute)
#  The folder can be run on any Windows 10/11 PC without Python.
# ============================================================

import sys
from pathlib import Path

block_cipher = None

# All data files that must be bundled (source, dest-in-bundle)
datas = [
    ("assets/icon.png",   "assets"),
    ("assets/i18n.py",    "assets"),
    ("assets/themes.py",  "assets"),
    ("assets/__init__.py","assets"),
]

a = Analysis(
    ["main.py"],
    pathex=[str(Path(".").resolve())],
    binaries=[],
    datas=datas,
    hiddenimports=[
        # GUI
        "customtkinter",
        "PIL",
        "PIL._tkinter_finder",
        # AI engine (optional — install before building)
        "llama_cpp",
        # Voice
        "speech_recognition",
        "pyttsx3",
        "pyaudio",
        # Crypto / system
        "cryptography",
        "cryptography.fernet",
        "cryptography.hazmat.primitives.kdf.pbkdf2",
        "psutil",
        "GPUtil",
        "requests",
        # Modules
        "modules.weather",
        "modules.agent",
        "modules.video",
        # Core
        "core.config",
        "core.logger",
        "core.model_manager",
        "core.hardware",
        "core.tts",
        "core.encryption",
        "core.privacy",
        "core.crash_reporter",
        "core.metadata_stamp",
        "core.network_monitor",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="FreedomForgeAI",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,          # No terminal window — GUI only
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon="assets/icon.png",
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="FreedomForgeAI",
)
