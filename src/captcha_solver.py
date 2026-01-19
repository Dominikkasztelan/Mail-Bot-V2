# src/captcha_solver.py
import os
import time
import random
import json
import re
from typing import List, Any, Optional

from playwright.sync_api import Frame, Locator, TimeoutError as PlaywrightTimeout, Error as PlaywrightError

# --- FIX: JEDNOLITA NOWA BIBLIOTEKA (v1.0+) ---
# Kompatybilność z src/check_models.py
from google import genai
from google.genai import types


from src.config import API_KEYS, RETRY_LIMITS
from src.logger_config import get_logger
from src.exceptions import CaptchaSolveError

logger = get_logger(__name__)


class CaptchaSolver:
    """
    Solver wykorzystujący Google Gemini Vision (API v1.0+) do rozwiązywania Captcha.
    Wersja PRODUCTION-READY:
    - Unified Imports (google-genai)
    - Robust JSON Parsing (JSON Mode)
    - Safe Clicking (Bounding Box Check)
    - Key Rotation
    """

    def __init__(self, page: Optional[Any] = None):
        self.page = page
        self.api_keys: List[str] = API_KEYS.get("GEMINI", [])

        if not self.api_keys:
            logger.critical("❌ Brak kluczy API Gemini w pliku .env! Solver nie zadziała.")
            raise ValueError("CRITICAL: Brak kluczy GEMINI_API_KEY")

        logger.info(f"🔧 Załadowano {len(self.api_keys)} kluczy API Gemini.")

        # Model zoptymalizowany pod kątem wizji i szybkości
        self.model_name = "gemini-1.5-flash"

    def _get_client(self) -> genai.Client:
        """Tworzy klienta z losowym kluczem (rotacja dla każdego zapytania)."""
        return genai.Client(api_key=random.choice(self.api_keys))

    def solve_loop(self, frame: Frame) -> bool:
        """
        Główna pętla obsługująca proces rozwiązywania Captchy wewnątrz ramki.
        Zwraca True jeśli sukces, False jeśli porażka po X próbach.
        """
        logger.info("🤖 Startuję pętlę rozwiązywania Captchy...")
        max_total_attempts = RETRY_LIMITS["CAPTCHA_ATTEMPTS"]

        for i in range(max_total_attempts):
            if self._is_solved_or_detached(frame):
                 return True

            target = self._find_captcha_target(frame)
            
            if not target:
                if self._handle_fallback_actions(frame, i):
                    continue
                time.sleep(2)
                continue

            # Próba rozwiązania jednej rundy
            if self._attempt_solve_round(frame, target, i):
                # Po udanej rundzie, sprawdzamy czy to koniec w kolejnej iteracji pętli
                pass
            else:
                # Błąd w rundzie (np. API failure, brak płytek to click)
                self._click_reload_or_skip(frame)
                
        return False

    def _is_solved_or_detached(self, frame: Frame) -> bool:
        try:
            if frame.is_detached() or not frame.locator("body").is_visible():
                logger.info("✅ Ramka Captchy zniknęła/detached - zakładam sukces.")
                return True
        except (PlaywrightTimeout, PlaywrightError):
            return True
        return False

    def _find_captcha_target(self, frame: Frame) -> Optional[Locator]:
        target_selectors = ["#rc-imageselect-target", ".rc-imageselect-payload", "table", "body"]
        for selector in target_selectors:
            loc = frame.locator(selector).first
            try:
                # Krótszy timeout dla body, dłuższy dla konkretnych elementów
                timeout = 2000 if selector == "body" else 4000
                loc.wait_for(state="visible", timeout=timeout)
                
                # Check dla pustego body (żeby nie robić screena białego tła)
                if selector == "body":
                    box = loc.bounding_box()
                    if box and box['height'] < 50:
                        continue

                return loc
            except PlaywrightTimeout:
                continue
        return None

    def _attempt_solve_round(self, frame: Frame, target: Locator, attempt_idx: int) -> bool:
        try:
            screenshot_path = self._take_screenshot(target, attempt_idx)
            instruction = self._get_instruction(frame)
            
            tiles_to_click = self._solve_grid(screenshot_path, instruction)
            if not tiles_to_click:
                logger.warning("⚠️ Gemini zwróciło pustą listę.")
                return False

            self._click_tiles(frame, target, tiles_to_click)
            self._confirm_solution(frame)
            return True

        except PlaywrightError as e:
            logger.error(f"❌ Błąd w rundzie rozwiązywania: {e}")
            return False

    def _take_screenshot(self, target: Locator, attempt_idx: int) -> str:
        timestamp = int(time.time())
        screenshot_path = f"logs/captcha_{timestamp}_{attempt_idx}.png"
        
        # Upewniamy się, że katalog istnieje
        os.makedirs("logs", exist_ok=True)
        target.screenshot(path=screenshot_path)
        return screenshot_path

    def _get_instruction(self, frame: Frame) -> str:
        instruction_el = frame.locator(
            "strong, .rc-imageselect-desc-no-canonical, #rc-imageselect-instructions").first
        if instruction_el.is_visible():
            instruction = instruction_el.inner_text()
            logger.info(f"🧩 Wyzwanie: '{instruction}'")
            return instruction
        return "Select all matching images"

    def _click_tiles(self, frame: Frame, target: Locator, tiles_idx: List[int]) -> None:
        logger.info(f"👉 Klikam kafelki: {tiles_idx}")

        # Próba znalezienia kafelków wewnątrz celu lub w całej ramce
        tiles = target.locator("td, .rc-imageselect-tile")
        if tiles.count() == 0:
            tiles = frame.locator("td, .rc-imageselect-tile")

        count = tiles.count()
        for index in tiles_idx:
            idx_zero_based = index - 1
            if idx_zero_based < count:
                tile = tiles.nth(idx_zero_based)
                self._safe_click_tile(tile)
                # Losowe opóźnienie między kliknięciami
                time.sleep(random.uniform(0.15, 0.4))

        time.sleep(1)

    def _confirm_solution(self, frame: Frame) -> None:
        # 8. Zatwierdzenie
        verify_btn = frame.locator("#recaptcha-verify-button, .rc-button-default").first
        if verify_btn.is_visible():
            verify_btn.click()
            time.sleep(3)

    def _handle_fallback_actions(self, frame: Frame, attempt_idx: int) -> bool:
        """Obsługa checkboxów, przycisków odświeżania i logowania błędów."""
        # A) Checkbox "Nie jestem robotem"
        checkbox = frame.locator(".recaptcha-checkbox-border, #recaptcha-anchor")
        if checkbox.is_visible():
            logger.info("👉 Widzę checkbox, klikam...")
            checkbox.click()
            time.sleep(2)
            return True

        # B) Przycisk Odświeżania (np. błąd sieci)
        reload_btn = frame.locator("#recaptcha-reload-button, .rc-button-reload").first
        if reload_btn.is_visible():
            logger.warning("⚠️ Widzę przycisk odświeżania, klikam.")
            reload_btn.click()
            time.sleep(2)
            return True

        # C) Tylko logowanie
        logger.warning(f"⚠️ Nie znaleziono obrazka ani kontrolek (próba {attempt_idx + 1}).")
        return False

    def _click_reload_or_skip(self, frame: Frame):
        """Pomocnicza funkcja do klikania Pomiń lub Odśwież w przypadku braku pewności."""
        try:
            reload_btn = frame.locator("#recaptcha-reload-button, .rc-button-reload").first
            if reload_btn.is_visible():
                reload_btn.click()
                return

            skip_btn = frame.get_by_role("button", name="Pomiń")
            if skip_btn.is_visible():
                skip_btn.click()
        except PlaywrightError:
            pass

    def _safe_click_tile(self, tile_locator: Locator) -> None:
        """
        Bezpieczne klikanie w kafelek z losowym offsetem wewnątrz bounding boxa.
        Chroni przed klikaniem w punkty (0,0) lub poza elementem (np. gdy grid jest dynamiczny).
        """
        try:
            box = tile_locator.bounding_box()
            if box:
                # Margines bezpieczeństwa 5px z każdej strony
                width = box['width']
                height = box['height']

                # Upewniamy się, że element nie jest za mały na marginesy
                if width > 10 and height > 10:
                    safe_x = random.uniform(5, width - 5)
                    safe_y = random.uniform(5, height - 5)
                    tile_locator.click(position={"x": safe_x, "y": safe_y})
                else:
                    # Element bardzo mały, klikamy w środek
                    tile_locator.click(force=True)
            else:
                # Fallback jeśli nie można pobrać boxa (np. element partially hidden)
                tile_locator.click(force=True)
        except PlaywrightError as e:
            logger.warning(f"⚠️ Błąd kliknięcia w kafelek: {e}")

    def _solve_grid(self, image_path: str, instruction: str) -> List[int]:
        """
        Wysyła obrazek do Gemini (Nowe API) i zwraca listę indeksów do kliknięcia.
        Wymusza format JSON response_mime_type.
        """
        try:
            with open(image_path, "rb") as f:
                image_bytes = f.read()
        except OSError as e:
            logger.error(f"❌ Nie można odczytać pliku screenshotu: {e}")
            return []

        prompt = f"""
        Task: Identify tiles containing: "{instruction}".
        Format: Return ONLY a raw JSON list of integers (1-based index).
        Grid: Assume standard 3x3 or 4x4.
        Example: [1, 5, 9]
        NO MARKDOWN, NO EXPLANATIONS.
        """

        for attempt in range(RETRY_LIMITS["GEMINI_API_RETRIES"]):
            try:
                client = self._get_client()

                # Nowe API call (google-genai)
                response = client.models.generate_content(
                    model=self.model_name,
                    contents=[
                        types.Content(
                            parts=[
                                types.Part.from_text(text=prompt),
                                types.Part.from_bytes(data=image_bytes, mime_type="image/png")
                            ]
                        )
                    ],
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",  # JSON MODE - kluczowe dla stabilności
                        temperature=0.1
                    )
                )

                text_resp = response.text
                if not text_resp:
                    continue

                # Cleaning na wypadek gdyby model dodał ```json ... ``` mimo JSON mode
                clean_json = text_resp.strip()
                if "```" in clean_json:
                    # Wyciągnij treść między klamrami []
                    match = re.search(r'\[.*\]', clean_json, re.DOTALL)
                    if match:
                        clean_json = match.group(0)
                    else:
                        clean_json = clean_json.replace("```json", "").replace("```", "")

                result = json.loads(clean_json)

                if isinstance(result, list):
                    # Filtrujemy tylko inty, żeby zabezpieczyć bota przed błędami typu
                    return [x for x in result if isinstance(x, int)]

            except (json.JSONDecodeError, KeyError, AttributeError) as e:
                max_retries = RETRY_LIMITS["GEMINI_API_RETRIES"]
                logger.warning(f"⚠️ Gemini API Error ({attempt + 1}/{max_retries}): {e}")
                time.sleep(1)
                continue

        return []

    def solve(self, image_path: str) -> str:
        """Placeholder dla legacy calls lub innych typów captchy."""
        return "NOT_IMPLEMENTED"