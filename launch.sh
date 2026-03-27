#!/usr/bin/env bash
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$REPO_DIR/venv"

if [ ! -x "$VENV_DIR/bin/python" ]; then
    echo "[ERROR] Virtual environment not found. Run setup.sh first."
    exit 1
fi

exec "$VENV_DIR/bin/python" "$REPO_DIR/app.py" "$@"
