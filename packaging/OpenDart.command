#!/bin/bash
# Double-click to launch OpenDart. Runs through Terminal so it inherits
# Terminal's existing Full Disk Access — a standalone .app bundle hits
# macOS's per-app TCC sandboxing and gets denied reading this folder.
cd "$(dirname "${BASH_SOURCE[0]}")/.." || exit 1

if [ -x "$HOME/miniconda3/envs/darts/bin/python" ]; then
    PYTHON="$HOME/miniconda3/envs/darts/bin/python"
elif [ -x "/opt/miniconda3/envs/darts/bin/python" ]; then
    PYTHON="/opt/miniconda3/envs/darts/bin/python"
elif [ -x "venv/bin/python3" ]; then
    PYTHON="venv/bin/python3"
else
    PYTHON="$(command -v python3)"
fi

if [ -z "$PYTHON" ]; then
    echo "No python3 found. Install Python 3, then: pip3 install -r requirements.txt"
    read -n 1 -s -r -p "Press any key to close..."
    exit 1
fi

"$PYTHON" darts.py
