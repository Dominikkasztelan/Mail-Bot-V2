# src/check_models.py
import os
import sys
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from google import genai

# Setup path to allow running as script
# This allows 'python src/check_models.py' to work by adding project root to path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.append(str(BASE_DIR))

try:
    from src.logger_config import get_logger
except ImportError:
    # Fallback if logger config is broken or missing deps
    import logging
    logging.basicConfig(level=logging.INFO)
    def get_logger(name): return logging.getLogger(name)

logger = get_logger("CheckModels")

def list_gemini_models() -> None:
    """
    Connects to Google GenAI and lists available models.
    """
    load_dotenv()
    api_key: str | None = os.getenv("GEMINI_API_KEY")

    if not api_key:
        logger.critical("❌ CRITICAL: 'GEMINI_API_KEY' not found in .env!")
        sys.exit(1)

    # Mask key for logging
    masked_key = f"{api_key[:5]}...*****"
    logger.info(f"🔑 Using API Key: {masked_key}")

    models: Any = None

    try:
        client = genai.Client(api_key=api_key)
        logger.info("🔍 Connecting to Google API...")

        models = client.models.list()
        logger.info("✅ AVAILABLE MODELS:")

        count = 0
        for m in models:
            # Safer attribute access
            model_name = getattr(m, 'name', 'Unknown Name')
            logger.info(f"👉 {model_name}")
            count += 1

        if count == 0:
            logger.warning("⚠️ Model list is empty. Check API key permissions.")

    except Exception as e:
        logger.error(f"❌ API CRITICAL ERROR: {e}")

        # Debugging info
        if models:
            try:
                logger.info(f"🔍 Models object dir: {dir(models)}")
            except Exception:
                pass
        else:
            logger.warning("⚠️ 'models' variable is empty (failed before fetching).")

if __name__ == "__main__":
    list_gemini_models()
