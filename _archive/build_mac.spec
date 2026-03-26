# ============================================================
#  FreedomForge AI — build_mac.spec
#  PyInstaller spec for a macOS .app bundle.
#
#  Usage:
#    pip install pyinstaller
#    pyinstaller build_mac.spec
#
#  Output: dist/FreedomForgeAI.app  (drag to /Applications)
#  Tested on macOS 12 Monterey + 13 Ventura + 14 Sonoma.
#
#  NOTE: To notarise for distribution outside the App Store,
#  sign with an Apple Developer certificate:
#    codesign --deep --force --sign "Developer ID Application: ..."
#              dist/FreedomForgeAI.app
# ============================================================

import sys
from pathlib import Path

block_cipher = None

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
        "customtkinter",
        "PIL",
        "PIL._tkinter_finder",
        "llama_cpp",
        "speech_recognition",
        "pyttsx3",
        "pyaudio",
        "cryptography",
        "cryptography.fernet",
        "cryptography.hazmat.primitives.kdf.pbkdf2",
        "psutil",
        "GPUtil",
        "requests",
        "modules.weather",
        "modules.agent",
        "modules.video",
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
        "core.phone_bridge",
        "ui.phone_tab",
        "qrcode",
        "qrcode.image.pure",
        "qrcode.image.pil",
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
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=True,    # Required for macOS .app bundles
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

# Wrap into a .app bundle (macOS only)
app = BUNDLE(
    coll,
    name="FreedomForgeAI.app",
    icon="assets/icon.png",
    bundle_identifier="ai.freedomforge.app",
    info_plist={
        "NSPrincipalClass":         "NSApplication",
        "NSAppleScriptEnabled":     False,
        "CFBundleDisplayName":      "FreedomForge AI",
        "CFBundleShortVersionString":"0.1.0",
        "NSMicrophoneUsageDescription":
            "FreedomForge AI uses your microphone for voice input.",
        "NSSpeechRecognitionUsageDescription":
            "FreedomForge AI uses speech recognition for voice input.",
        "NSHighResolutionCapable":  True,
    },
)
