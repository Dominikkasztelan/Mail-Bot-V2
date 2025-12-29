import time
import os
import re
import random  # <--- Potrzebne do losowania
from playwright.sync_api import Locator
from google import genai
from PIL import Image

# --- KONFIGURACJA API ---
# Pamiętaj, że w wersji PRO ten klucz powinien być w src/config.py i .env!
API_KEY = "AIzaSyDLUNwkH2aZgMzecoek9JO2fMiQlWtG0ws"


class CaptchaSolver:
    def __init__(self, page):
        self.page = page

        # Konfiguracja klienta Gemini
        # (Tutaj wersja uproszczona, w pełnym projekcie bierzemy z configu)
        if "TWOJ_KLUCZ" in API_KEY:
            print("⚠️ OSTRZEŻENIE: Nie podano klucza API Gemini!")
            self.client = None
        else:
            try:
                self.client = genai.Client(api_key=API_KEY)
            except Exception as e:
                print(f"⚠️ Błąd inicjalizacji klienta Gemini: {e}")
                self.client = None

    def get_captcha_instruction(self, frame_element: Locator):
        """Pobiera tekst instrukcji z Captchy."""
        try:
            instruction_locator = frame_element.locator(".rc-imageselect-desc-wrapper strong").first
            if instruction_locator.is_visible():
                text = instruction_locator.inner_text().strip()
                print(f"👀 Instrukcja z Captchy: SZUKAMY -> {text}")
                return text

            text = frame_element.locator(".rc-imageselect-instructions").first.inner_text()
            return text
        except Exception:
            # Fallback jeśli nie uda się odczytać
            return "objects"

    def _human_click(self, tile_locator: Locator):
        """
        Klika w losowy punkt wewnątrz elementu, zamiast w środek.
        Symuluje niedokładność człowieka.
        """
        # Pobieramy wymiary elementu
        box = tile_locator.bounding_box()
        if not box:
            tile_locator.click()  # Fallback
            return

        width = box['width']
        height = box['height']

        # Definiujemy margines (żeby nie klikać po krawędziach, bo to ryzykowne)
        margin = min(width, height) * 0.2  # 20% marginesu

        # Losujemy punkt wewnątrz bezpiecznej strefy
        random_x = random.uniform(margin, width - margin)
        random_y = random.uniform(margin, height - margin)

        # Wykonujemy kliknięcie z przesunięciem (offsetem)
        tile_locator.click(position={"x": random_x, "y": random_y})

    def solve_loop(self, captcha_frame: Locator):
        frame_element = captcha_frame.content_frame
        tiles = frame_element.locator(".rc-imageselect-tile")
        verify_btn = frame_element.locator("#recaptcha-verify-button")

        target_name = self.get_captcha_instruction(frame_element)

        attempt = 0
        max_attempts = 15

        while attempt < max_attempts:
            attempt += 1
            print(f"\n🧩 Captcha Loop: Iteracja {attempt} | Cel: {target_name}")

            # Pauza na "analizę wzrokową"
            time.sleep(random.uniform(1.5, 3.0))

            filename = "current_captcha.png"
            try:
                # Robimy screen samej tabelki (lub całej ramki jeśli tabelki nie ma)
                target_table = frame_element.locator("table.rc-imageselect-table").first
                if target_table.is_visible():
                    target_table.screenshot(path=filename)
                else:
                    captcha_frame.screenshot(path=filename)
            except Exception as e:
                print(f"⚠️ Błąd screenshotu: {e}")
                break

            targets = self._ask_gemini(filename, target_name)

            if targets:
                # Mieszamy kolejność klikania (człowiek nie zawsze klika 1, 2, 3 po kolei)
                random.shuffle(targets)

                for i, target_index in enumerate(targets):
                    if target_index >= tiles.count():
                        continue

                    print(f"   👉 Klikam kafelek nr {target_index + 1}")
                    try:
                        tile = tiles.nth(target_index)

                        # --- UŻYCIE HUMAN CLICK ---
                        self._human_click(tile)

                        # Losowa pauza między kliknięciami (bardzo ważne!)
                        time.sleep(random.uniform(0.3, 0.9))

                    except Exception as e:
                        print(f"Kliknięcie nieudane: {e}")

                # Czekamy aż animacje znikną (jeśli są nowe obrazki)
                time.sleep(random.uniform(2.0, 3.5))
                continue

            else:
                print("   ✅ Klikam 'Zweryfikuj'.")
                # Klikamy w przycisk też "po ludzku"
                self._human_click(verify_btn)

                time.sleep(3)

                if not captcha_frame.is_visible():
                    print("🎉 SUKCES! Captcha zniknęła.")
                    return True

                error_msg = frame_element.locator(".rc-imageselect-error-select-more").first
                if error_msg.is_visible():
                    print("   🔄 'Wybierz więcej'. Wracam do pętli.")
                    continue

                print("   🔄 Captcha przeładowała się (nowe zadanie?).")
                target_name = self.get_captcha_instruction(frame_element)
                time.sleep(1)

        print("❌ Przekroczono limit prób.")
        return False

    def _ask_gemini(self, image_path, target_name):
        if not self.client:
            return []

        try:
            img = Image.open(image_path)
            # Prompt bez zmian
            prompt = f"""
            Look at this CAPTCHA grid. Find all tiles containing: "{target_name}".
            Assume a standard numbered grid (1-9 for 3x3, 1-16 for 4x4).
            Return ONLY a Python list of numbers, e.g., [1, 5, 9].
            If none, return [].
            """

            # Pamiętaj o ustawieniu modelu, który działa u Ciebie (np. gemini-2.0-flash)
            response = self.client.models.generate_content(
                model='gemini-2.0-flash',
                contents=[prompt, img]
            )

            numbers = re.findall(r'\d+', response.text)
            indices = [int(n) - 1 for n in numbers]
            return indices

        except Exception as e:
            print(f"   ⚠️ Błąd API: {e}")
            return []