# src/registration_page.py
import os
import random
import re
import time
from collections.abc import Callable
from typing import Any

from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import Frame, Locator, Page
from playwright.sync_api import TimeoutError as PlaywrightTimeout

from src.captcha_solver import CaptchaSolver
from src.config import DELAYS, REGISTRATION_URL, RETRY_LIMITS
from src.exceptions import CaptchaBlockadeError, ElementNotFoundError, RegistrationFailedError
from src.logger_config import get_logger

logger = get_logger(__name__)

class RegistrationPage:
    """
    Page Object Model for the registration page.
    Production-Ready:
    - Non-blocking waits (page.wait_for_timeout)
    - strict typing
    - Robust handling of existing account check
    """

    DEFAULT_DOMAIN = "interia.pl"

    def __init__(self, page: Page) -> None:
        self.page: Page = page
        self.solver: CaptchaSolver = CaptchaSolver(page)

        # --- FORM SELECTORS ---
        self.input_name: Locator = page.get_by_role("textbox", name="Imię")
        self.input_surname: Locator = page.get_by_role("textbox", name="Nazwisko")
        self.input_day: Locator = page.get_by_role("textbox", name="Dzień")
        self.label_month: Locator = page.locator(".account-input__label").filter(has_text="Miesiąc")
        self.input_year: Locator = page.get_by_role("textbox", name="Rok ur.")

        self.label_gender: Locator = page.get_by_text("Jak się do Ciebie zwracać?")
        self.gender_male: Locator = page.get_by_role("list").filter(has_text="Pan Pani").locator("span").first

        # Login and Domain
        self.input_login: Locator = page.get_by_label("Nazwa konta", exact=False)
        self.domain_select_trigger: Locator = page.locator(".account-identity__domain-select")

        self.input_password: Locator = page.get_by_role("textbox", name="Hasło", exact=True)
        self.input_password_repeat: Locator = page.get_by_role("textbox", name="Powtórz hasło")

        self.checkbox_accept_all: Locator = page.locator("div").filter(
            has_text=re.compile(r"^Akceptuję i zaznaczam wszystkie poniższe zgody$")).first
        self.btn_submit: Locator = page.get_by_role("button", name="Załóż darmowe konto")

        # --- BLOCKADE SELECTORS ---
        self.rodo_btn_primary: Locator = page.get_by_role("button", name="Przejdź do serwisu")
        self.rodo_btn_secondary: Locator = page.get_by_role("button", name="Zgoda")
        self.rodo_btn_accept_all: Locator = page.locator(".rodo-popup-agree")

        self.verify_text: Locator = page.locator("text=Zweryfikuj")
        self.verify_btn: Locator = page.get_by_role("button", name="Zweryfikuj")

    def _save_debug_screenshot(self, name: str) -> None:
        """Safe screenshot capture that ignores errors."""
        try:
            if not os.path.exists("logs"):
                os.makedirs("logs", exist_ok=True)
            timestamp = time.strftime("%H%M%S")
            path = f"logs/debug_{timestamp}_{name}.png"
            self.page.screenshot(path=path)
            logger.info(f"📸 Saved screenshot: {path}")
        except Exception:
            pass

    def load(self) -> None:
        logger.info("🔄 Opening registration page...")
        try:
            self.page.goto(REGISTRATION_URL, timeout=60000)
            self.page.wait_for_load_state("domcontentloaded")
            try:
                self.ensure_path_clear()
            except CaptchaBlockadeError:
                logger.warning("⚠️ Page loaded with active Captcha blockade!")
        except (PlaywrightError, PlaywrightTimeout) as e:
            logger.error(f"Critical: Failed to load page. {e}")
            raise ElementNotFoundError(f"Page load failed: {e}")

    def human_delay(self) -> None:
        """Simulate human thinking time using browser timeout."""
        delay = random.uniform(DELAYS.get("THINKING_MIN", 0.1), DELAYS.get("THINKING_MAX", 0.5))
        self.page.wait_for_timeout(delay * 1000)

    def section_delay(self) -> None:
        """Simulate delay between form sections."""
        delay = random.uniform(DELAYS.get("SECTION_PAUSE_MIN", 0.5), DELAYS.get("SECTION_PAUSE_MAX", 1.5))
        self.page.wait_for_timeout(delay * 1000)

    def human_type(self, locator: Locator, text: str, use_click: bool = True) -> None:
        """Type text with human-like delays."""
        if use_click:
            locator.scroll_into_view_if_needed()
            locator.click(timeout=5000)

        self.page.wait_for_timeout(200)
        min_delay_ms = int(DELAYS.get("HUMAN_TYPE_MIN", 0.05) * 1000)
        max_delay_ms = int(DELAYS.get("HUMAN_TYPE_MAX", 0.15) * 1000)
        locator.press_sequentially(text, delay=random.randint(min_delay_ms, max_delay_ms))
        self.human_delay()

    def handle_captcha_if_present(self) -> bool:
        """Checks for blockade and solves if present."""
        has_blockade_ui = self._is_blockade_ui_visible()
        frames = self._get_captcha_frames()

        if not (has_blockade_ui or frames):
            return False

        logger.info("⚠️ Potential blockade detected.")

        if has_blockade_ui:
            self._handle_blockade_ui()

        target_frame = self._find_target_frame()

        if target_frame:
            logger.warning("🚨 Passing frame to Solver...")
            if self.solver.solve_loop(target_frame):
                return True
            else:
                self._save_debug_screenshot("captcha_failed")
                raise CaptchaBlockadeError("Solver failed to solve Captcha.")

        if has_blockade_ui:
            # Check if still blocked after attempts
            if self.verify_btn.is_visible() or self.verify_text.is_visible():
                self._save_debug_screenshot("blocked_dead_end")
                raise CaptchaBlockadeError("Blockade visible but no image frame found.")

        return False

    def _is_blockade_ui_visible(self) -> bool:
        return self.verify_text.is_visible() or self.verify_btn.is_visible()

    def _get_captcha_frames(self) -> list[Frame]:
        return [f for f in self.page.frames if "recaptcha" in f.url or "captcha" in f.url]

    def _handle_blockade_ui(self) -> None:
        try:
            if self.verify_btn.is_visible():
                self.verify_btn.click(force=True)
            else:
                self.verify_text.click(force=True)
            self.page.wait_for_timeout(2500)
        except (PlaywrightError, PlaywrightTimeout):
            pass

    def _find_target_frame(self) -> Frame | None:
        # Try to find frame with payload
        for attempt in range(5):
            all_frames = self.page.frames
            target_frame = None

            for frame in all_frames:
                if frame.is_detached(): continue
                url = frame.url.lower()

                if ("recaptcha" in url) and ("bframe" in url or "payload" in url):
                    target_frame = frame
                    break

                try:
                    if frame.locator("#rc-imageselect-target, table, .rc-imageselect-payload").first.is_visible():
                        target_frame = frame
                        break
                except (PlaywrightError, PlaywrightTimeout):
                    pass

            if target_frame:
                return target_frame

            self._attempt_checkbox_click(all_frames)
            self.page.wait_for_timeout(1000)

        return None

    def _attempt_checkbox_click(self, frames: list[Frame]) -> None:
        for frame in frames:
            if frame.is_detached(): continue
            cb = frame.locator("#recaptcha-anchor").first
            if cb.is_visible():
                class_attr = cb.get_attribute("class") or ""
                if "checked" not in class_attr:
                    cb.click()
                    self.page.wait_for_timeout(2000)
                break

    def ensure_path_clear(self) -> None:
        """Removes obstacles (RODO, Captcha)."""
        # Small delay to allow RODO banner to fully render/animate
        self.page.wait_for_timeout(2000)

        for btn in [self.rodo_btn_primary, self.rodo_btn_secondary, self.rodo_btn_accept_all]:
            if btn.is_visible():
                try:
                    btn.click()
                    self.page.wait_for_timeout(500)
                    break
                except (PlaywrightError, PlaywrightTimeout):
                    pass
        self.handle_captcha_if_present()

    def retry_action(self, action_name: str, action_callback: Callable[[], Any], retries: int = 3) -> None:
        """Retries an action, ensuring path is clear of captchas."""
        for i in range(retries):
            try:
                self.ensure_path_clear()
                action_callback()
                return
            except CaptchaBlockadeError:
                logger.critical(f"⛔ STOP: Captcha blockade during '{action_name}'.")
                raise
            except (PlaywrightError, PlaywrightTimeout) as e:
                logger.warning(f"⚠️ Retry {i + 1}/{retries} '{action_name}': {str(e)[:100]}")
                if "intercepts" in str(e):
                    self.page.keyboard.press("Escape")
                if i == retries - 1:
                    raise ElementNotFoundError(f"Failed: {action_name}") from e
                self.page.wait_for_timeout(1000)

    def fill_form(self, identity: dict[str, Any]) -> None:
        logger.info(f"📝 Filling form: {identity['first_name']} {identity['last_name']}")

        self.retry_action("FirstName", lambda: self.human_type(self.input_name, identity['first_name']))
        self.page.keyboard.press("Tab")
        self.retry_action("LastName",
                          lambda: self.human_type(self.input_surname, identity['last_name'], use_click=False))
        self.section_delay()

        self.retry_action("Day", lambda: self.human_type(self.input_day, identity['birth_day']))

        def sel_month():
            self.label_month.click()
            self.page.get_by_role("listitem").get_by_text(identity['birth_month_name'], exact=True).click()

        self.retry_action("Month", sel_month)
        self.retry_action("Year", lambda: self.human_type(self.input_year, identity['birth_year']))
        self.section_delay()

        self.retry_action("Gender", lambda: (self.label_gender.click(), self.gender_male.click()))
        self.section_delay()

        # --- LOGIN UNIQUENESS ---
        self._ensure_unique_identity(identity)

        self.retry_action("Password", lambda: self.human_type(self.input_password, identity['password']))
        self.retry_action("RepeatPass", lambda: self.human_type(self.input_password_repeat, identity['password']))

    def accept_terms(self) -> None:
        self.retry_action("Terms", lambda: self.checkbox_accept_all.click())

    def submit(self) -> None:
        self.retry_action("Submit", lambda: self.btn_submit.click())

    def verify_success(self) -> bool:
        try:
            self.page.wait_for_url(lambda u: "nowe-konto" not in u, timeout=15000)
            return True
        except (PlaywrightError, PlaywrightTimeout):
            return False

    def _select_domain(self, domain: str) -> bool:
        """
        Selects a domain. If domain is default, return True immediately.
        """
        if domain == self.DEFAULT_DOMAIN:
            # logger.debug(f"🌐 Domain is {self.DEFAULT_DOMAIN} (default). Skipping selection.")
            return True

        try:
            logger.info(f"🌐 Changing domain to: {domain}")
            self.domain_select_trigger.click()
            self.page.wait_for_timeout(500)

            option = self.page.locator(".account-identity__domain-select-item").filter(has_text=domain).first
            if option.is_visible():
                option.click()
                self.page.wait_for_timeout(1000)
                return True
            else:
                logger.warning(f"⚠️ Domain {domain} not visible.")
                self.page.mouse.click(0, 0)
                return False
        except (PlaywrightError, PlaywrightTimeout) as e:
            logger.error(f"❌ Failed to switch domain: {e}")
            return False

    def _check_availability(self) -> bool:
        """Checks if login or domain fields show error."""
        if self.page.locator(".input-error-message").is_visible():
            return False

        # Sometimes there are multiple error divs
        if self.page.locator("div.account-identity .input-error-message").count() > 0:
            return False

        return True

    def _ensure_unique_identity(self, identity: dict[str, Any]) -> None:
        """Generates a unique login using retries."""
        self.input_login.wait_for(state="visible", timeout=10000)
        base_login = identity['login']

        # Normalize base login
        if '.' in base_login and len(base_login) > 5:
             # Assume 'name.surname' structure
             parts = base_login.split('.')
             base_login = f"{parts[0]}.{parts[1]}"

        attempts_limit = RETRY_LIMITS.get("LOGIN_ATTEMPTS", 10)
        for attempt in range(attempts_limit):
            current_login = self._generate_login_variant(base_login, attempt)

            self._fill_login_field(current_login)
            self.page.wait_for_timeout(1000)

            # _select_domain handles the hard skip for defaults logic internally
            if self._select_domain(self.DEFAULT_DOMAIN):
                if self._check_availability():
                    logger.info(f"✅ Available account found: {current_login} @ {self.DEFAULT_DOMAIN}")

                    identity['login'] = current_login
                    identity['domain'] = self.DEFAULT_DOMAIN
                    return

            # Simple backoff/retry
            logger.warning(f"⚠️ Login {current_login}@{self.DEFAULT_DOMAIN} taken. Retrying...")

        raise RegistrationFailedError(f"Could not find free login in {self.DEFAULT_DOMAIN} after {attempts_limit} attempts.")

    def _generate_login_variant(self, base_login: str, attempt: int) -> str:
        if attempt == 0:
            if len(base_login) > 20:
                 return f"{base_login}.{random.randint(100, 999)}"
            return base_login

        suffix = str(random.randint(100, 9999))
        return f"{base_login}.{suffix}"[:30]

    def _fill_login_field(self, login: str) -> None:
        self.input_login.click()
        self.page.keyboard.press("Control+A")
        self.page.keyboard.press("Backspace")
        self.input_login.press_sequentially(login, delay=50)
        self.page.keyboard.press("Tab")
