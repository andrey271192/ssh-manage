@echo off
echo === PCA SSH v2.0 — Install and Run ===

where python >nul 2>&1
if errorlevel 1 (
    echo Python not found!
    echo Download: https://python.org/downloads/
    echo Check "Add Python to PATH" during install!
    pause
    exit /b 1
)

echo Installing dependencies...
pip install paramiko

echo Starting PCA SSH...
python ssh_manager.py
