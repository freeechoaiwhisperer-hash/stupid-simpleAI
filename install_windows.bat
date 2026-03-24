@echo off
:: ============================================================
::  FreedomForge AI — Windows One-Click Installer
::  Copyright (c) 2026 Ryan Dennison
::  Dedicated to Miranda. She will never be forgotten.
::
::  Double-click this file to install FreedomForge AI.
::  Requirements: Windows 10 or 11 (64-bit)
:: ============================================================

title FreedomForge AI Installer

:: ── Enable colors via ANSI (Windows 10+) ───────────────────
reg add HKCU\Console /v VirtualTerminalLevel /t REG_DWORD /d 1 /f >nul 2>&1

cls
echo.
echo   [93m ^u2692^uFE0F   FreedomForge AI ^u2014 Windows Installer[0m
echo   [96m  Free. Private. Yours. For Everyone.[0m
echo   ^u2500^u2500^u2500^u2500^u2500^u2500^u2500^u2500^u2500^u2500^u2500^u2500^u2500^u2500^u2500^u2500^u2500^u2500^u2500^u2500^u2500^u2500^u2500^u2500^u2500^u2500^u2500^u2500^u2500^u2500^u2500^u2500^u2500^u2500^u2500^u2500^u2500^u2500^u2500^u2500^u2500^u2500^u2500^u2500
echo.

:: ── Set working directory to this file's location ──────────
cd /d "%~dp0"

:: ── Create needed folders ───────────────────────────────────
if not exist "models"  mkdir models
if not exist "logs"    mkdir logs
if not exist "assets"  mkdir assets

:: ── Check for Python ────────────────────────────────────────
echo   [96mChecking Python...[0m
python --version >nul 2>&1
if %errorlevel% neq 0 (
    python3 --version >nul 2>&1
)
if %errorlevel% neq 0 (
    echo   [91m^u274C  Python not found.[0m
    echo.
    echo   Please install Python 3.10 or newer from:
    echo   https://www.python.org/downloads/
    echo.
    echo   Make sure to check "Add Python to PATH" during install.
    echo.
    pause
    start https://www.python.org/downloads/
    exit /b 1
)

:: Prefer "python" over "python3" on Windows
set PYTHON=python
python --version >nul 2>&1
if %errorlevel% neq 0 set PYTHON=python3

for /f "tokens=2 delims= " %%v in ('%PYTHON% --version 2^>^&1') do set PY_VER=%%v
echo   [92m^u2705  Python %PY_VER% found[0m

:: ── Create virtual environment ──────────────────────────────
echo.
echo   [96mCreating isolated environment...[0m
if not exist "venv" (
    %PYTHON% -m venv venv
)
call venv\Scripts\activate.bat
python -m pip install --upgrade pip --quiet
echo   [92m^u2705  Virtual environment ready[0m

:: ── Install Python packages ──────────────────────────────────
echo.
echo   [96mInstalling packages (this may take a few minutes)...[0m

pip install ^
    customtkinter ^
    psutil ^
    gputil ^
    requests ^
    SpeechRecognition ^
    pyttsx3 ^
    cryptography ^
    Pillow ^
    "qrcode[pil]" ^
    --quiet

:: pyaudio (optional — voice input)
pip install pyaudio --quiet 2>nul || (
    echo   [93m^u26A0^uFE0F   pyaudio optional ^u2014 voice input may need manual install[0m
)

echo   [92m^u2705  Packages installed[0m

:: ── AI engine (llama-cpp-python) ─────────────────────────────
echo.
echo   [96mInstalling AI engine (this may take several minutes)...[0m

:: Check for NVIDIA GPU
nvidia-smi >nul 2>&1
if %errorlevel% equ 0 (
    echo   [92m^uD83C^uDFAE  NVIDIA GPU detected ^u2014 using CUDA build...[0m
    set CMAKE_ARGS=-DLLAMA_CUBLAS=on
    set FORCE_CMAKE=1
)

pip install llama-cpp-python --quiet 2>nul || (
    echo   [93m^u26A0^uFE0F   AI engine needs manual install: pip install llama-cpp-python[0m
)
echo   [92m^u2705  AI engine ready[0m

:: ── Create desktop shortcut ──────────────────────────────────
echo.
echo   [96mCreating desktop shortcut...[0m

set SCRIPT_DIR=%~dp0
set SCRIPT_DIR=%SCRIPT_DIR:~0,-1%
set DESKTOP=%USERPROFILE%\Desktop

:: Write a VBScript to create the shortcut
set VBS_TMP=%TEMP%\make_shortcut_ffai.vbs
(
  echo Set oWS = WScript.CreateObject^("WScript.Shell"^)
  echo sLinkFile = "%DESKTOP%\FreedomForge AI.lnk"
  echo Set oLink = oWS.CreateShortcut^(sLinkFile^)
  echo oLink.TargetPath = "%SCRIPT_DIR%\venv\Scripts\pythonw.exe"
  echo oLink.Arguments = """%SCRIPT_DIR%\main.py"""
  echo oLink.WorkingDirectory = "%SCRIPT_DIR%"
  echo oLink.IconLocation = "%SCRIPT_DIR%\assets\icon.png"
  echo oLink.Description = "FreedomForge AI ^u2014 Dedicated to Miranda"
  echo oLink.Save
) > "%VBS_TMP%"

cscript //nologo "%VBS_TMP%" 2>nul
del "%VBS_TMP%" 2>nul

echo   [92m^u2705  Desktop shortcut created[0m

:: ── Create launch.bat helper ──────────────────────────────────
(
  echo @echo off
  echo cd /d "%SCRIPT_DIR%"
  echo call "%SCRIPT_DIR%\venv\Scripts\activate.bat"
  echo python "%SCRIPT_DIR%\main.py" %%*
) > "%SCRIPT_DIR%\launch.bat"

:: ── Done ─────────────────────────────────────────────────────
echo.
echo   ^u2500^u2500^u2500^u2500^u2500^u2500^u2500^u2500^u2500^u2500^u2500^u2500^u2500^u2500^u2500^u2500^u2500^u2500^u2500^u2500^u2500^u2500^u2500^u2500^u2500^u2500^u2500^u2500^u2500^u2500^u2500^u2500^u2500^u2500^u2500^u2500^u2500^u2500^u2500^u2500^u2500^u2500^u2500^u2500
echo   [92m^u2705  FreedomForge AI is installed![0m
echo.
echo   [93m^u25B6  Double-click "FreedomForge AI" on your Desktop[0m
echo   [96m^u25B6  Or run: launch.bat[0m
echo.
echo   [96m^uD83E^uDE84  Dedicated to Miranda.[0m
echo   [96m    She will never be forgotten.[0m
echo.
echo   ^u2500^u2500^u2500^u2500^u2500^u2500^u2500^u2500^u2500^u2500^u2500^u2500^u2500^u2500^u2500^u2500^u2500^u2500^u2500^u2500^u2500^u2500^u2500^u2500^u2500^u2500^u2500^u2500^u2500^u2500^u2500^u2500^u2500^u2500^u2500^u2500^u2500^u2500^u2500^u2500^u2500^u2500^u2500^u2500
echo.

:: ── Launch ───────────────────────────────────────────────────
echo   [96m^uD83D^uDE80  Launching FreedomForge AI...[0m
timeout /t 2 /nobreak >nul
call venv\Scripts\activate.bat
start "" pythonw "%~dp0main.py"

exit /b 0
