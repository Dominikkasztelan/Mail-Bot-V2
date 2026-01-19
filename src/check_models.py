import os
import sys
from pathlib import Path
from typing import Optional, Any

# --- HARDENING: Obsługa uruchamiania bezpośredniego ---
# Pozwala uruchomić plik jako 'python src/check_models.py' bez błędów importu
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.append(str(BASE_DIR))

from google import genai
from dotenv import load_dotenv
from src.logger_config import get_logger

# Inicjalizacja loggera
logger = get_logger("CheckModels")

# 1. Ładujemy klucz z pliku .env
load_dotenv()
api_key: Optional[str] = os.getenv("GEMINI_API_KEY")

if not api_key:
    logger.critical("❌ BŁĄD: Nie znaleziono klucza 'GEMINI_API_KEY' w pliku .env!")
    sys.exit(1)

logger.info(f"🔑 Używam klucza: {api_key[:5]}...*****")

# Inicjalizacja zmiennej przed blokiem try
models: Any = None

try:
    client = genai.Client(api_key=api_key)
    logger.info("🔍 Łączę się z Google API...")

    # 2. Pobieramy listę modeli
    models = client.models.list()

    logger.info("✅ POBRANO LISTĘ MODELI:")

    count = 0
    # Iteracja po modelach
    for m in models:
        # Bezpieczne pobieranie nazwy
        model_name = getattr(m, 'name', 'Nieznana nazwa')
        logger.info(f"👉 {model_name}")
        count += 1

    if count == 0:
        logger.warning("⚠️ Lista modeli jest pusta. Sprawdź czy Twój klucz API ma uprawnienia.")

except Exception as e:
    logger.error(f"❌ BŁĄD KRYTYCZNY API: {e}")

    # 3. Bezpieczna diagnostyka w bloku except
    if models:
        try:
            # Używamy debug/info do zrzutu struktury obiektu
            logger.info(f"🔍 Szczegóły obiektu 'models' (dir): {dir(models)}")
        except Exception as debug_err:
            logger.error(f"⚠️ Nie udało się wylistować szczegółów obiektu: {debug_err}")
    else:
        logger.warning("⚠️ Zmienna 'models' jest pusta (błąd wystąpił przed lub w trakcie pobierania listy).")