#!/bin/bash
# ============================================================
#  FreedomForge AI — One-Click Installer
#  Copyright (c) 2026 Ryan Dennison
#  Dedicated to Miranda. She will never be forgotten.
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
echo -e "${GOLD}  ⚒️   FreedomForge AI — Installer${RESET}"
echo -e "${CYAN}  Free. Private. Yours. For Everyone.${RESET}"
echo "  ─────────────────────────────────────────"
echo ""

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

mkdir -p "$SCRIPT_DIR/models"
mkdir -p "$SCRIPT_DIR/logs"
mkdir -p "$SCRIPT_DIR/assets"

# ── Python check ─────────────────────────────────────────────
echo -e "  ${CYAN}Checking Python...${RESET}"
if ! command -v python3 &>/dev/null; then
    echo -e "  ${RED}❌  Python 3 not found.${RESET}"
    echo "  Install with: sudo apt install python3 python3-pip"
    exit 1
fi

PY_MINOR=$(python3 -c 'import sys; print(sys.version_info.minor)')
PY_MAJOR=$(python3 -c 'import sys; print(sys.version_info.major)')
if [ "$PY_MAJOR" -lt 3 ] || [ "$PY_MINOR" -lt 8 ]; then
    echo -e "  ${RED}❌  Python 3.8+ required. Found: $PY_MAJOR.$PY_MINOR${RESET}"
    exit 1
fi
echo -e "  ${GREEN}✅  Python 3.$PY_MINOR found${RESET}"

# ── System packages ──────────────────────────────────────────
echo ""
echo -e "  ${CYAN}Installing system packages...${RESET}"

# tkinter
if ! python3 -c "import tkinter" &>/dev/null 2>&1; then
    echo "  📦  Installing tkinter..."
    sudo apt install python3-tk -y 2>/dev/null || \
        echo -e "  ${YELLOW}⚠️   tkinter install failed — try manually: sudo apt install python3-tk${RESET}"
fi

# Audio (for voice input)
echo "  📦  Installing audio support..."
sudo apt install portaudio19-dev python3-pyaudio -y 2>/dev/null || true

echo -e "  ${GREEN}✅  System packages done${RESET}"

# ── Virtual environment ──────────────────────────────────────
echo ""
echo -e "  ${CYAN}Creating isolated environment...${RESET}"
python3 -m venv "$SCRIPT_DIR/venv"
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

# pyaudio
pip install pyaudio --quiet 2>/dev/null || \
    echo -e "  ${YELLOW}⚠️   pyaudio optional — voice input may need manual install${RESET}"

echo -e "  ${GREEN}✅  Packages installed${RESET}"

# ── AI engine ────────────────────────────────────────────────
echo ""
echo -e "  ${CYAN}Installing AI engine (this may take a few minutes)...${RESET}"

if command -v nvidia-smi &>/dev/null && nvidia-smi &>/dev/null 2>&1; then
    echo -e "  ${GREEN}🎮  NVIDIA GPU detected — building with CUDA...${RESET}"
    CMAKE_ARGS="-DLLAMA_CUBLAS=on" FORCE_CMAKE=1 \
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
    font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 108)
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

# ── Desktop shortcut ─────────────────────────────────────────
echo ""
echo -e "  ${CYAN}Creating desktop shortcut...${RESET}"

DESKTOP="$HOME/Desktop"
mkdir -p "$DESKTOP"

cat > "$DESKTOP/FreedomForgeAI.desktop" << SHORTCUT
[Desktop Entry]
Version=1.0
Type=Application
Name=FreedomForge AI
Comment=Free local AI for everyone — Dedicated to Miranda
Exec=$SCRIPT_DIR/venv/bin/python3 $SCRIPT_DIR/main.py
Path=$SCRIPT_DIR
Icon=$SCRIPT_DIR/assets/icon.png
Terminal=false
StartupNotify=true
StartupWMClass=FreedomForgeAI
Categories=Utility;AI;Education;
SHORTCUT

chmod +x "$DESKTOP/FreedomForgeAI.desktop"

# Mark as trusted on GNOME
gio set "$DESKTOP/FreedomForgeAI.desktop" \
    metadata::trusted true 2>/dev/null || true

echo -e "  ${GREEN}✅  Desktop shortcut created${RESET}"

# ── Launch script ─────────────────────────────────────────────
cat > "$SCRIPT_DIR/launch.sh" << LAUNCHER
#!/bin/bash
cd "$SCRIPT_DIR"
source "$SCRIPT_DIR/venv/bin/activate"
python3 "$SCRIPT_DIR/main.py" "\$@"
LAUNCHER
chmod +x "$SCRIPT_DIR/launch.sh"

# ── Done ─────────────────────────────────────────────────────
echo ""
echo "  ────────────────────────────────────────────"
echo -e "  ${GREEN}✅  FreedomForge AI is installed!${RESET}"
echo ""
echo -e "  ${GOLD}▶  Double-click FreedomForgeAI on your Desktop${RESET}"
echo -e "  ${CYAN}▶  Or run: bash $SCRIPT_DIR/launch.sh${RESET}"
echo ""
echo -e "  ${CYAN}🪄  Dedicated to Miranda.${RESET}"
echo -e "  ${CYAN}    She will never be forgotten.${RESET}"
echo ""
echo "  ────────────────────────────────────────────"
echo ""

# Launch
echo -e "  ${CYAN}🚀  Launching FreedomForge AI...${RESET}"
sleep 1
source "$SCRIPT_DIR/venv/bin/activate"
python3 "$SCRIPT_DIR/main.py" &
