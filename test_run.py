# test_run.py
import random
import time
import os
from typing import Any, Dict, cast, Optional

from playwright.sync_api import sync_playwright, Page, BrowserContext, ViewportSize, Geolocation
from playwright_stealth import Stealth

# Importy lokalne
from src.registration_page import RegistrationPage
from src.config import USER_AGENTS, BROWSER_ARGS
from src.profile_manager import ProfileManager
from src.identity_manager import IdentityManager
from src.storage_manager import StorageManager
from src.logger_config import logger
from src.exceptions import CaptchaSolveError, RegistrationFailedError


def run_worker(instance_id: int, file_lock: Any) -> None:
    time.sleep(instance_id * 2.0)
    prefix = f"[Worker-{instance_id}]"

    profile_mgr = ProfileManager()
    identity_mgr = IdentityManager()
    storage_mgr = StorageManager()

    # 1. POBRANIE PROFILU
    profile_data: Optional[Dict[str, Any]] = None
    for i in range(10):
        profile_data = profile_mgr.get_fresh_profile()
        if profile_data:
            break
        time.sleep(5)

    if not profile_data:
        logger.warning(f"{prefix} ⚠️ Brak profili w kolejce. Kończę pracę.")
        return

    # 2. GENEROWANIE DANYCH
    identity = identity_mgr.generate(lock=file_lock)
    logger.info(f"{prefix} 🎭 Tożsamość: {identity['login']}")

    metadata = profile_data.get("metadata", {})
    selected_ua = metadata.get("user_agent", random.choice(USER_AGENTS))

    vp_raw = metadata.get("viewport", {"width": 1366, "height": 768})
    current_viewport: ViewportSize = {"width": vp_raw["width"], "height": vp_raw["height"]}
    geo_data: Geolocation = {"latitude": 52.2297, "longitude": 21.0122}

    # FIX: Double Cast dla ciasteczek
    raw_cookies = profile_data.get("cookies")
    cookies_data = cast(Dict[str, Any], cast(object, raw_cookies))

    is_headless = os.getenv("HEADLESS", "False").lower() == "true"

    with sync_playwright() as p:
        # FIX: Użycie channel="chrome" i BROWSER_ARGS z configa
        browser = p.chromium.launch(
            channel="chrome",
            headless=is_headless,
            args=BROWSER_ARGS
        )

        context: BrowserContext = browser.new_context(
            storage_state=cast(Any, cookies_data),
            user_agent=selected_ua,
            viewport=current_viewport,
            locale="pl-PL",
            timezone_id="Europe/Warsaw",
            permissions=["geolocation"],
            geolocation=geo_data
        )
        context.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

        page: Page = context.new_page()
        stealth = Stealth()
        stealth.use_sync(cast(Any, page))

        bot = RegistrationPage(page)

        try:
            bot.load()
            bot.fill_form(identity)
            bot.accept_terms()
            bot.submit()

            if bot.verify_success():
                logger.info(f"{prefix} 🎉 SUKCES!")
                storage_mgr.save_account(identity, lock=file_lock)
            else:
                logger.error(f"{prefix} ❌ Błąd weryfikacji.")

        except CaptchaSolveError:
            logger.critical(f"{prefix} 🤖 Nie udało się rozwiązać Captchy.")
        except RegistrationFailedError as e:
            logger.error(f"{prefix} ⛔ Rejestracja odrzucona: {e}")
        # noinspection PyBroadException
        except Exception as e:
            logger.critical(f"{prefix} 💥 Krytyczny błąd: {e}")
            try:
                page.screenshot(path=f"logs/crash_{instance_id}.png")
            except Exception:
                pass
        finally:
            try:
                context.close()
                browser.close()
            except Exception:
                pass


if __name__ == "__main__":
    from multiprocessing import Lock

    run_worker(1, Lock())