#!/usr/bin/env python3
# ============================================================
#  FreedomForge AI — build.py
#  Cross-platform build helper.
#
#  Run from the project root:
#    python build.py          # auto-detects your OS
#    python build.py windows  # force Windows spec
#    python build.py mac      # force Mac spec
#    python build.py linux    # build Linux AppImage via setup.sh
# ============================================================

import os
import sys
import platform
import subprocess
import shutil
from pathlib import Path

ROOT    = Path(__file__).parent.resolve()
DIST    = ROOT / "dist"
BUILD   = ROOT / "build"

SPECS = {
    "windows": ROOT / "build_windows.spec",
    "mac":     ROOT / "build_mac.spec",
}


def _check_pyinstaller():
    try:
        import PyInstaller  # noqa: F401
    except ImportError:
        print("❌  PyInstaller not found.")
        print("    Run:  pip install pyinstaller")
        sys.exit(1)


def _clean():
    print("🧹  Cleaning previous build artefacts…")
    for d in (DIST, BUILD):
        if d.exists():
            shutil.rmtree(d)


def _build(spec: Path):
    print(f"🔨  Building with {spec.name}…")
    result = subprocess.run(
        [sys.executable, "-m", "PyInstaller",
         "--noconfirm", str(spec)],
        cwd=ROOT,
    )
    if result.returncode != 0:
        print("❌  Build failed — see output above.")
        sys.exit(result.returncode)


def _report(target: str):
    out = DIST / ("FreedomForgeAI.app" if target == "mac"
                  else "FreedomForgeAI")
    if out.exists():
        print()
        print("✅  Build complete!")
        print(f"   Output: {out}")
        if target == "mac":
            print("   Drag FreedomForgeAI.app to /Applications to install.")
        elif target == "windows":
            print("   Zip the FreedomForgeAI/ folder and distribute.")
    else:
        print("⚠️   Build finished but output folder not found — check for errors.")


def main():
    # Determine target
    if len(sys.argv) > 1:
        target = sys.argv[1].lower()
    else:
        system = platform.system()
        target = {
            "Windows": "windows",
            "Darwin":  "mac",
            "Linux":   "linux",
        }.get(system, "linux")

    print()
    print(f"⚒️   FreedomForge AI — Build Helper")
    print(f"    Target: {target}")
    print()

    if target == "linux":
        print("🐧  Linux: use setup.sh to install with a virtual environment.")
        print("    Run:  bash setup.sh")
        print()
        print("    For an AppImage, install appimagetool and run:")
        print("      pyinstaller build_windows.spec  # creates a folder build")
        print("      # then wrap with appimagetool — see AppImage docs")
        sys.exit(0)

    if target not in SPECS:
        print(f"❌  Unknown target '{target}'. Choose: windows / mac / linux")
        sys.exit(1)

    _check_pyinstaller()
    _clean()
    _build(SPECS[target])
    _report(target)


if __name__ == "__main__":
    main()
