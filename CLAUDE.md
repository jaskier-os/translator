# CLAUDE.md -- Translator Service

This file provides guidance to Claude Code when working in this repository.

IMPORTANT: NEVER USE EMOJIS ANYWHERE IN LOGGING, CODE OR OTHER TEXT.

IMPORTANT: Treat this codebase as work in progress. Never do backwards-compatibility or legacy support unless explicitly asked. Remove code that becomes redundant.

## What this service is

A machine-translation microservice providing multilingual support for the AI orchestration
system. It serves Meta's NLLB-200 (`nllb-200-distilled-600M` by default) via CTranslate2
behind a FastAPI HTTP API.

This service listens on **port 10015**.

For the whole-system architecture and the full port table, see the orchestrator repo
(`jaskier-os/orchestrator`) CLAUDE.md / docs -- do not duplicate that map here.

## Tech stack

- Python 3 + FastAPI
- CTranslate2 (CPU or CUDA via `DEVICE`)
- NLLB-200 model

## Model fetch

The model is NOT committed. `fetch_models.sh` downloads it into `MODEL_DIR/MODEL_NAME`. The
Docker build fetches the model at build time so the image ships with it. `run.sh` loads
`.env`, defaults the model path, and frees the port before starting.

```bash
bash fetch_models.sh   # download model into ./models/<MODEL_NAME>
bash run.sh            # venv + requirements + main.py
```

Copy `.env.example` to `.env`. Key knobs: `MODEL_DIR`, `MODEL_NAME`, `DEVICE`, `PORT`,
`BEAM_SIZE`, `MAX_INPUT_LENGTH`, `API_KEY` (required).

## Layout

- `main.py` -- FastAPI app; model load on lifespan startup
- `config.py` -- env-driven configuration
- `test_e2e.py`, `test_20_languages.py` -- tests

## API

- `GET /health` -- no auth
- `POST /translate` -- requires `Authorization: Bearer <API_KEY>`

## Deploy

Server-side service: it auto-deploys on git push to `main`. CI (`.gitlab-ci.yml`) builds the
Dockerfile with `docker buildx --push` to the local registry, then bumps the image tag in
the `infrastructure/deploy` repo, which Flux reconciles onto the cluster.

- NEVER restart the running service yourself -- if a restart is needed, tell the user.
- NEVER build/push Docker images by hand; commit + push and let CI handle it.
- NEVER modify Kubernetes env/secrets/deployments directly; changes go through the deploy
  manifests repo so Flux reconciles them.
