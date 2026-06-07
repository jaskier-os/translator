import os
import logging

from dotenv import load_dotenv

load_dotenv()

log = logging.getLogger(__name__)

MODEL_DIR = os.environ.get("MODEL_DIR", "./models")
MODEL_NAME = os.environ.get("MODEL_NAME", "nllb-200-distilled-600M")
DEVICE = os.environ.get("DEVICE", "cpu")
PORT = int(os.environ.get("PORT", "10015"))
BEAM_SIZE = int(os.environ.get("BEAM_SIZE", "4"))
MAX_INPUT_LENGTH = int(os.environ.get("MAX_INPUT_LENGTH", "512"))

API_KEY = os.environ.get("API_KEY")
if not API_KEY:
    raise RuntimeError("API_KEY environment variable is required")
