#!/usr/bin/env bash
# Delete the "darts" conda environment.
#
# Usage:
#   ./delete_env.sh      # prompt before removing
#   ./delete_env.sh -y   # remove without prompting
set -euo pipefail

ENV_NAME="darts"
ASSUME_YES=0
if [ "${1:-}" = "-y" ] || [ "${1:-}" = "--yes" ]; then
    ASSUME_YES=1
fi

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
    echo "Error: conda not found." >&2
    exit 1
fi

CONDA_BASE="$("$CONDA_EXE_PATH" info --base)"
ENV_PREFIX="$CONDA_BASE/envs/$ENV_NAME"

if [ ! -d "$ENV_PREFIX" ]; then
    echo "Environment '$ENV_NAME' does not exist. Nothing to do."
    exit 0
fi

if [ "$ASSUME_YES" -ne 1 ]; then
    read -r -p "Delete conda environment '$ENV_NAME' at $ENV_PREFIX? [y/N] " reply || reply=""
    case "$reply" in
        [yY]|[yY][eE][sS]) ;;
        *) echo "Aborted."; exit 0 ;;
    esac
fi

echo "Removing conda environment '$ENV_NAME'..."
"$CONDA_EXE_PATH" env remove -y -n "$ENV_NAME"
echo "Done."
