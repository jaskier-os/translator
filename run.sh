#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"

# Kill any existing process on our port
fuser -k 10015/tcp 2>/dev/null || true

MODEL_DIR="models"
MODEL_NAME="nllb-200-distilled-600M"
MODEL_PATH="$MODEL_DIR/$MODEL_NAME"

if [ ! -d "venv" ]; then
  echo "[translator] Creating venv..."
  python3 -m venv venv
fi

echo "[translator] Installing dependencies..."
venv/bin/python -m pip install -q -r requirements.txt

# Convert model from HuggingFace if not present
if [ ! -d "$MODEL_PATH" ]; then
  echo "[translator] Converting NLLB-200 model (requires transformers + torch)..."
  venv/bin/python -m pip install -q transformers torch
  venv/bin/ct2-transformers-converter \
    --model "facebook/$MODEL_NAME" \
    --output_dir "$MODEL_PATH" \
    --quantization float16 \
    --copy_files sentencepiece.bpe.model tokenizer.json
  mv "$MODEL_PATH/sentencepiece.bpe.model" "$MODEL_PATH/sentencepiece.model"
  echo "[translator] Model conversion complete."
fi

# Set up CUDA library paths if available
NVIDIA_LIBS="$(dirname "$(find venv -name 'libcublas.so*' -print -quit 2>/dev/null)" 2>/dev/null)"
CUDNN_LIBS="$(dirname "$(find venv -name 'libcudnn.so*' -print -quit 2>/dev/null)" 2>/dev/null)"
if [ -n "$NVIDIA_LIBS" ] || [ -n "$CUDNN_LIBS" ]; then
  export LD_LIBRARY_PATH="${NVIDIA_LIBS}:${CUDNN_LIBS}:${LD_LIBRARY_PATH}"
fi

echo "[translator] Starting..."
exec venv/bin/python main.py
