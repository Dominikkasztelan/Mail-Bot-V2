import re
import time
import random
import os
from itertools import cycle
from google import genai
from PIL import Image
from dotenv import load_dotenv

load_dotenv()

# --- KONFIGURACJA KLUCZY ---
keys_env = os.getenv("GEMINI_KEYS", "")
GEMINI_KEY_POOL = [k.strip() for k in keys_env.split(",") if k.strip()]

if not GEMINI_KEY_POOL:
    single = os.getenv("GEMINI_API_KEY")
    if single:
        GEMINI_KEY_POOL = [single]

# --- MODELE ---
AVAILABLE_MODELS = [
    "gemini-2.5-flash",
    "gemini-2.5-pro",
    "gemini-flash-latest",
    "gemini-2.0-flash-lite-preview-02-05",
]

print(f"🔧 Załadowano {len(GEMINI_KEY_POOL)} kluczy. Modele: {AVAILABLE_MODELS}")


class CaptchaSolver:
    def __init__(self, page):
        self.page = page
        self.client = None

        if not GEMINI_KEY_POOL:
            print("❌ KRYTYCZNY BŁĄD: Brak kluczy w .env!")
            self.keys_iterator = None
        else:
            self.keys_iterator = cycle(GEMINI_KEY_POOL)
            self._rotate_key()

    def _rotate_key(self):
        if not self.keys_iterator:
            return
        next_key = next(self.keys_iterator)
        masked = f"...{next_key[-6:]}"
        print(f"🔄 ROTACJA KLUCZA -> Nowy: {masked}")
        try:
            self.client = genai.Client(api_key=next_key)
        except Exception as e:
            print(f"⚠️ Błąd inicjalizacji klucza: {e}")

    def get_captcha_instruction(self, frame):
        try:
            elm = frame.locator(".rc-imageselect-desc-wrapper strong").first
            if elm.is_visible():
                txt = elm.inner_text().strip()
                print(f"👀 Cel: {txt}")
                return txt
            return frame.locator(".rc-imageselect-instructions").first.inner_text()
        except:
            return "objects"

    def _human_click(self, locator):
        try:
            box = locator.bounding_box()
            if box:
                m = min(box['width'], box['height']) * 0.2
                x = random.uniform(m, box['width'] - m)
                y = random.uniform(m, box['height'] - m)
                locator.click(position={"x": x, "y": y})
            else:
                locator.click()
        except:
            pass

    def solve_loop(self, captcha_frame):
        frame = captcha_frame.content_frame
        tiles = frame.locator(".rc-imageselect-tile")
        verify_btn = frame.locator("#recaptcha-verify-button")

        target = self.get_captcha_instruction(frame)
        previous_indices = []

        for i in range(1, 20):
            print(f"\n🧩 Próba {i} | Cel: {target}")
            time.sleep(random.uniform(2.5, 4.0))

            try:
                path = "logs/captcha_current.png"
                if not os.path.exists("logs"):
                    os.makedirs("logs")

                try:
                    tbl = frame.locator("table.rc-imageselect-table").first
                    if tbl.is_visible():
                        tbl.screenshot(path=path)
                    else:
                        captcha_frame.screenshot(path=path)
                except:
                    print("⚠️ Błąd zrzutu ekranu.")
                    break

                # --- STRZAŁ DO GEMINI ---
                indices = self._ask_gemini_smart(path, target)
                indices = list(set(indices))

                if len(indices) >= 9:
                    print(f"⚠️ ALARM: Gemini chce kliknąć {len(indices)} kafelków. Reset.")
                    self._human_click(verify_btn)
                    time.sleep(4)
                    target = self.get_captcha_instruction(frame)
                    continue

                if indices and (sorted(indices) == sorted(previous_indices)):
                    print(f"⚠️ ZACIĘCIE! Te same numery. Klikam WERYFIKUJ.")
                    self._human_click(verify_btn)
                    previous_indices = []
                    time.sleep(4)
                    target = self.get_captcha_instruction(frame)
                    continue

                previous_indices = indices

                if indices:
                    random.shuffle(indices)
                    print(f"   🤖 Gemini wskazał: {indices}")

                    for idx in indices:
                        if idx < tiles.count():
                            self._human_click(tiles.nth(idx))
                            time.sleep(random.uniform(0.5, 1.0))

                    print("   🕵️ Analiza po kliknięciu...")
                    time.sleep(2.5)

                    selected_tiles = frame.locator(".rc-imageselect-tileselected").count()

                    if selected_tiles > 0:
                        print(f"   🛑 Wykryto {selected_tiles} zaznaczonych. STATYCZNA -> WERYFIKUJ.")
                        self._human_click(verify_btn)
                    else:
                        print("   🌊 Kafelki zniknęły. DYNAMICZNA -> Czekam...")
                        if i >= 8:
                            print("   😤 Za długo. Ryzykuję WERYFIKACJĘ.")
                            self._human_click(verify_btn)
                        else:
                            continue

                else:
                    print("   ✅ Brak celów (wg Gemini) -> Klikam 'Zweryfikuj'.")
                    self._human_click(verify_btn)

                time.sleep(5)
                if not captcha_frame.is_visible():
                    print("🎉 SUKCES! Captcha zniknęła.")
                    return True

                if frame.locator(".rc-imageselect-error-select-more").is_visible():
                    print("   🔄 'Wybierz więcej'...")
                    continue

                target = self.get_captcha_instruction(frame)

            except Exception as e:
                print(f"❌ Błąd w pętli: {e}")
                break

        return False

    def _ask_gemini_smart(self, path, target):
        """
        Wysyła zapytanie do API.
        POPRAWKA: Usunięto 'enable_http2', które powodowało błąd walidacji.
        Zostawiono wydłużony timeout.
        """
        img = Image.open(path)
        prompt = f"""
        Analyze CAPTCHA. Target: '{target}'.
        1. If Dynamic (grid), ignore white/loading tiles.
        2. If Static (single image), ignore checked tiles.
        3. Be conservative. Return list of numbers (1-indexed).
        """

        # --- KONFIGURACJA ---
        # Zostawiamy tylko timeout, bo 'enable_http2' nie jest wspierane w tym configu
        http_conf = {
            'timeout': 60.0,
        }

        for _ in range(2):
            if not self.client:
                self._rotate_key()

            for model_name in AVAILABLE_MODELS:
                try:
                    response = self.client.models.generate_content(
                        model=model_name,
                        contents=[prompt, img],
                        # Przekazujemy tylko dozwolone parametry
                        config={'http_options': http_conf}
                    )
                    nums = re.findall(r'\d+', response.text)
                    return [int(n) - 1 for n in nums]

                except Exception as e:
                    msg = str(e)
                    print(f"   ⚠️ Błąd modelu {model_name}: {msg[:100]}...")
                    continue

            print("⚡ Żaden model nie odpowiedział. Rotacja klucza...")
            self._rotate_key()

        return []