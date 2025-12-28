import time
import re
from typing import List, Optional
from playwright.sync_api import Locator, Page
from google import genai
from PIL import Image

from src.config import API_KEYS
from src.logger_config import logger  # <--- IMPORT LOGGERA


class CaptchaSolver:
    def __init__(self, page: Page) -> None:
        self.page: Page = page
        self.api_key: Optional[str] = API_KEYS.get("GEMINI")
        self.client: Optional[genai.Client] = None

        if not self.api_key or "AIzaSy" not in self.api_key:
            logger.warning("⚠️ OSTRZEŻENIE: Brak poprawnego klucza API Gemini w src/config.py!")
        else:
            try:
                self.client = genai.Client(api_key=self.api_key)
                logger.debug("Klient Gemini zainicjalizowany pomyślnie.")
            except Exception as e:
                logger.error(f"⚠️ Błąd inicjalizacji klienta Gemini: {e}")

    def get_captcha_instruction(self, frame_element: Locator) -> str:
        try:
            instruction_locator = frame_element.locator(".rc-imageselect-desc-wrapper strong").first
            if instruction_locator.is_visible():
                text = instruction_locator.inner_text().strip()
                logger.info(f"👀 Instrukcja z Captchy: SZUKAMY -> {text}")
                return text

            text = frame_element.locator(".rc-imageselect-instructions").first.inner_text()
            return text
        except Exception:
            logger.warning("⚠️ Nie udało się odczytać instrukcji. Zgaduję domyślną.")
            return "objects"

    def solve_loop(self, captcha_frame: Locator) -> bool:
        frame_element = captcha_frame.content_frame
        tiles = frame_element.locator(".rc-imageselect-tile")
        verify_btn = frame_element.locator("#recaptcha-verify-button")

        target_name = self.get_captcha_instruction(frame_element)

        attempt = 0
        max_attempts = 15

        while attempt < max_attempts:
            attempt += 1
            logger.info(f"🧩 Captcha Loop: Iteracja {attempt} | Cel: {target_name}")

            filename = "logs/current_captcha.png"  # Zapisujemy w folderze logs
            try:
                target_table = frame_element.locator("table.rc-imageselect-table").first
                if target_table.is_visible():
                    target_table.screenshot(path=filename)
                else:
                    captcha_frame.screenshot(path=filename)
            except Exception as e:
                logger.error(f"⚠️ Błąd screenshotu: {e}")
                break

            targets = self._ask_gemini(filename, target_name)

            if targets:
                target_index = targets[0]
                if target_index >= tiles.count():
                    continue

                logger.info(f"   👉 Gemini: {targets}. Klikam kafelek nr {target_index}")
                try:
                    tiles.nth(target_index).click()
                except Exception as e:
                    logger.debug(f"Kliknięcie nieudane: {e}")

                time.sleep(2.5)
                continue

            else:
                logger.info("   ✅ Klikam 'Zweryfikuj'.")
                verify_btn.click()
                time.sleep(3)

                if not captcha_frame.is_visible():
                    logger.info("🎉 SUKCES! Captcha zniknęła.")
                    return True

                error_msg = frame_element.locator(".rc-imageselect-error-select-more").first
                if error_msg.is_visible():
                    logger.info("   🔄 'Wybierz więcej'. Wracam do pętli.")
                    continue

                logger.info("   🔄 Captcha przeładowała się.")
                target_name = self.get_captcha_instruction(frame_element)
                time.sleep(1)

        logger.error("❌ Przekroczono limit prób rozwiązania Captchy.")
        return False

    def _ask_gemini(self, image_path: str, target_name: str) -> List[int]:
        if not self.client:
            return []

        try:
            img = Image.open(image_path)
            prompt = f"""
            Find all tiles containing: "{target_name}".
            Assume standard grid 3x3 (1-9) or 4x4 (1-16).
            Return ONLY a Python list of numbers, e.g., [1, 5, 9].
            """

            response = self.client.models.generate_content(
                model='gemini-1.5-flash',
                contents=[prompt, img]
            )

            text_response = response.text if response.text else ""
            numbers = re.findall(r'\d+', text_response)
            indices = [int(n) - 1 for n in numbers]
            return indices

        except Exception as e:
            logger.error(f"   ⚠️ Błąd API Gemini: {e}")
            return []