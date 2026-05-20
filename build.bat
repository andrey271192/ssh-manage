@echo off
echo === KU SSH Manager — Build ===

where python >nul 2>&1
if errorlevel 1 (
    echo Python not found! Install from https://python.org/downloads/
    pause
    exit /b 1
)

echo Installing dependencies...
pip install paramiko pyinstaller

echo Building .exe...
pyinstaller --onefile --noconsole --name "KU SSH Manager" ^
    --add-data "sessions.json;." ^
    --icon NONE ^
    ssh_manager.py

echo.
echo Done! EXE: dist\KU SSH Manager.exe
echo Copy it anywhere — sessions.json saves next to .exe
pause
