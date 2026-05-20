@echo off
echo === PCA SSH v2.0 — Build for Windows ===

where python >nul 2>&1
if errorlevel 1 (
    echo Python not found! Install from https://python.org/downloads/
    echo Check "Add Python to PATH" during install!
    pause
    exit /b 1
)

echo Installing dependencies...
pip install paramiko pillow pyinstaller

echo Generating icon...
python gen_icon.py

echo Building PCA_SSH.exe...
if exist pca_ssh.ico (
    pyinstaller --onefile --noconsole --name "PCA_SSH" --icon=pca_ssh.ico ssh_manager.py
) else (
    pyinstaller --onefile --noconsole --name "PCA_SSH" ssh_manager.py
)

echo.
if exist dist\PCA_SSH.exe (
    echo DONE! EXE: dist\PCA_SSH.exe
    echo Copy it anywhere — sessions.json and pca_config.json save next to .exe
) else (
    echo BUILD FAILED
)
pause
