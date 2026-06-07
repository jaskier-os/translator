# Stage 1: Convert model (has torch+transformers)
FROM python:3.12-slim AS builder
WORKDIR /build
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt transformers torch
RUN ct2-transformers-converter \
      --model facebook/nllb-200-distilled-600M \
      --output_dir models/nllb-200-distilled-600M \
      --quantization float16 \
      --copy_files sentencepiece.bpe.model tokenizer.json && \
    mv models/nllb-200-distilled-600M/sentencepiece.bpe.model models/nllb-200-distilled-600M/sentencepiece.model

# Stage 2: Runtime (NO torch/transformers)
FROM python:3.12-slim
RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY --from=builder /build/models/ models/
COPY . .
EXPOSE 10015
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
  CMD curl -f http://localhost:10015/health || exit 1
CMD ["python3", "-u", "main.py"]
