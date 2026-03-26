#!/bin/bash
# ============================================================
#  FreedomForge AI — macOS One-Click Installer
#  Copyright (c) 2026 Ryan Dennison
#  Dedicated to Miranda. She will never be forgotten.
#
#  Double-click this file in Finder to install.
#  If macOS blocks it: right-click → Open → Open
# ============================================================

set -e

# ── Colors ───────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
GOLD='\033[0;33m'
CYAN='\033[0;36m'
RESET='\033[0m'

clear

echo ""
echo -e "${GOLD}  ⚒️   FreedomForge AI — macOS Installer${RESET}"
echo -e "${CYAN}  Free. Private. Yours. For Everyone.${RESET}"
echo "  ─────────────────────────────────────────"
echo ""

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

mkdir -p "$SCRIPT_DIR/models"
mkdir -p "$SCRIPT_DIR/logs"
mkdir -p "$SCRIPT_DIR/assets"

# ── Xcode Command Line Tools (provides git, python3 etc.) ────
if ! xcode-select -p &>/dev/null; then
    echo -e "  ${CYAN}Installing Xcode Command Line Tools...${RESET}"
    xcode-select --install 2>/dev/null || true
    echo -e "  ${YELLOW}⚠️   If a dialog appeared, click Install, then re-run this script.${RESET}"
    read -p "  Press Enter after Xcode tools are installed..."
fi

# ── Homebrew (optional, used for portaudio) ──────────────────
BREW_OK=false
if command -v brew &>/dev/null; then
    BREW_OK=true
fi

# ── Python check ─────────────────────────────────────────────
echo -e "  ${CYAN}Checking Python...${RESET}"

PYTHON=""
for cmd in python3.12 python3.11 python3.10 python3; do
    if command -v "$cmd" &>/dev/null; then
        VER=$("$cmd" -c 'import sys; print(sys.version_info.minor)')
        MAJ=$("$cmd" -c 'import sys; print(sys.version_info.major)')
        if [ "$MAJ" -ge 3 ] && [ "$VER" -ge 8 ]; then
            PYTHON="$cmd"
            break
        fi
    fi
done

if [ -z "$PYTHON" ]; then
    echo -e "  ${RED}❌  Python 3.8+ not found.${RESET}"
    echo ""
    if $BREW_OK; then
        echo -e "  ${CYAN}Installing Python via Homebrew...${RESET}"
        brew install python3
        PYTHON=python3
    else
        echo "  Please install Python from:"
        echo "  https://www.python.org/downloads/macos/"
        echo ""
        open "https://www.python.org/downloads/macos/" 2>/dev/null || true
        read -p "  Press Enter after Python is installed, then re-run..."
        exit 1
    fi
fi

PY_VER=$("$PYTHON" --version 2>&1)
echo -e "  ${GREEN}✅  $PY_VER found${RESET}"

# ── tkinter check ────────────────────────────────────────────
if ! "$PYTHON" -c "import tkinter" &>/dev/null 2>&1; then
    echo -e "  ${YELLOW}⚠️   tkinter missing — trying to fix...${RESET}"
    if $BREW_OK; then
        brew install python-tk 2>/dev/null || true
    else
        echo -e "  ${YELLOW}    Install python-tk or use the python.org installer.${RESET}"
    fi
fi

# ── Audio support (for voice input) ──────────────────────────
if $BREW_OK; then
    brew install portaudio 2>/dev/null || true
fi

# ── Virtual environment ──────────────────────────────────────
echo ""
echo -e "  ${CYAN}Creating isolated environment...${RESET}"
"$PYTHON" -m venv "$SCRIPT_DIR/venv"
source "$SCRIPT_DIR/venv/bin/activate"
pip install --upgrade pip --quiet
echo -e "  ${GREEN}✅  Virtual environment ready${RESET}"

# ── Python packages ──────────────────────────────────────────
echo ""
echo -e "  ${CYAN}Installing Python packages...${RESET}"

pip install \
    customtkinter \
    psutil \
    gputil \
    requests \
    SpeechRecognition \
    pyttsx3 \
    cryptography \
    Pillow \
    "qrcode[pil]" \
    --quiet

pip install pyaudio --quiet 2>/dev/null || \
    echo -e "  ${YELLOW}⚠️   pyaudio optional — voice input may need manual install${RESET}"

echo -e "  ${GREEN}✅  Packages installed${RESET}"

# ── AI engine ────────────────────────────────────────────────
echo ""
echo -e "  ${CYAN}Installing AI engine (this may take a few minutes)...${RESET}"

# Apple Silicon uses Metal — pass the Metal flag
ARCH=$(uname -m)
if [ "$ARCH" = "arm64" ]; then
    echo -e "  ${GREEN}🍎  Apple Silicon detected — using Metal acceleration...${RESET}"
    CMAKE_ARGS="-DLLAMA_METAL=on" FORCE_CMAKE=1 \
        pip install llama-cpp-python --quiet 2>/dev/null || \
        pip install llama-cpp-python --quiet 2>/dev/null || \
        echo -e "  ${YELLOW}⚠️   AI engine needs manual install: pip install llama-cpp-python${RESET}"
else
    pip install llama-cpp-python --quiet 2>/dev/null || \
        echo -e "  ${YELLOW}⚠️   AI engine needs manual install: pip install llama-cpp-python${RESET}"
fi

echo -e "  ${GREEN}✅  AI engine ready${RESET}"

# ── Generate icon if missing ──────────────────────────────────
if [ ! -f "$SCRIPT_DIR/assets/icon.png" ]; then
    echo ""
    echo -e "  ${CYAN}Generating app icon...${RESET}"
    python3 - << 'ICONSCRIPT'
from PIL import Image, ImageDraw, ImageFont
import os

size = 512
img  = Image.new('RGBA', (size, size), (0,0,0,0))
draw = ImageDraw.Draw(img)

draw.rounded_rectangle([0,0,512,512], radius=80, fill=(15,15,15,255))
for i in range(3):
    draw.ellipse([44+i,44+i,468-i,468-i], outline=(255,215,0,50+i*20))
draw.rounded_rectangle([108,145,404,292], radius=22, fill=(255,215,0,255))
draw.rounded_rectangle([108,145,404,180], radius=22, fill=(255,245,160,80))
draw.rounded_rectangle([222,282,290,448], radius=14, fill=(139,105,20,255))

try:
    font = ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc', 108)
except:
    font = ImageFont.load_default()
draw.text((256,218), 'F', font=font, fill=(15,15,15,210), anchor='mm')

for sx,sy,sr,op in [(132,132,13,230),(104,168,8,180),(158,102,10,200),
                     (380,132,13,230),(408,168,8,180),(354,102,10,200)]:
    draw.ellipse([sx-sr,sy-sr,sx+sr,sy+sr], fill=(255,215,0,op))

os.makedirs('assets', exist_ok=True)
img.save('assets/icon.png', 'PNG')
print('Icon generated')
ICONSCRIPT
fi

# ── macOS .app wrapper (double-clickable in Finder) ──────────
echo ""
echo -e "  ${CYAN}Creating macOS app wrapper...${RESET}"

APP_DIR="$SCRIPT_DIR/FreedomForgeAI.app"
CONTENTS="$APP_DIR/Contents"
mkdir -p "$CONTENTS/MacOS"
mkdir -p "$CONTENTS/Resources"

# Info.plist
cat > "$CONTENTS/Info.plist" << PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>CFBundleExecutable</key>       <string>launch</string>
  <key>CFBundleIdentifier</key>       <string>ai.freedomforge.app</string>
  <key>CFBundleName</key>             <string>FreedomForge AI</string>
  <key>CFBundleDisplayName</key>      <string>FreedomForge AI</string>
  <key>CFBundleVersion</key>          <string>0.1.0</string>
  <key>CFBundleShortVersionString</key><string>0.1.0</string>
  <key>CFBundlePackageType</key>      <string>APPL</string>
  <key>NSHighResolutionCapable</key>  <true/>
  <key>LSUIElement</key>              <false/>
</dict>
</plist>
PLIST

# Launcher script inside .app
cat > "$CONTENTS/MacOS/launch" << LAUNCHER
#!/bin/bash
cd "$SCRIPT_DIR"
source "$SCRIPT_DIR/venv/bin/activate"
exec python3 "$SCRIPT_DIR/main.py" "\$@"
LAUNCHER
chmod +x "$CONTENTS/MacOS/launch"

# Copy icon if it exists
if [ -f "$SCRIPT_DIR/assets/icon.png" ]; then
    cp "$SCRIPT_DIR/assets/icon.png" "$CONTENTS/Resources/icon.png"
fi

echo -e "  ${GREEN}✅  FreedomForge AI.app created${RESET}"

# ── Applications alias ────────────────────────────────────────
if [ -d "/Applications" ]; then
    rm -f "/Applications/FreedomForge AI.app" 2>/dev/null || true
    ln -sf "$APP_DIR" "/Applications/FreedomForge AI.app" 2>/dev/null && \
        echo -e "  ${GREEN}✅  Added to /Applications${RESET}" || \
        echo -e "  ${YELLOW}⚠️   Could not link to /Applications — drag FreedomForgeAI.app manually.${RESET}"
fi

# ── launch.sh helper ─────────────────────────────────────────
cat > "$SCRIPT_DIR/launch.sh" << LAUNCHER2
#!/bin/bash
cd "$SCRIPT_DIR"
source "$SCRIPT_DIR/venv/bin/activate"
python3 "$SCRIPT_DIR/main.py" "\$@"
LAUNCHER2
chmod +x "$SCRIPT_DIR/launch.sh"

# ── Done ─────────────────────────────────────────────────────
echo ""
echo "  ────────────────────────────────────────────"
echo -e "  ${GREEN}✅  FreedomForge AI is installed!${RESET}"
echo ""
echo -e "  ${GOLD}▶  Open Launchpad or /Applications → FreedomForge AI${RESET}"
echo -e "  ${CYAN}▶  Or run: bash $SCRIPT_DIR/launch.sh${RESET}"
echo ""
echo -e "  ${CYAN}🪄  Dedicated to Miranda.${RESET}"
echo -e "  ${CYAN}    She will never be forgotten.${RESET}"
echo ""
echo "  ────────────────────────────────────────────"
echo ""

# ── Launch ───────────────────────────────────────────────────
echo -e "  ${CYAN}🚀  Launching FreedomForge AI...${RESET}"
sleep 1
source "$SCRIPT_DIR/venv/bin/activate"
python3 "$SCRIPT_DIR/main.py" &
