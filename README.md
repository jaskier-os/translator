# translator

## What it is

A translation HTTP service. It serves Meta's NLLB-200 (distilled-600M) through
CTranslate2 for fast CPU/GPU inference. FastAPI, port 10015. `POST /translate`
(bearer-token auth), `GET /health`. Runtime has no torch/transformers - the model
is pre-converted to CTranslate2 format.

## Build / run

Local:

```bash
cp .env.example .env   # set API_KEY at minimum
./run.sh               # venv + deps + fetch_models.sh (if needed) + start
```

`run.sh` creates the venv, installs requirements, runs `fetch_models.sh` when the
model folder is missing, then starts `main.py`. You can also fetch the model
manually:

```bash
bash fetch_models.sh   # downloads facebook/nllb-200-distilled-600M, converts to CTranslate2
```

That step installs `transformers` + `torch` temporarily for the one-time
conversion and writes to `./models/nllb-200-distilled-600M` (gitignored, not
committed).

Docker (multi-stage - the model is converted in the builder stage, so the final
image has no torch):

```bash
docker build -t translator .
docker run -p 10015:10015 --env-file .env translator
```

## Configuration

Config is env vars. `.env.example` is the source of truth - copy to `.env` and
edit. What matters:

- `API_KEY` - bearer token, required. Set it to something real.
- `MODEL_DIR`, `MODEL_NAME` - where the converted model lives (default
  `./models/nllb-200-distilled-600M`).
- `DEVICE` - `cpu`, `cuda`, or `auto`.
- `BEAM_SIZE`, `MAX_INPUT_LENGTH`, `PORT`.

## Dependencies

Python 3.12, FastAPI + uvicorn, `ctranslate2`, `sentencepiece`, `pydantic`. The
runtime does NOT need torch/transformers - those are only used by
`fetch_models.sh` (and the Docker builder stage) to convert the weights once. For
CUDA, `run.sh` auto-adds cublas/cudnn lib paths if present in the venv.
