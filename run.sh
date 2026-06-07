#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"

# Load .env if present so PORT/MODEL_DIR/MODEL_NAME are available to this script.
if [ -f .env ]; then
  set -a
  # shellcheck disable=SC1091
  . ./.env
  set +a
fi

PORT="${PORT:-10015}"
MODEL_DIR="${MODEL_DIR:-./models}"
MODEL_NAME="${MODEL_NAME:-nllb-200-distilled-600M}"
export MODEL_DIR MODEL_NAME
MODEL_PATH="$MODEL_DIR/$MODEL_NAME"

# Free the port if a previous instance is still bound.
fuser -k "${PORT}/tcp" 2>/dev/null || true

if [ ! -d "venv" ]; then
  echo "[translator] Creating venv..."
  python3 -m venv venv
fi

echo "[translator] Installing dependencies..."
venv/bin/python -m pip install -q -r requirements.txt

# Fetch + convert the model if it is not present yet.
if [ ! -d "$MODEL_PATH" ]; then
  echo "[translator] Model not found at $MODEL_PATH. Running fetch_models.sh..."
  bash fetch_models.sh
fi

# Set up CUDA library paths if available (only relevant when DEVICE=cuda).
NVIDIA_LIBS="$(dirname "$(find venv -name 'libcublas.so*' -print -quit 2>/dev/null)" 2>/dev/null)"
CUDNN_LIBS="$(dirname "$(find venv -name 'libcudnn.so*' -print -quit 2>/dev/null)" 2>/dev/null)"
if [ -n "$NVIDIA_LIBS" ] || [ -n "$CUDNN_LIBS" ]; then
  export LD_LIBRARY_PATH="${NVIDIA_LIBS}:${CUDNN_LIBS}:${LD_LIBRARY_PATH}"
fi

echo "[translator] Starting on port ${PORT}..."
exec venv/bin/python main.py
