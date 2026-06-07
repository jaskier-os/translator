#!/usr/bin/env bash
# Download and convert the NLLB-200 model into CTranslate2 format.
#
# This fetches the standard pretrained model from Hugging Face
# (facebook/nllb-200-distilled-600M) and converts it with the
# CTranslate2 transformers converter. The resulting model is written to
# $MODEL_DIR/$MODEL_NAME and is NOT committed to the repository.
#
# Requirements: python3, pip, internet access. transformers + torch are
# installed temporarily for the one-time conversion.
set -e
cd "$(dirname "$0")"

MODEL_DIR="${MODEL_DIR:-./models}"
MODEL_NAME="${MODEL_NAME:-nllb-200-distilled-600M}"
QUANTIZATION="${QUANTIZATION:-float16}"
MODEL_PATH="$MODEL_DIR/$MODEL_NAME"

if [ -d "$MODEL_PATH" ]; then
  echo "[fetch_models] Model already present at $MODEL_PATH. Nothing to do."
  exit 0
fi

PY="${PYTHON:-python3}"
if [ -x "venv/bin/python" ]; then
  PY="venv/bin/python"
fi

echo "[fetch_models] Installing conversion dependencies (transformers, torch)..."
"$PY" -m pip install -q transformers torch

echo "[fetch_models] Converting facebook/$MODEL_NAME -> $MODEL_PATH ($QUANTIZATION)..."
"$PY" -m ctranslate2.converters.transformers \
  --model "facebook/$MODEL_NAME" \
  --output_dir "$MODEL_PATH" \
  --quantization "$QUANTIZATION" \
  --copy_files sentencepiece.bpe.model tokenizer.json

mv "$MODEL_PATH/sentencepiece.bpe.model" "$MODEL_PATH/sentencepiece.model"
echo "[fetch_models] Model conversion complete: $MODEL_PATH"
