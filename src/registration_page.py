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
from src.exceptions import ElementNotFoundError, CaptchaSolveError, RegistrationFailedError

logger = get_logger(__name__)


class RegistrationPage:
    """
    Page Object Model dla strony rejestracji.
    Przywrócono wersję ROBUST (z obsługą retry, get_by_role i poprawnym URL).
    """

    def __init__(self, page: Page) -> None:
        self.page: Page = page
        self.solver: CaptchaSolver = CaptchaSolver(page)

        # --- SELEKTORY (Twoje oryginalne - najlepsze) ---
        self.input_name: Locator = page.get_by_role("textbox", name="Imię")
        self.input_surname: Locator = page.get_by_role("textbox", name="Nazwisko")
        self.input_day: Locator = page.get_by_role("textbox", name="Dzień")
        self.label_month: Locator = page.locator(".account-input__label").filter(has_text="Miesiąc")
        self.input_year: Locator = page.get_by_role("textbox", name="Rok ur.")

        self.label_gender: Locator = page.get_by_text("Jak się do Ciebie zwracać?")
        self.gender_male: Locator = page.get_by_role("list").filter(has_text="Pan Pani").locator("span").first

        # Selektor loginu oparty na etykiecie
        self.input_login: Locator = page.get_by_label("Nazwa konta", exact=False)

        self.input_password: Locator = page.get_by_role("textbox", name="Hasło", exact=True)
        self.input_password_repeat: Locator = page.get_by_role("textbox", name="Powtórz hasło")

        self.checkbox_accept_all: Locator = page.locator("div").filter(
            has_text=re.compile(r"^Akceptuję i zaznaczam wszystkie poniższe zgody$")).first
        self.btn_submit: Locator = page.get_by_role("button", name="Załóż darmowe konto")

        # --- PRZESZKADZAJKI (RODO) ---
        self.rodo_btn_primary: Locator = page.get_by_role("button", name="Przejdź do serwisu")
        self.rodo_btn_secondary: Locator = page.get_by_role("button", name="Zgoda")
        self.rodo_btn_accept_all: Locator = page.locator(".rodo-popup-agree")

        self.captcha_frame_locator: Locator = page.locator("iframe[src*='captcha'], iframe[src*='recaptcha']")
        self.verify_text: Locator = page.locator("text=Zweryfikuj")
        self.verify_btn: Locator = page.get_by_role("button", name="Zweryfikuj")

        self.error_msg: Locator = page.locator(".form-error")
        self.login_error_locator: Locator = page.locator(".input-error-message, .form-error").filter(
            has_text=re.compile(r"zajęty|istnieje|niedozwolone", re.IGNORECASE))

    def _save_debug_screenshot(self, name: str) -> None:
        try:
            if not os.path.exists("logs"):
                os.makedirs("logs")
            timestamp = time.strftime("%H%M%S")
            path = f"logs/debug_{timestamp}_{name}.png"
            self.page.screenshot(path=path)
            logger.info(f"📸 Zapisano screenshot błędu: {path}")
        except Exception as e:
            logger.error(f"Nie udało się zapisać screena: {e}")

    def load(self) -> None:
        # PRZYWRÓCONO: Poprawny URL do nowej wersji formularza
        logger.info("🔄 Otwieram stronę rejestracji (Nowy Layout)...")
        try:
            self.page.goto("https://konto-pocztowe.interia.pl/#/nowe-konto/darmowe", timeout=60000)
            self.page.wait_for_load_state("domcontentloaded")
            self.ensure_path_clear()
        except Exception as e:
            logger.error(f"Critical: Nie udało się załadować strony. {e}")
            raise ElementNotFoundError(f"Page load failed: {e}")

    def human_delay(self) -> None:
        time.sleep(random.uniform(DELAYS.get("THINKING_MIN", 0.1), DELAYS.get("THINKING_MAX", 0.5)))

    def section_delay(self) -> None:
        time.sleep(random.uniform(DELAYS.get("SECTION_PAUSE_MIN", 0.5), DELAYS.get("SECTION_PAUSE_MAX", 1.5)))

    def human_type(self, locator: Locator, text: str, use_click: bool = True) -> None:
        try:
            if use_click:
                locator.scroll_into_view_if_needed()
                locator.click(timeout=5000)

            time.sleep(0.2)
            min_delay_ms = int(DELAYS.get("HUMAN_TYPE_MIN", 0.05) * 1000)
            max_delay_ms = int(DELAYS.get("HUMAN_TYPE_MAX", 0.15) * 1000)
            locator.press_sequentially(text, delay=random.randint(min_delay_ms, max_delay_ms))
            self.human_delay()
        except PlaywrightTimeout:
            logger.warning(f"Timeout podczas pisania w {locator}")
            raise

    def handle_captcha_if_present(self) -> bool:
        has_frame = self.captcha_frame_locator.first.is_visible()
        has_verify_text = self.verify_text.is_visible()
        has_verify_btn = self.verify_btn.is_visible()

        if not (has_frame or has_verify_text or has_verify_btn):
            return False

        logger.info("⚠️ Wykryto blokadę (Captcha/Zweryfikuj).")

        if has_verify_btn or has_verify_text:
            logger.info("👉 Klikam 'Zweryfikuj', aby odsłonić formularz...")
            try:
                if has_verify_btn:
                    self.verify_btn.click(force=True)
                else:
                    self.verify_text.click(force=True)
                time.sleep(2.0)
            except Exception as e:
                logger.warning(f"Problem z kliknięciem Zweryfikuj: {e}")

        # Szukanie ramek captchy
        visible_frames = []
        count = self.captcha_frame_locator.count()
        for i in range(count):
            frame = self.captcha_frame_locator.nth(i)
            if frame.is_visible():
                visible_frames.append(frame)

        if not visible_frames:
            return True

        for frame in visible_frames:
            box = frame.bounding_box()
            if box and box['width'] > 150 and box['height'] > 150:
                logger.warning(f"🚨 CAPTCHA AKTYWNA - Uruchamiam solver.")
                self.section_delay()
                # UWAGA: Używamy solve_loop (zgodnie z Twoim plikiem captcha_solver.py)
                if self.solver.solve_loop(frame):
                    logger.info("✅ Captcha pokonana.")
                    return True
                else:
                    raise CaptchaSolveError("Solver failed.")

        return False

    def ensure_path_clear(self) -> bool:
        """
        Zamyka RODO i inne przeszkadzajki.
        To tutaj jest klucz do sukcesu - Twój stary kod robił to lepiej.
        """
        cleared_something = False
        for btn in [self.rodo_btn_primary, self.rodo_btn_secondary, self.rodo_btn_accept_all]:
            if btn.is_visible():
                try:
                    logger.info(f"🍪 Zamykam RODO przyciskiem: {btn}")
                    btn.click()
                    cleared_something = True
                    time.sleep(1.0)  # Dajmy czas na animację znikania
                    break
                except Exception:
                    pass

        if self.handle_captcha_if_present():
            cleared_something = True

        return cleared_something

    def retry_action(self, action_name: str, action_callback: Callable[[], Any], retries: int = 3) -> None:
        """
        Mechanizm ponawiania akcji w razie zasłonięcia elementu (np. przez RODO).
        """
        for i in range(retries):
            # Przed każdą próbą upewniamy się, że droga jest czysta
            self.ensure_path_clear()
            try:
                action_callback()
                return
            except Exception as e:
                msg = str(e)
                logger.warning(f"⚠️ Retry {i + 1}/{retries} '{action_name}': {msg[:80]}...")

                # Jeśli to Playwright intercept, spróbuj uciec (Escape)
                if "intercepts" in msg:
                    self.page.keyboard.press("Escape")

                if i == retries - 1:
                    self._save_debug_screenshot(f"fail_{action_name}")
                    raise ElementNotFoundError(f"Failed to perform action: {action_name}") from e
                time.sleep(1.0)

    def _ensure_unique_login(self, identity: Dict[str, Any]) -> None:
        max_attempts = 5

        # Upewnij się, że input jest dostępny
        if not self.input_login.is_visible():
            if self.verify_btn.is_visible():
                self.verify_btn.click(force=True)
            elif self.verify_text.is_visible():
                self.verify_text.click(force=True)

        self.input_login.wait_for(state="visible", timeout=10000)

        for attempt in range(max_attempts):
            current_login = identity['login']
            logger.info(f"📧 Próba loginu ({attempt + 1}/{max_attempts}): {current_login}")

            self.input_login.clear()
            self.human_type(self.input_login, current_login, use_click=True)

            self.page.keyboard.press("Tab")
            time.sleep(1.5)

            actual_value = self.input_login.input_value()

            if not actual_value.strip():
                logger.warning("❌ Pole loginu jest PUSTE po walidacji! Generuję nowy...")
                is_error = True
            else:
                identity['login'] = actual_value
                is_error = False

            if self.login_error_locator.first.is_visible():
                logger.warning(f"❌ Login '{actual_value}' jest ZAJĘTY.")
                is_error = True

            if is_error:
                suffix = random.randint(10, 999)
                try:
                    base_parts = current_login.split('.')
                    base_login = f"{base_parts[0]}.{base_parts[1]}"
                except IndexError:
                    base_login = current_login[:10]

                identity['login'] = f"{base_login}.{suffix}"
                continue
            else:
                logger.info(f"✅ Login '{identity['login']}' zaakceptowany.")
                return

        raise RegistrationFailedError("Nie udało się znaleźć wolnego loginu po wielu próbach.")

    def fill_form(self, identity: Dict[str, Any]) -> None:
        """
        Główna metoda wypełniania. Przyjmuje słownik z identity_manager.
        """
        logger.info(f"📝 Wypełnianie: {identity['first_name']} {identity['last_name']}")

        # Używamy retry_action, które samo czyści RODO w razie błędu!
        self.retry_action("Imię", lambda: self.human_type(self.input_name, identity['first_name']))
        self.page.keyboard.press("Tab")
        self.retry_action("Nazwisko",
                          lambda: self.human_type(self.input_surname, identity['last_name'], use_click=False))

        self.section_delay()
        self.retry_action("Dzień ur.", lambda: self.human_type(self.input_day, identity['birth_day']))

        def select_month():
            self.label_month.click()
            self.page.get_by_role("listitem").filter(has_text=identity['birth_month_name']).locator(
                "span").first.click()

        self.retry_action("Miesiąc", select_month)
        self.retry_action("Rok ur.", lambda: self.human_type(self.input_year, identity['birth_year']))
        self.section_delay()

        self.retry_action("Płeć", lambda: (self.label_gender.click(), self.gender_male.click()))
        self.section_delay()

        self.retry_action("Obsługa loginu unikalnego", lambda: self._ensure_unique_login(identity))

        self.retry_action("Hasło", lambda: self.human_type(self.input_password, identity['password']))
        self.retry_action("Powtórz hasło", lambda: self.human_type(self.input_password_repeat, identity['password']))

        logger.info(f"✅ Formularz gotowy. Ostateczny login: {identity['login']}")

    def accept_terms(self) -> None:
        self.retry_action("Zgody", lambda: self.checkbox_accept_all.click())

    def submit(self) -> None:
        logger.info("🚀 SUBMIT...")
        self.retry_action("Przycisk Załóż", lambda: self.btn_submit.click())

    def verify_success(self) -> bool:
        logger.info("🕵️ Weryfikacja sukcesu...")
        try:
            self.page.wait_for_url(lambda url: "nowe-konto" not in url, timeout=15000)
            logger.info("🎉 Sukces! URL zmieniony (konto założone).")
            return True
        except Exception:
            if self.error_msg.is_visible():
                err_text = self.error_msg.first.inner_text()
                logger.error(f"❌ Błąd formularza widoczny na stronie: {err_text}")
                self._save_debug_screenshot("verify_fail_msg")

            self._save_debug_screenshot("verify_fail_timeout")
            return False