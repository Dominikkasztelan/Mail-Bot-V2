# run_farmer.py
import time
import random
from typing import Dict, Any, cast

# ZEWNĘTRZNE
from playwright.sync_api import sync_playwright, Page, BrowserContext, ViewportSize, Geolocation
from playwright_stealth import Stealth

# LOKALNE
from src.config import USER_AGENTS, VIEWPORTS, BROWSER_ARGS
from src.cookie_warmer import CookieWarmer
from src.profile_manager import ProfileManager
from src.logger_config import get_logger

logger = get_logger("Farmer")

# KONFIGURACJA FARMERA
MAX_POOL_SIZE = 20
FARMER_HEADLESS = False  # Ustaw True na produkcji (VPS)


def run_farmer_loop() -> None:
    manager = ProfileManager()
    logger.info("🚜 Startuję Farmera Ciasteczek (Producer)...")

    while True:
        try:
            current_count = manager.count_ready()
            if current_count >= MAX_POOL_SIZE:
                logger.info(f"💤 Magazyn pełny ({current_count}/{MAX_POOL_SIZE}). Czekam 30s...")
                time.sleep(30)
                continue

            logger.info(f"🌱 Generuję nowy profil (Stan: {current_count})...")

            selected_ua = random.choice(USER_AGENTS)
            vp_raw = random.choice(VIEWPORTS)

            # FIX: Explicit Type Hinting
            width = int(vp_raw["width"])
            height = int(vp_raw["height"])
            viewport_data: ViewportSize = {"width": width, "height": height}
            geo_data: Geolocation = {"latitude": 52.2297, "longitude": 21.0122}

            with sync_playwright() as p:
                # FIX: Użycie channel="chrome" i flag z Configa
                browser = p.chromium.launch(
                    channel="chrome",
                    headless=FARMER_HEADLESS,
                    args=BROWSER_ARGS
                )

                context: BrowserContext = browser.new_context(
                    user_agent=selected_ua,
                    viewport=viewport_data,
                    locale="pl-PL",
                    timezone_id="Europe/Warsaw",
                    permissions=["geolocation"],
                    geolocation=geo_data
                )

                context.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

                page: Page = context.new_page()

                # FIX: Stealth 2.0 + Cast to Any
                stealth = Stealth()
                stealth.use_sync(cast(Any, page))

                warmer = CookieWarmer(page)
                warmer.run_scenario()

                # FIX: Double Cast dla StorageState
                raw_state = context.storage_state()
                cookies_json = cast(Dict[str, Any], cast(object, raw_state))

                manager.save_profile(
                    cookies=cookies_json,
                    metadata={
                        "user_agent": selected_ua,
                        "viewport": vp_raw,
                        "created_by": "Farmer-v2"
                    }
                )

                context.close()
                browser.close()

            time.sleep(random.uniform(2, 5))

        # noinspection PyBroadException
        except Exception as e:
            logger.error(f"💥 Błąd w cyklu farmera: {e}")
            time.sleep(5)


if __name__ == "__main__":
    run_farmer_loop()