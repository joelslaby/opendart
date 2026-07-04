#!/bin/bash
# Double-click to launch OpenDart. Runs through Terminal so it inherits
# Terminal's existing Full Disk Access — a standalone .app bundle hits
# macOS's per-app TCC sandboxing and gets denied reading this folder.
cd "$(dirname "${BASH_SOURCE[0]}")" || exit 1
/Users/jhiesener/miniconda3/envs/darts/bin/python darts.py
