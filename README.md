# Translator

A small HTTP translation microservice. It serves Meta's NLLB-200
(`nllb-200-distilled-600M`) via [CTranslate2](https://github.com/OpenNMT/CTranslate2)
behind a [FastAPI](https://fastapi.tiangolo.com/) API, supporting 200+ languages
with single and batch translation. Requests are authenticated with a bearer token.

## Endpoints

- `GET /health` - liveness check, reports model name and active device.
- `POST /translate` - translate text. Body:
  ```json
  {
    "text": "Hello, how are you?",
    "source_lang": "eng_Latn",
    "target_lang": "zho_Hans"
  }
  ```
  `text` may also be a list of strings (batch, up to 64). Language codes use the
  NLLB `xxx_Yyyy` format (e.g. `eng_Latn`, `rus_Cyrl`, `jpn_Jpan`). Requires header
  `Authorization: Bearer <API_KEY>`.

## Prerequisites

- Python 3.12
- Internet access for the one-time model download/conversion (pulls
  `transformers` + `torch` temporarily; the runtime itself does not need them).
- Optional: an NVIDIA GPU with CUDA libraries if you set `DEVICE=cuda`.
- Optional: Docker, to build/run the containerized version instead.

## Setup

1. Copy the example environment file and edit the values:
   ```bash
   cp .env.example .env
   ```
   Variables:

   | Variable           | Default                  | Description                                                        |
   | ------------------ | ------------------------ | ------------------------------------------------------------------ |
   | `MODEL_DIR`        | `./models`               | Directory containing model subfolders.                             |
   | `MODEL_NAME`       | `nllb-200-distilled-600M`| Model subfolder name inside `MODEL_DIR`.                            |
   | `DEVICE`           | `cpu`                    | CTranslate2 device: `cpu`, `cuda`, or `auto`.                      |
   | `PORT`             | `10015`                  | TCP port the service listens on.                                   |
   | `BEAM_SIZE`        | `4`                      | Decoding beam size (1 = greedy/fastest, higher = better/slower).  |
   | `MAX_INPUT_LENGTH` | `512`                    | Maximum input token length per request.                           |
   | `API_KEY`          | (required)               | Bearer token clients must present. Set a strong random value.     |

2. Fetch and convert the model weights (see "Model weights" below):
   ```bash
   bash fetch_models.sh
   ```

## Build / run

The simplest path uses the bundled script, which creates a virtualenv, installs
pinned dependencies, fetches the model if missing, and starts the server:

```bash
bash run.sh
```

Or run the steps manually:

```bash
python3 -m venv venv
venv/bin/pip install -r requirements.txt
bash fetch_models.sh          # one-time model download + conversion
venv/bin/python main.py
```

The service then listens on `http://0.0.0.0:$PORT`.

### Docker

The Docker image converts the model at build time, so the resulting container is
fully self-contained:

```bash
docker build -t translator .
docker run --rm -p 10015:10015 -e API_KEY=your-secret translator
```

## Test

Install the dev dependencies and run the smoke tests against a running instance:

```bash
venv/bin/pip install -r requirements-dev.txt
API_KEY=your-secret venv/bin/python test_e2e.py          # basic health + translate
API_KEY=your-secret venv/bin/python test_20_languages.py # 20-language sweep
```

`test_e2e.py` and `test_20_languages.py` read `TRANSLATOR_URL` (default
`http://localhost:10015`) and `API_KEY` from the environment.

## Model weights

This service uses the **standard pretrained** NLLB-200 model
`facebook/nllb-200-distilled-600M` from Hugging Face. The weights are NOT
committed to this repository. `fetch_models.sh` downloads the model and converts
it into the CTranslate2 format under `$MODEL_DIR/$MODEL_NAME`
(`model.bin`, `sentencepiece.model`, `tokenizer.json`, ...). The Docker build
performs the same conversion automatically. Set `QUANTIZATION` (default
`float16`) to control the converted precision.

## Networking / TLS

This service speaks plain HTTP and has no VPN or certificate dependencies. Run it
behind a reverse proxy (nginx, Caddy, Traefik) if you need TLS termination or to
expose it publicly. Authentication is via the `API_KEY` bearer token only.
