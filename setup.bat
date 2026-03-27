@echo off
setlocal EnableExtensions EnableDelayedExpansion

set "REPO_DIR=%~dp0"
set "VENV_DIR=%REPO_DIR%venv"
set "DESKTOP_DIR=%USERPROFILE%\Desktop"
set "LAUNCHER=%REPO_DIR%launch.bat"

echo =======================================================
echo   FreedomForge AI - Windows One-Click Installer
echo =======================================================
echo.

python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python 3.10+ is required and was not found in PATH.
    echo Install Python from https://www.python.org/downloads/
    echo Make sure "Add Python to PATH" is enabled.
    pause
    exit /b 1
)

python -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)"
if errorlevel 1 (
    echo [ERROR] Python 3.10+ is required.
    pause
    exit /b 1
)

if not exist "%VENV_DIR%\Scripts\python.exe" (
    echo [INFO] Creating virtual environment...
    python -m venv "%VENV_DIR%"
)

call "%VENV_DIR%\Scripts\activate.bat"
if errorlevel 1 (
    echo [ERROR] Failed to activate virtual environment.
    pause
    exit /b 1
)

echo [INFO] Installing base application...
python -m pip install --upgrade pip setuptools wheel
python -m pip install -e "%REPO_DIR%"
if errorlevel 1 (
    echo [ERROR] Base application install failed.
    pause
    exit /b 1
)

echo [INFO] Installing optional voice support...
python -m pip install SpeechRecognition pyaudio
if errorlevel 1 (
    echo [WARN] Optional voice packages failed; microphone input may need manual setup.
)

echo [INFO] Installing optional llama.cpp support...
nvidia-smi >nul 2>&1
if errorlevel 1 (
    python -m pip install llama-cpp-python
) else (
    set "CMAKE_ARGS=-DGGML_CUDA=on"
    set "FORCE_CMAKE=1"
    python -m pip install llama-cpp-python
)
if errorlevel 1 (
    echo [WARN] Optional llama.cpp install failed; local GGUF models may need manual setup.
)

if not exist "%LAUNCHER%" (
    >"%LAUNCHER%" (
        echo @echo off
        echo setlocal EnableExtensions
        echo call "%%~dp0venv\Scripts\activate.bat"
        echo python "%%~dp0app.py" %%*
    )
)

if exist "%DESKTOP_DIR%" (
    echo [INFO] Creating desktop shortcut...
    powershell -NoProfile -ExecutionPolicy Bypass -Command ^
        "$shell = New-Object -ComObject WScript.Shell; " ^
        "$shortcut = $shell.CreateShortcut('%DESKTOP_DIR%\FreedomForge AI.lnk'); " ^
        "$shortcut.TargetPath = '%COMSPEC%'; " ^
        "$shortcut.Arguments = '/c """"%LAUNCHER%""""'; " ^
        "$shortcut.WorkingDirectory = '%REPO_DIR%'; " ^
        "$shortcut.Save()"
)

echo.
echo =======================================================
echo   Installation complete
echo   Launch with launch.bat or the desktop shortcut.
echo =======================================================
pause
