# src/captcha_solver.py
import os
import time
import random
import google.generativeai as genai
from typing import List, Any, Optional

from src.config import API_KEYS
from src.logger_config import logger
from src.exceptions import CaptchaSolveError


class CaptchaSolver:
    """
    Solver wykorzystujący Google Gemini Vision do rozwiązywania Captcha.
    Obsługuje rotację kluczy API (Load Balancing).
    """

    # FIX: Dodano parametr 'page=None', aby RegistrationPage nie wyrzucał błędu TypeError
    def __init__(self, page: Optional[Any] = None):
        self.page = page  # Zachowujemy referencję (dla kompatybilności), choć API jej nie wymaga
        self.api_keys: List[str] = API_KEYS.get("GEMINI", [])

        if not self.api_keys:
            logger.critical("❌ Brak kluczy API Gemini w pliku .env! Solver nie zadziała.")
            raise ValueError("Brak kluczy GEMINI_API_KEY")

        logger.info(f"🔧 Załadowano {len(self.api_keys)} kluczy API Gemini.")

        # Modele w kolejności od najszybszego/najtańszego
        self.models = [
            "gemini-2.0-flash-lite-preview-02-05",  # Super szybki
            "gemini-flash-latest",  # Standardowy szybki
            "gemini-1.5-flash",  # Stabilny
            "gemini-pro-vision"  # Fallback
        ]

    def _get_random_key(self) -> str:
        """Zwraca losowy klucz z puli."""
        return random.choice(self.api_keys)

    def solve(self, image_path: str) -> str:
        """
        Główna metoda rozwiązująca.
        """
        if not os.path.exists(image_path):
            logger.error(f"❌ Nie znaleziono pliku Captcha: {image_path}")
            raise CaptchaSolveError("File not found")

        # 1. Ładowanie obrazu
        try:
            with open(image_path, "rb") as img_file:
                image_data = img_file.read()
        except Exception as e:
            logger.error(f"❌ Błąd odczytu pliku: {e}")
            raise CaptchaSolveError(f"Read error: {e}")

        # 2. Próba rozwiązania (Retry Logic)
        max_retries = 3
        for attempt in range(max_retries):
            current_key = self._get_random_key()

            # Konfiguracja klucza DLA TEGO KONKRETNEGO ZAPYTANIA
            genai.configure(api_key=current_key)

            # Wybór modelu
            model_name = self.models[0]
            model = genai.GenerativeModel(model_name)

            prompt = "Rewrite the text from this image exactly as it appears. Return ONLY the text, no spaces, no explanations."

            try:
                # logger.debug(f"🧩 Próba {attempt+1}/{max_retries} na modelu {model_name}...")

                response = model.generate_content([
                    prompt,
                    {"mime_type": "image/png", "data": image_data}
                ])

                if response.text:
                    captcha_text = response.text.strip().replace(" ", "").upper()
                    logger.info(f"✅ Captcha rozwiązana: {captcha_text}")
                    return captcha_text
                else:
                    logger.warning(f"⚠️ Pusta odpowiedź od Gemini (Próba {attempt + 1}).")

            except Exception as e:
                logger.warning(f"⚠️ Błąd API Gemini: {e}. Przełączam klucz...")
                time.sleep(1)  # Krótka pauza przed retry

        logger.error("❌ Wszystkie próby rozwiązania Captchy nieudane.")
        raise CaptchaSolveError("Gemini failed 3 times")