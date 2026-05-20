#!/bin/bash
echo "=== PCA SSH v2.0 — Build for macOS ==="

# Check Python
if ! command -v python3 &>/dev/null; then
    echo "Python3 not found!"
    echo "Install: brew install python3"
    echo "Or: https://python.org/downloads/"
    exit 1
fi

echo "Installing dependencies..."
pip3 install paramiko pillow pyinstaller

echo "Generating icon..."
python3 gen_icon.py

echo "Building PCA_SSH.app..."
if [ -f pca_ssh.icns ]; then
    python3 -m PyInstaller --onefile --windowed --name "PCA_SSH" --icon=pca_ssh.icns ssh_manager.py
else
    python3 -m PyInstaller --onefile --windowed --name "PCA_SSH" ssh_manager.py
fi

if [ -f dist/PCA_SSH ]; then
    echo ""
    echo "DONE! App: dist/PCA_SSH"
    echo "Copy to /Applications or run directly"
    echo "sessions.json and pca_config.json save next to executable"
else
    echo "BUILD FAILED"
fi
