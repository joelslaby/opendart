#!/usr/bin/env bash
# Create (if needed) the "darts" conda environment and launch OpenDart in it.
#
# Usage:
#   ./run.sh              # launch the launcher menu (darts.py)
#   ./run.sh 501.py       # launch a specific entrypoint
#   FORCE_DEPS=1 ./run.sh # re-install requirements even if already satisfied
set -euo pipefail

ENV_NAME="darts"
PY_VERSION="3.12"
SCRIPT="${1:-darts.py}"

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"

# --- locate conda -----------------------------------------------------------
if command -v conda >/dev/null 2>&1; then
    CONDA_EXE_PATH="$(command -v conda)"
else
    for candidate in \
        "$HOME/miniconda3/bin/conda" \
        "$HOME/anaconda3/bin/conda" \
        "$HOME/miniforge3/bin/conda" \
        "/opt/miniconda3/bin/conda" \
        "/opt/homebrew/Caskroom/miniconda/base/bin/conda"; do
        if [ -x "$candidate" ]; then
            CONDA_EXE_PATH="$candidate"
            break
        fi
    done
fi

if [ -z "${CONDA_EXE_PATH:-}" ]; then
    echo "Error: conda not found. Install Miniconda from https://docs.conda.io/en/latest/miniconda.html" >&2
    exit 1
fi

CONDA_BASE="$("$CONDA_EXE_PATH" info --base)"
ENV_PREFIX="$CONDA_BASE/envs/$ENV_NAME"

# --- create env if missing --------------------------------------------------
if [ ! -x "$ENV_PREFIX/bin/python" ]; then
    echo "Creating conda environment '$ENV_NAME' (python $PY_VERSION)..."
    "$CONDA_EXE_PATH" create -y -n "$ENV_NAME" "python=$PY_VERSION" tk
else
    echo "Using existing conda environment '$ENV_NAME'."
fi

PYTHON="$ENV_PREFIX/bin/python"

# --- install requirements ---------------------------------------------------
# Skip the pip round-trip when every requirement already imports cleanly.
if [ "${FORCE_DEPS:-0}" = "1" ] || ! "$PYTHON" -c "import tkinter, PIL, matplotlib, pandas" 2>/dev/null; then
    echo "Installing requirements..."
    "$PYTHON" -m pip install --upgrade pip
    "$PYTHON" -m pip install -r requirements.txt
fi

"$PYTHON" -c "import tkinter" 2>/dev/null || {
    echo "Error: tkinter is missing from the '$ENV_NAME' environment." >&2
    echo "Fix with: $CONDA_EXE_PATH install -n $ENV_NAME tk" >&2
    exit 1
}

# --- run --------------------------------------------------------------------
echo "Launching $SCRIPT..."
exec "$PYTHON" "$SCRIPT" "${@:2}"
