# src/cookie_warmer.py
import time
import random
from playwright.sync_api import Page

from src.logger_config import get_logger

logger = get_logger("CookieWarmer")


class CookieWarmer:
    """
    Klasa odpowiedzialna za "wygrzewanie" profilu przeglądarki przed właściwą rejestracją.
    Generuje historię, ciasteczka i cache, aby bot wyglądał na realnego użytkownika.
    """

    def __init__(self, page: Page):
        self.page = page

    # FIX: Metoda statyczna (brak self)
    @staticmethod
    def _human_delay(min_s=1.0, max_s=3.0):
        time.sleep(random.uniform(min_s, max_s))

    def _human_scroll(self):
        """Symuluje czytanie strony (scrollowanie w dół i czasem w górę)."""
        # noinspection PyBroadException
        try:
            for _ in range(random.randint(3, 6)):
                scroll_amount = random.randint(300, 700)
                self.page.mouse.wheel(0, scroll_amount)
                time.sleep(random.uniform(0.5, 1.5))

                if random.random() < 0.3:
                    self.page.mouse.wheel(0, -random.randint(100, 300))
                    time.sleep(0.5)
        except Exception:
            pass

    def _simple_consent_click(self):
        """Uniwersalna próba zamknięcia pop-upów RODO/Cookie."""
        common_selectors = [
            "button:has-text('Akceptuję')",
            "button:has-text('Zgadzam się')",
            "button:has-text('Przejdź do serwisu')",
            "button[aria-label='Akceptuj wszystko']",
            ".rodo-popup-agree"
        ]
        for sel in common_selectors:
            # noinspection PyBroadException
            try:
                btn = self.page.locator(sel).first
                if btn.is_visible():
                    btn.click(timeout=1000)
                    self._human_delay(0.5, 1.0)
                    return
            except Exception:
                continue

    # --- AKCJE BUDUJĄCE HISTORIĘ ---

    def action_visit_onet(self):
        logger.info("🍪 [WARMER] Odwiedzam Onet...")
        # noinspection PyBroadException
        try:
            self.page.goto("https://www.onet.pl", timeout=20000)
            self._simple_consent_click()
            self._human_scroll()

            links = self.page.locator("a.itemUrl").all()
            if links:
                random.choice(links[:5]).click(timeout=3000)
                self._human_delay(2, 4)
                self._human_scroll()
        except Exception:
            pass

    def action_visit_wp(self):
        logger.info("🍪 [WARMER] Odwiedzam WP...")
        # noinspection PyBroadException
        try:
            self.page.goto("https://www.wp.pl", timeout=20000)
            self._simple_consent_click()
            self._human_scroll()
        except Exception:
            pass

    def action_visit_allegro_search(self):
        logger.info("🍪 [WARMER] Odwiedzam Allegro (Szukanie)...")
        # noinspection PyBroadException
        try:
            self.page.goto("https://allegro.pl", timeout=20000)
            self._simple_consent_click()

            search_bar = self.page.get_by_placeholder("czego szukasz?")
            if search_bar.is_visible():
                products = ["laptop", "iphone case", "karma dla kota", "buty nike", "lego"]
                query = random.choice(products)

                search_bar.click()
                self.page.keyboard.type(query, delay=100)
                self.page.keyboard.press("Enter")
                self._human_delay(2, 4)
                self._human_scroll()
        except Exception as e:
            logger.warning(f"⚠️ Allegro fail: {e}")

    def action_google_redirect(self):
        logger.info("🍪 [WARMER] Google -> Interia Redirect (Golden Path)")
        # noinspection PyBroadException
        try:
            self.page.goto("https://www.google.com", timeout=15000)
            self._simple_consent_click()

            search_box = self.page.get_by_role("combobox", name="Szukaj").or_(
                self.page.locator('textarea[name="q"]')).first

            search_box.click()
            self.page.keyboard.type("poczta interia logowanie", delay=random.randint(50, 150))
            self._human_delay(0.5, 1.0)
            self.page.keyboard.press("Enter")

            self.page.wait_for_load_state("domcontentloaded")
            self._human_delay(1.5, 3.0)

            target_link = self.page.locator("a[href*='interia.pl']").first

            if target_link.is_visible():
                logger.info("   -> Znaleziono link w Google, klikam...")
                target_link.click()
            else:
                logger.warning("   -> Nie znaleziono linku Interii w Google! Wchodzę bezpośrednio.")
                self.page.goto("https://poczta.interia.pl/")

        except Exception as e:
            logger.error(f"❌ Google Redirect Failed: {e}")
            self.page.goto("https://poczta.interia.pl/")

    def run_scenario(self):
        fillers = [self.action_visit_onet, self.action_visit_wp, self.action_visit_allegro_search]
        chosen_fillers = random.sample(fillers, k=random.randint(1, 2))

        for action in chosen_fillers:
            # noinspection PyBroadException
            try:
                action()
                self._human_delay(2.0, 5.0)
            except Exception as e:
                logger.warning(f"⚠️ Warmer action failed: {e}")

        self.action_google_redirect()