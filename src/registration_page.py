import re
import time
import random
from typing import Callable, Any
from playwright.sync_api import Page, Locator

from src.captcha_solver import CaptchaSolver
from src.config import DELAYS
from src.models import UserIdentity
from src.logger_config import logger
# IMPORTUJEMY NOWE WYJĄTKI
from src.exceptions import ElementNotFoundError, CaptchaSolveError, RegistrationFailedError


class RegistrationPage:
    def __init__(self, page: Page) -> None:
        self.page: Page = page
        self.solver: CaptchaSolver = CaptchaSolver(page)

        # --- SELEKTORY ---
        self.input_name: Locator = page.get_by_role("textbox", name="Imię")
        self.input_surname: Locator = page.get_by_role("textbox", name="Nazwisko")
        self.input_day: Locator = page.get_by_role("textbox", name="Dzień")
        self.label_month: Locator = page.locator(".account-input__label").filter(has_text="Miesiąc")
        self.input_year: Locator = page.get_by_role("textbox", name="Rok ur.")
        self.label_gender: Locator = page.get_by_text("Jak się do Ciebie zwracać?")
        self.gender_male: Locator = page.get_by_role("list").filter(has_text="Pan Pani").locator("span").first
        self.input_login: Locator = page.get_by_role("textbox", name="Nazwa konta")
        self.input_password: Locator = page.get_by_role("textbox", name="Hasło", exact=True)
        self.input_password_repeat: Locator = page.get_by_role("textbox", name="Powtórz hasło")
        self.checkbox_accept_all: Locator = page.locator("div").filter(
            has_text=re.compile(r"^Akceptuję i zaznaczam wszystkie poniższe zgody$")).first
        self.btn_submit: Locator = page.get_by_role("button", name="Załóż darmowe konto")

        # --- PRZESZKADZAJKI ---
        self.rodo_btn_primary: Locator = page.get_by_role("button", name="Przejdź do serwisu")
        self.rodo_btn_secondary: Locator = page.get_by_role("button", name="Zgoda")
        self.rodo_btn_accept_all: Locator = page.locator(".rodo-popup-agree")
        self.captcha_frame_locator: Locator = page.locator("iframe[src*='captcha'], iframe[src*='recaptcha']")
        self.verify_text: Locator = page.locator("text=Zweryfikuj")

    def load(self) -> None:
        logger.info("🔄 Otwieram stronę rejestracji...")
        try:
            self.page.goto("https://konto-pocztowe.interia.pl/#/nowe-konto/darmowe", timeout=60000)
            time.sleep(random.uniform(DELAYS["PAGE_LOAD_MIN"], DELAYS["PAGE_LOAD_MAX"]))
            self.ensure_path_clear()
        except Exception as e:
            # Tu łapiemy błąd sieciowy Playwrighta
            raise ElementNotFoundError(f"Nie udało się załadować strony: {e}")

    # --- MECHANIKA ---

    def human_delay(self) -> None:
        time.sleep(random.uniform(DELAYS["THINKING_MIN"], DELAYS["THINKING_MAX"]))

    def section_delay(self) -> None:
        time.sleep(random.uniform(DELAYS["SECTION_PAUSE_MIN"], DELAYS["SECTION_PAUSE_MAX"]))

    def human_type(self, locator: Locator, text: str, use_click: bool = True) -> None:
        if use_click:
            locator.scroll_into_view_if_needed()
            time.sleep(0.5)
            locator.click()

        time.sleep(0.5)
        min_delay_ms = int(DELAYS["HUMAN_TYPE_MIN"] * 1000)
        max_delay_ms = int(DELAYS["HUMAN_TYPE_MAX"] * 1000)

        logger.debug(f"Wpisuję: {text[:2]}***")
        locator.press_sequentially(text, delay=random.randint(min_delay_ms, max_delay_ms))
        self.human_delay()

    def handle_captcha_if_present(self) -> bool:
        if not self.captcha_frame_locator.first.is_visible() and not self.verify_text.is_visible():
            return False

        logger.info("⚠️ Wykryto potencjalną Captchę.")
        count = self.captcha_frame_locator.count()

        for i in range(count):
            frame = self.captcha_frame_locator.nth(i)
            if frame.is_visible():
                box = frame.bounding_box()
                if box and box['width'] > 150 and box['height'] > 150:
                    logger.warning(f"🚨 CAPTCHA AKTYWNA - Uruchamiam solver.")
                    self.section_delay()

                    if self.solver.solve_loop(frame):
                        logger.info("✅ Captcha pokonana.")
                        return True
                    else:
                        # Rzucamy specyficzny błąd zamiast tylko logować
                        logger.error("❌ Solver zawiódł.")
                        raise CaptchaSolveError("Nie udało się rozwiązać Captchy po wielu próbach.")
        return False

    def ensure_path_clear(self) -> bool:
        cleared_something = False
        if self.rodo_btn_primary.is_visible():
            self.rodo_btn_primary.click()
        elif self.rodo_btn_secondary.is_visible():
            self.rodo_btn_secondary.click()
        elif self.rodo_btn_accept_all.is_visible():
            self.rodo_btn_accept_all.click()

        if self.handle_captcha_if_present():
            cleared_something = True
        return cleared_something

    def retry_action(self, action_name: str, action_callback: Callable[[], Any], retries: int = 3) -> None:
        """Wykonuje akcję z ponawianiem. Rzuca ElementNotFoundError w przypadku porażki."""
        self.ensure_path_clear()
        for i in range(retries):
            try:
                logger.debug(f"👉 {action_name} ({i + 1}/{retries})")
                action_callback()
                return
            except Exception as e:
                if "intercepts" in str(e):
                    logger.warning("🧱 Zasłonięte. ESC...")
                    self.page.keyboard.press("Escape")
                    time.sleep(0.5)
                else:
                    logger.warning(f"⚠️ Problem z '{action_name}': {e}")
                time.sleep(1)

        # Po wyczerpaniu prób rzucamy nasz własny błąd
        raise ElementNotFoundError(f"Nie udało się wykonać akcji: {action_name} po {retries} próbach.")

    def fill_form(self, identity: UserIdentity) -> None:
        logger.info("📝 Wypełnianie formularza...")
        # Tutaj nie musimy dawać try-except, bo wyjątki obsłuży test_run.py

        self.retry_action("Wpisanie imienia", lambda: self.human_type(self.input_name, identity['first_name']))

        self.page.keyboard.press("Tab")
        self.retry_action("Wpisanie nazwiska",
                          lambda: self.human_type(self.input_surname, identity['last_name'], use_click=False))

        self.section_delay()

        self.retry_action("Wpisanie dnia ur.", lambda: self.human_type(self.input_day, identity['birth_day']))

        def select_month() -> None:
            self.label_month.scroll_into_view_if_needed()
            self.label_month.click()
            time.sleep(0.5)
            self.page.get_by_role("listitem").filter(has_text=identity['birth_month_name']).locator(
                "span").first.click()

        self.retry_action("Wybór miesiąca", select_month)

        self.retry_action("Wpisanie roku", lambda: self.human_type(self.input_year, identity['birth_year']))

        self.section_delay()

        def select_gender() -> None:
            self.label_gender.scroll_into_view_if_needed()
            self.label_gender.click()
            time.sleep(0.5)
            self.gender_male.click()

        self.retry_action("Wybór płci", select_gender)

        logger.info("☕ Przerwa przed loginem...")
        self.section_delay()

        self.retry_action("Wpisanie loginu", lambda: self.human_type(self.input_login, identity['login']))
        self.retry_action("Wpisanie hasła", lambda: self.human_type(self.input_password, identity['password']))
        self.retry_action("Powtórzenie hasła",
                          lambda: self.human_type(self.input_password_repeat, identity['password']))

        logger.info("✅ Formularz wypełniony.")

    def accept_terms(self) -> None:
        logger.info("📜 Akceptacja zgód...")
        self.section_delay()
        self.retry_action("Akceptacja checkboxa", lambda: self.checkbox_accept_all.click())

    def submit(self) -> None:
        logger.info("🚀 SUBMIT...")
        self.section_delay()
        self.retry_action("Kliknięcie Załóż Konto", lambda: self.btn_submit.click())

        # Weryfikacja czy przeszło (np. sprawdzamy czy URL się zmienił albo czy zniknął formularz)
        # Na razie zostawiamy tak, ale w wersji PRO sprawdzalibyśmy sukces tutaj.