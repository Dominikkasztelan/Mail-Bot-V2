# src/captcha_solver.py
import os
import time
import random
import json
from typing import List, Any, Optional

from playwright.sync_api import Frame, TimeoutError as PlaywrightTimeout

# --- FIX: OBSŁUGA NOWEJ I STAREJ BIBLIOTEKI GOOGLE ---
try:
    import google.genai as genai
except ImportError:
    import google.generativeai as genai

from src.config import API_KEYS
from src.logger_config import logger
from src.exceptions import CaptchaSolveError


class CaptchaSolver:
    """
    Solver wykorzystujący Google Gemini Vision do rozwiązywania Captcha.
    Wersja ULTIMATE: Fallback do 'body' i debugowanie HTML.
    """

    def __init__(self, page: Optional[Any] = None):
        self.page = page
        self.api_keys: List[str] = API_KEYS.get("GEMINI", [])

        if not self.api_keys:
            logger.critical("❌ Brak kluczy API Gemini w pliku .env! Solver nie zadziała.")
            raise ValueError("Brak kluczy GEMINI_API_KEY")

        logger.info(f"🔧 Załadowano {len(self.api_keys)} kluczy API Gemini.")

        self.models = [
            "gemini-1.5-flash",
            "gemini-1.5-pro",
            "gemini-pro-vision"
        ]

    def _get_random_key(self) -> str:
        return random.choice(self.api_keys)

    def solve_loop(self, frame: Frame) -> bool:
        """
        Główna pętla obsługująca proces rozwiązywania Captchy wewnątrz ramki.
        Zwraca True jeśli sukces, False jeśli porażka po X próbach.
        """
        logger.info("🤖 Startuję pętlę rozwiązywania Captchy...")

        max_total_attempts = 5

        # Lista selektorów. Dodano "body" jako ostateczny fallback.
        # Jeśli specyficzne kontenery nie zostaną znalezione, robimy zrzut całej ramki.
        target_selectors = ["#rc-imageselect-target", ".rc-imageselect-payload", "table", "body"]

        for i in range(max_total_attempts):
            # 1. Sprawdź czy captcha zniknęła (oznacza sukces weryfikacji)
            if not frame.is_visible():
                logger.info("✅ Ramka Captchy zniknęła - zakładam sukces.")
                return True

            try:
                target = None
                # 2. Iteracja po selektorach
                for selector in target_selectors:
                    loc = frame.locator(selector).first
                    try:
                        # Dla 'body' czekamy krócej, dla konkretnych dłużej (dajmy czas na render)
                        timeout = 2000 if selector == "body" else 4000
                        loc.wait_for(state="visible", timeout=timeout)

                        # Dodatkowe sprawdzenie dla body - czy nie jest puste (małą wysokość)
                        if selector == "body":
                            box = loc.bounding_box()
                            if box and box['height'] < 50:
                                continue  # To puste body, szukamy dalej lub czekamy

                        target = loc
                        # logger.debug(f"🔍 Znaleziono element captchy: {selector}")
                        break
                    except PlaywrightTimeout:
                        continue

                # 3. Jeśli NIE znaleziono celu
                if not target:
                    # A) Checkbox "Nie jestem robotem"
                    checkbox = frame.locator(".recaptcha-checkbox-border, #recaptcha-anchor")
                    if checkbox.is_visible():
                        logger.info("👉 Widzę checkbox, klikam...")
                        checkbox.click()
                        time.sleep(2)
                        continue

                    # B) Przycisk odświeżania
                    reload_btn = frame.locator("#recaptcha-reload-button, .rc-button-reload").first
                    if reload_btn.is_visible():
                        logger.warning("⚠️ Widzę przycisk odświeżania, klikam.")
                        reload_btn.click()
                        time.sleep(2)
                        continue

                    # C) Debugging - co widzi bot?
                    logger.warning(f"⚠️ Nie znaleziono obrazka (próba {i + 1}). Analiza HTML...")
                    try:
                        html_dump = frame.content()
                        # Logujemy tylko fragment, żeby nie zapchać konsoli
                        logger.info(f"📄 HTML Dump: {html_dump[:300]} ...")
                    except Exception:
                        pass

                    time.sleep(2)
                    continue

                # 4. Wykonanie zrzutu ekranu
                timestamp = int(time.time())
                screenshot_path = f"logs/captcha_{timestamp}_{i}.png"
                target.screenshot(path=screenshot_path)

                # 5. Pobranie instrukcji
                instruction_el = frame.locator(
                    "strong, .rc-imageselect-desc-no-canonical, #rc-imageselect-instructions").first
                instruction = instruction_el.inner_text() if instruction_el.is_visible() else "Select all matching images"
                logger.info(f"🧩 Wyzwanie: '{instruction}'")

                # 6. Zapytanie do Gemini
                tiles_to_click = self._solve_grid(screenshot_path, instruction)

                if not tiles_to_click:
                    logger.warning("⚠️ Gemini zwróciło pustą listę. Klikam 'Pomiń/Odśwież'.")
                    self._click_reload_or_skip(frame)
                    continue

                # 7. Klikanie w kafelki
                logger.info(f"👉 Klikam kafelki: {tiles_to_click}")
                # Szukamy kafelków wewnątrz targetu (jeśli target to body, szukamy w body)
                tiles = target.locator("td, .rc-imageselect-tile")

                # Fallback: jeśli nie znaleziono standardowych kafelków, a target to body
                if tiles.count() == 0:
                    tiles = frame.locator("td, .rc-imageselect-tile")

                count = tiles.count()

                for index in tiles_to_click:
                    idx_zero_based = index - 1
                    if idx_zero_based < count:
                        tile = tiles.nth(idx_zero_based)
                        tile.click(position={"x": random.randint(10, 50), "y": random.randint(10, 50)})
                        time.sleep(random.uniform(0.15, 0.4))

                time.sleep(1)

                # 8. Zatwierdzenie
                verify_btn = frame.locator("#recaptcha-verify-button, .rc-button-default").first
                if verify_btn.is_visible():
                    verify_btn.click()
                    time.sleep(3)

            except Exception as e:
                logger.error(f"❌ Błąd w pętli solve_loop: {e}")
                time.sleep(2)

        return False

    def _click_reload_or_skip(self, frame: Frame):
        try:
            reload_btn = frame.locator("#recaptcha-reload-button, .rc-button-reload").first
            if reload_btn.is_visible():
                reload_btn.click()
                return

            skip_btn = frame.get_by_role("button", name="Pomiń")
            if skip_btn.is_visible():
                skip_btn.click()
        except Exception:
            pass

    def _solve_grid(self, image_path: str, instruction: str) -> List[int]:
        """Wysyła obrazek do Gemini i zwraca listę indeksów do kliknięcia."""
        try:
            with open(image_path, "rb") as f:
                image_data = f.read()
        except Exception as e:
            logger.error(f"Nie można odczytać pliku screenshotu: {e}")
            return []

        prompt = f"""
        Task: Solve this CAPTCHA puzzle.
        Instruction: "{instruction}".
        The image is a grid (3x3 or 4x4).
        Return a JSON list of integers for tiles that MATCH the instruction.
        Index starts at 1 (top-left is 1, top-right is 3 or 4).
        Example output: [1, 5, 9]
        Do not explain. Return ONLY the JSON list.
        """

        for attempt in range(3):
            key = self._get_random_key()
            try:
                # Obsługa API Gemini (stara/nowa lib) - uniwersalne podejście
                genai.configure(api_key=key)
                model = genai.GenerativeModel(self.models[0])

                response = model.generate_content([
                    prompt,
                    {"mime_type": "image/png", "data": image_data}
                ])

                text = response.text.strip().replace("```json", "").replace("```", "").strip()
                result = json.loads(text)

                if isinstance(result, list):
                    return result

            except Exception as e:
                logger.warning(f"⚠️ Gemini API Error ({attempt + 1}/3): {e}")
                time.sleep(1)
                continue

        return []

    def solve(self, image_path: str) -> str:
        return "NOT_IMPLEMENTED"