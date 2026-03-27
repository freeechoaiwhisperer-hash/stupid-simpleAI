#!/usr/bin/env bash
# ============================================================
#  FreedomForge AI — macOS/Linux one-click installer
# ============================================================

set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$REPO_DIR/venv"
DESKTOP_DIR="${XDG_DESKTOP_DIR:-$HOME/Desktop}"
OS_NAME="$(uname -s)"

echo "======================================================="
echo "  FreedomForge AI - macOS/Linux One-Click Installer"
echo "======================================================="
echo

if ! command -v python3 >/dev/null 2>&1; then
    echo "[ERROR] Python 3.10+ is required but python3 was not found."
    exit 1
fi

if ! python3 -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)'; then
    echo "[ERROR] Python 3.10+ is required."
    exit 1
fi

if [ ! -d "$VENV_DIR" ]; then
    echo "[INFO] Creating virtual environment..."
    python3 -m venv "$VENV_DIR"
fi

if [ "$OS_NAME" = "Linux" ] && command -v apt-get >/dev/null 2>&1 && command -v sudo >/dev/null 2>&1; then
    echo "[INFO] Installing optional Linux system packages..."
    sudo apt-get update || true
    sudo apt-get install -y python3-tk portaudio19-dev python3-pyaudio || \
        echo "[WARN] Optional system packages failed; audio or Tk setup may need manual fixes."
fi

if [ "$OS_NAME" = "Darwin" ] && command -v brew >/dev/null 2>&1; then
    echo "[INFO] Installing optional macOS audio dependency..."
    brew list portaudio >/dev/null 2>&1 || brew install portaudio || \
        echo "[WARN] Optional portaudio install failed."
fi

echo "[INFO] Installing base application..."
"$VENV_DIR/bin/python" -m pip install --upgrade pip setuptools wheel
"$VENV_DIR/bin/python" -m pip install -e "$REPO_DIR"

echo "[INFO] Installing optional voice support..."
"$VENV_DIR/bin/python" -m pip install SpeechRecognition pyaudio || \
    echo "[WARN] Optional voice packages failed; voice input may need manual setup."

echo "[INFO] Installing optional llama.cpp support..."
if command -v nvidia-smi >/dev/null 2>&1; then
    CMAKE_ARGS="-DGGML_CUDA=on" FORCE_CMAKE=1 \
        "$VENV_DIR/bin/python" -m pip install llama-cpp-python || \
        echo "[WARN] Optional CUDA llama.cpp install failed."
elif [ "$OS_NAME" = "Darwin" ]; then
    CMAKE_ARGS="-DGGML_METAL=on" FORCE_CMAKE=1 \
        "$VENV_DIR/bin/python" -m pip install llama-cpp-python || \
        echo "[WARN] Optional Metal llama.cpp install failed."
else
    "$VENV_DIR/bin/python" -m pip install llama-cpp-python || \
        echo "[WARN] Optional llama.cpp install failed."
fi

chmod +x "$REPO_DIR/launch.sh"

if [ "$OS_NAME" = "Linux" ] && [ -d "$DESKTOP_DIR" ]; then
    cat > "$DESKTOP_DIR/FreedomForgeAI.desktop" <<EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=FreedomForge AI
Comment=Free local AI for everyone
Exec=$REPO_DIR/launch.sh
Path=$REPO_DIR
Terminal=false
Categories=Utility;Education;
EOF
    chmod +x "$DESKTOP_DIR/FreedomForgeAI.desktop"
fi

if [ "$OS_NAME" = "Darwin" ] && [ -d "$DESKTOP_DIR" ]; then
    cat > "$DESKTOP_DIR/FreedomForgeAI.command" <<EOF
#!/usr/bin/env bash
"$REPO_DIR/launch.sh" "\$@"
EOF
    chmod +x "$DESKTOP_DIR/FreedomForgeAI.command"
fi

echo
echo "======================================================="
echo "  Installation complete"
echo "  Launch with: $REPO_DIR/launch.sh"
echo "======================================================="
