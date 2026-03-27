@echo off
setlocal EnableExtensions

set "REPO_DIR=%~dp0"
set "VENV_DIR=%REPO_DIR%venv"

if not exist "%VENV_DIR%\Scripts\python.exe" (
    echo [ERROR] Virtual environment not found. Run setup.bat first.
    pause
    exit /b 1
)

call "%VENV_DIR%\Scripts\activate.bat"
python "%REPO_DIR%app.py" %*
