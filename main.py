import asyncio
import logging
import re
from contextlib import asynccontextmanager
from pathlib import Path

import ctranslate2
import sentencepiece as spm
import uvicorn
from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel

from config import MODEL_DIR, MODEL_NAME, DEVICE, PORT, API_KEY, BEAM_SIZE, MAX_INPUT_LENGTH

MAX_TEXT_LENGTH = 10000
MAX_BATCH_SIZE = 64
LANG_CODE_PATTERN = re.compile(r"^[a-z]{3}_[A-Z][a-z]{3}$")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
log = logging.getLogger("translator")

translator = None
sp_model = None
actual_device = None


def load_models():
    model_path = Path(MODEL_DIR) / MODEL_NAME
    sp_path = model_path / "sentencepiece.model"

    if not model_path.exists():
        raise RuntimeError(f"Model not found at {model_path}. Run run.sh or download manually.")
    if not sp_path.exists():
        raise RuntimeError(f"SentencePiece model not found at {sp_path}.")

    log.info("Loading CTranslate2 model '%s' on %s...", MODEL_NAME, DEVICE)
    trans = ctranslate2.Translator(str(model_path), device=DEVICE, compute_type="auto")
    log.info("CTranslate2 model loaded on %s.", trans.device)

    log.info("Loading SentencePiece tokenizer...")
    sp = spm.SentencePieceProcessor()
    sp.Load(str(sp_path))
    log.info("SentencePiece tokenizer loaded (%d tokens).", sp.GetPieceSize())

    return trans, sp, trans.device


@asynccontextmanager
async def lifespan(app: FastAPI):
    global translator, sp_model, actual_device
    translator, sp_model, actual_device = load_models()
    yield
    log.info("Shutting down.")


app = FastAPI(lifespan=lifespan)


def verify_auth(authorization: str | None):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")
    token = authorization.removeprefix("Bearer ")
    if token != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")


def tokenize(text: str, lang_code: str) -> list[str]:
    """NLLB tokenization: [src_lang] + spm_tokens + [</s>]"""
    pieces = sp_model.Encode(text, out_type=str)
    return [lang_code] + pieces + ["</s>"]


def detokenize(tokens: list[str], target_lang: str) -> str:
    """Strip target language prefix token, then decode."""
    if tokens and tokens[0] == target_lang:
        tokens = tokens[1:]
    return sp_model.Decode(tokens)


def translate_batch(texts: list[str], source_lang: str, target_lang: str) -> list[str]:
    source_tokens = [tokenize(text, source_lang) for text in texts]
    target_prefix = [[target_lang]] * len(texts)

    results = translator.translate_batch(
        source_tokens,
        target_prefix=target_prefix,
        beam_size=BEAM_SIZE,
        max_input_length=MAX_INPUT_LENGTH,
        max_decoding_length=MAX_INPUT_LENGTH * 2,
    )

    return [detokenize(result.hypotheses[0], target_lang) for result in results]


class TranslateRequest(BaseModel):
    text: str | list[str]
    source_lang: str = "eng_Latn"
    target_lang: str


@app.get("/health")
async def health():
    return {"status": "ok", "model": MODEL_NAME, "device": str(actual_device)}


@app.post("/translate")
async def translate(body: TranslateRequest, authorization: str | None = Header(None)):
    verify_auth(authorization)

    if not LANG_CODE_PATTERN.match(body.source_lang):
        raise HTTPException(status_code=400, detail=f"Invalid source_lang format: {body.source_lang}")
    if not LANG_CODE_PATTERN.match(body.target_lang):
        raise HTTPException(status_code=400, detail=f"Invalid target_lang format: {body.target_lang}")

    texts = [body.text] if isinstance(body.text, str) else body.text
    if not texts:
        raise HTTPException(status_code=400, detail="Empty text")
    if len(texts) > MAX_BATCH_SIZE:
        raise HTTPException(status_code=400, detail=f"Batch size exceeds maximum of {MAX_BATCH_SIZE}")
    for t in texts:
        if len(t) > MAX_TEXT_LENGTH:
            raise HTTPException(status_code=400, detail=f"Text exceeds maximum length of {MAX_TEXT_LENGTH} characters")

    log.info("Translating %d text(s): %s -> %s", len(texts), body.source_lang, body.target_lang)

    try:
        translated = await asyncio.to_thread(translate_batch, texts, body.source_lang, body.target_lang)
    except Exception as e:
        log.error("Translation failed: %s", e)
        raise HTTPException(status_code=500, detail="Translation failed")

    return {
        "translations": [
            {"text": t, "source_lang": body.source_lang, "target_lang": body.target_lang}
            for t in translated
        ]
    }


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=PORT)
