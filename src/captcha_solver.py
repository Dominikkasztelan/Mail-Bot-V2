# src/captcha_solver.py
import os
import time
import random
import json
import re
from typing import List, Any, Optional

from playwright.sync_api import Frame, Locator, TimeoutError as PlaywrightTimeout

# --- FIX: JEDNOLITA NOWA BIBLIOTEKA (v1.0+) ---
# Kompatybilność z src/check_models.py
from google import genai
from google.genai import types

from src.config import API_KEYS
from src.logger_config import logger
from src.exceptions import CaptchaSolveError


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

        max_total_attempts = 5
        # Lista selektorów, gdzie szukamy obrazka (włącznie z fallbackiem do body)
        target_selectors = ["#rc-imageselect-target", ".rc-imageselect-payload", "table", "body"]

        for i in range(max_total_attempts):
            # 1. Sprawdź czy captcha zniknęła (oznacza sukces weryfikacji)
            try:
                if frame.is_detached() or not frame.is_visible():
                    logger.info("✅ Ramka Captchy zniknęła/detached - zakładam sukces.")
                    return True
            except Exception:
                # Jeśli frame jest martwy, to prawdopodobnie sukces (przeładowanie strony)
                return True

            try:
                target = None
                # 2. Iteracja po selektorach
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

                        target = loc
                        break
                    except PlaywrightTimeout:
                        continue

                # 3. Jeśli NIE znaleziono celu (Szukamy elementów sterujących lub błędu)
                if not target:
                    if self._handle_fallback_actions(frame, i):
                        continue
                    # Jeśli nie udało się nic zrobić -> czekamy chwilę i próbujemy od nowa
                    time.sleep(2)
                    continue

                # 4. Wykonanie zrzutu ekranu
                timestamp = int(time.time())
                screenshot_path = f"logs/captcha_{timestamp}_{i}.png"

                # Upewniamy się, że katalog istnieje
                os.makedirs("logs", exist_ok=True)
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

                # 7. Klikanie w kafelki (Nowa logika Safe Click)
                logger.info(f"👉 Klikam kafelki: {tiles_to_click}")

                # Próba znalezienia kafelków wewnątrz celu lub w całej ramce
                tiles = target.locator("td, .rc-imageselect-tile")
                if tiles.count() == 0:
                    tiles = frame.locator("td, .rc-imageselect-tile")

                count = tiles.count()
                for index in tiles_to_click:
                    idx_zero_based = index - 1
                    if idx_zero_based < count:
                        tile = tiles.nth(idx_zero_based)
                        self._safe_click_tile(tile)
                        # Losowe opóźnienie między kliknięciami
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
        except Exception:
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
        except Exception as e:
            logger.warning(f"⚠️ Błąd kliknięcia w kafelek: {e}")

    def _solve_grid(self, image_path: str, instruction: str) -> List[int]:
        """
        Wysyła obrazek do Gemini (Nowe API) i zwraca listę indeksów do kliknięcia.
        Wymusza format JSON response_mime_type.
        """
        try:
            with open(image_path, "rb") as f:
                image_bytes = f.read()
        except Exception as e:
            logger.error(f"❌ Nie można odczytać pliku screenshotu: {e}")
            return []

        prompt = f"""
        Task: Identify tiles containing: "{instruction}".
        Format: Return ONLY a raw JSON list of integers (1-based index).
        Grid: Assume standard 3x3 or 4x4.
        Example: [1, 5, 9]
        NO MARKDOWN, NO EXPLANATIONS.
        """

        for attempt in range(3):
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

            except Exception as e:
                logger.warning(f"⚠️ Gemini API Error ({attempt + 1}/3): {e}")
                time.sleep(1)
                continue

        return []

    def solve(self, image_path: str) -> str:
        """Placeholder dla legacy calls lub innych typów captchy."""
        return "NOT_IMPLEMENTED"