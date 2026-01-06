# src/registration_page.py
import re
import time
import random
import os
from typing import Callable, Any, Dict
from playwright.sync_api import Page, Locator, TimeoutError as PlaywrightTimeout

from src.captcha_solver import CaptchaSolver
from src.config import DELAYS
from src.models import UserIdentity
from src.logger_config import get_logger
# FIX: Dodano import CaptchaBlockadeError
from src.exceptions import ElementNotFoundError, RegistrationFailedError, CaptchaBlockadeError

logger = get_logger(__name__)


class RegistrationPage:
    """
    Page Object Model dla strony rejestracji.
    Wersja PRODUCTION:
    - Obsługa twardej blokady (CaptchaBlockadeError)
    - Nowoczesne metody pisania (press_sequentially)
    - Robust detection ramek
    """

    def __init__(self, page: Page) -> None:
        self.page: Page = page
        self.solver: CaptchaSolver = CaptchaSolver(page)

        # --- SELEKTORY FORMULARZA ---
        self.input_name: Locator = page.get_by_role("textbox", name="Imię")
        self.input_surname: Locator = page.get_by_role("textbox", name="Nazwisko")
        self.input_day: Locator = page.get_by_role("textbox", name="Dzień")
        self.label_month: Locator = page.locator(".account-input__label").filter(has_text="Miesiąc")
        self.input_year: Locator = page.get_by_role("textbox", name="Rok ur.")

        self.label_gender: Locator = page.get_by_text("Jak się do Ciebie zwracać?")
        self.gender_male: Locator = page.get_by_role("list").filter(has_text="Pan Pani").locator("span").first

        self.input_login: Locator = page.get_by_label("Nazwa konta", exact=False)
        self.input_password: Locator = page.get_by_role("textbox", name="Hasło", exact=True)
        self.input_password_repeat: Locator = page.get_by_role("textbox", name="Powtórz hasło")

        self.checkbox_accept_all: Locator = page.locator("div").filter(
            has_text=re.compile(r"^Akceptuję i zaznaczam wszystkie poniższe zgody$")).first
        self.btn_submit: Locator = page.get_by_role("button", name="Załóż darmowe konto")

        # --- SELEKTORY BLOKAD ---
        self.rodo_btn_primary: Locator = page.get_by_role("button", name="Przejdź do serwisu")
        self.rodo_btn_secondary: Locator = page.get_by_role("button", name="Zgoda")
        self.rodo_btn_accept_all: Locator = page.locator(".rodo-popup-agree")

        self.verify_text: Locator = page.locator("text=Zweryfikuj")
        self.verify_btn: Locator = page.get_by_role("button", name="Zweryfikuj")

    def _save_debug_screenshot(self, name: str) -> None:
        try:
            os.makedirs("logs", exist_ok=True)
            timestamp = time.strftime("%H%M%S")
            path = f"logs/debug_{timestamp}_{name}.png"
            self.page.screenshot(path=path)
            logger.info(f"📸 Zapisano screenshot: {path}")
        except Exception:
            pass

    def load(self) -> None:
        logger.info("🔄 Otwieram stronę rejestracji...")
        try:
            self.page.goto("https://konto-pocztowe.interia.pl/#/nowe-konto/darmowe", timeout=60000)
            self.page.wait_for_load_state("domcontentloaded")
            # Próba wstępnego czyszczenia
            try:
                self.ensure_path_clear()
            except CaptchaBlockadeError:
                logger.warning("⚠️ Strona załadowana z aktywną blokadą Captcha!")
        except Exception as e:
            logger.error(f"Critical: Nie udało się załadować strony. {e}")
            raise ElementNotFoundError(f"Page load failed: {e}")

    def human_delay(self) -> None:
        time.sleep(random.uniform(DELAYS.get("THINKING_MIN", 0.1), DELAYS.get("THINKING_MAX", 0.5)))

    def section_delay(self) -> None:
        time.sleep(random.uniform(DELAYS.get("SECTION_PAUSE_MIN", 0.5), DELAYS.get("SECTION_PAUSE_MAX", 1.5)))

    def human_type(self, locator: Locator, text: str, use_click: bool = True) -> None:
        if use_click:
            locator.scroll_into_view_if_needed()
            locator.click(timeout=5000)

        time.sleep(0.2)
        min_delay_ms = int(DELAYS.get("HUMAN_TYPE_MIN", 0.05) * 1000)
        max_delay_ms = int(DELAYS.get("HUMAN_TYPE_MAX", 0.15) * 1000)
        locator.press_sequentially(text, delay=random.randint(min_delay_ms, max_delay_ms))
        self.human_delay()

    def handle_captcha_if_present(self) -> bool:
        """
        Sprawdza obecność blokady. Zwraca True, jeśli rozwiązano.
        Rzuca CaptchaBlockadeError, jeśli blokada jest nie do przejścia.
        """
        has_blockade_ui = self.verify_text.is_visible() or self.verify_btn.is_visible()
        frames = [f for f in self.page.frames if "recaptcha" in f.url or "captcha" in f.url]

        if not (has_blockade_ui or frames):
            return False  # Droga wolna

        logger.info("⚠️ Wykryto potencjalną blokadę.")

        # Próba odsłonięcia ramki
        if has_blockade_ui:
            try:
                if self.verify_btn.is_visible():
                    self.verify_btn.click(force=True)
                else:
                    self.verify_text.click(force=True)
                time.sleep(2.5)
            except Exception:
                pass

        # Szukanie ramki (ULEPSZONE)
        target_frame = None
        for attempt in range(5):
            all_frames = self.page.frames
            target_frame = None

            for frame in all_frames:
                if frame.is_detached(): continue
                url = frame.url.lower()

                # A) Metoda URL (Stable)
                if ("recaptcha" in url) and ("bframe" in url or "payload" in url):
                    target_frame = frame
                    break

                # B) Metoda Selektora (Legacy)
                try:
                    if frame.locator("#rc-imageselect-target, table, .rc-imageselect-payload").first.is_visible(
                            timeout=100):
                        target_frame = frame
                        break
                except:
                    pass

            if target_frame:
                break

            # C) Checkbox fallback
            for frame in all_frames:
                if frame.is_detached(): continue
                cb = frame.locator("#recaptcha-anchor").first
                if cb.is_visible(timeout=100):
                    if "checked" not in cb.get_attribute("class", ""):
                        logger.info("👉 Klikam Checkbox...")
                        cb.click()
                        time.sleep(2.0)
                    break

            time.sleep(1.0)

        # Decyzja
        if target_frame:
            logger.warning(f"🚨 Przekazuję ramkę do Solvera...")
            if self.solver.solve_loop(target_frame):
                return True
            else:
                raise CaptchaBlockadeError("Solver nie rozwiązał Captchy mimo prób.")

        if has_blockade_ui:
            if self.verify_btn.is_visible() or self.verify_text.is_visible():
                self._save_debug_screenshot("blocked_dead_end")
                raise CaptchaBlockadeError("Blokada widoczna, ale brak ramki z obrazkami.")

        return False

    def ensure_path_clear(self) -> None:
        """Usuwa przeszkody. Rzuca błąd przy trwałej blokadzie."""
        # RODO
        for btn in [self.rodo_btn_primary, self.rodo_btn_secondary, self.rodo_btn_accept_all]:
            if btn.is_visible():
                try:
                    btn.click()
                    time.sleep(0.5)
                    break
                except:
                    pass

        # Captcha
        self.handle_captcha_if_present()

    def retry_action(self, action_name: str, action_callback: Callable[[], Any], retries: int = 3) -> None:
        """Ponawia akcję TYLKO jeśli droga jest czysta."""
        for i in range(retries):
            try:
                self.ensure_path_clear()
                action_callback()
                return
            except CaptchaBlockadeError:
                logger.critical(f"⛔ STOP: Blokada Captcha przy akcji '{action_name}'.")
                raise  # Przerywamy proces
            except Exception as e:
                logger.warning(f"⚠️ Retry {i + 1}/{retries} '{action_name}': {str(e)[:100]}")
                if "intercepts" in str(e):
                    self.page.keyboard.press("Escape")

                if i == retries - 1:
                    raise ElementNotFoundError(f"Failed: {action_name}") from e
                time.sleep(1.0)

    def fill_form(self, identity: Dict[str, Any]) -> None:
        logger.info(f"📝 Wypełnianie: {identity['first_name']} {identity['last_name']}")

        self.retry_action("Imię", lambda: self.human_type(self.input_name, identity['first_name']))
        self.page.keyboard.press("Tab")
        self.retry_action("Nazwisko",
                          lambda: self.human_type(self.input_surname, identity['last_name'], use_click=False))
        self.section_delay()

        self.retry_action("Dzień", lambda: self.human_type(self.input_day, identity['birth_day']))

        def sel_month():
            self.label_month.click()
            self.page.get_by_role("listitem").filter(has_text=identity['birth_month_name']).first.click()

        self.retry_action("Miesiąc", sel_month)
        self.retry_action("Rok", lambda: self.human_type(self.input_year, identity['birth_year']))
        self.section_delay()

        self.retry_action("Płeć", lambda: (self.label_gender.click(), self.gender_male.click()))
        self.section_delay()

        self._ensure_unique_login(identity)

        self.retry_action("Hasło", lambda: self.human_type(self.input_password, identity['password']))
        self.retry_action("Powtórz", lambda: self.human_type(self.input_password_repeat, identity['password']))

    def accept_terms(self) -> None:
        self.retry_action("Zgody", lambda: self.checkbox_accept_all.click())

    def submit(self) -> None:
        self.retry_action("Submit", lambda: self.btn_submit.click())

    def verify_success(self) -> bool:
        try:
            self.page.wait_for_url(lambda u: "nowe-konto" not in u, timeout=15000)
            return True
        except:
            return False

    def _ensure_unique_login(self, identity: Dict[str, Any]) -> None:
        self.input_login.wait_for(state="visible", timeout=10000)
        base = identity['login'].split('.')[0] + "." + identity['login'].split('.')[1]

        for _ in range(10):
            suffix = str(random.randint(100, 9999))
            login = f"{base}{suffix}"[:30]

            self.input_login.click()
            self.page.keyboard.press("Control+A")
            self.page.keyboard.press("Backspace")

            # FIX: Użycie nowoczesnej metody zamiast deprecated .type()
            self.input_login.press_sequentially(login, delay=50)

            self.page.keyboard.press("Tab")
            time.sleep(1.0)

            if not self.page.locator(".input-error-message").is_visible():
                identity['login'] = login
                logger.info(f"✅ Login OK: {login}")
                return
        raise RegistrationFailedError("Brak wolnego loginu.")