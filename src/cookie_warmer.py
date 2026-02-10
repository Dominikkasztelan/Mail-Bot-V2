# src/cookie_warmer.py
import os
import random
import time
from datetime import datetime

from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import Locator, Page
from playwright.sync_api import TimeoutError as PlaywrightTimeout

from src.logger_config import get_logger

logger = get_logger("CookieWarmer")


class CookieWarmer:
    """
    CookieWarmer v3 (Production Hardened).
    - Fix: Usunięto błąd 'unexpected keyword argument timeout' w is_visible.
    - Fix: Obsługa dynamicznego DOM Google (nowe selektory).
    - Feature: Fallback do wejścia bezpośredniego (nie tracimy profilu przy błędzie Google).
    """

    def __init__(self, page: Page):
        self.page = page
        self.debug_dir = "logs/debug_warmer"
        os.makedirs(self.debug_dir, exist_ok=True)

    def _save_debug_snapshot(self, tag: str, error: bool = False) -> None:
        """Zapisuje zrzut ekranu i HTML w momencie krytycznym.
        
        Args:
            tag: Opis kontekstu zrzutu (np. 'google_no_input').
            error: Jeśli True, prefix 'ERR', inaczej 'INFO'.
        """
        try:
            timestamp = datetime.now().strftime("%H%M%S")
            status = "ERR" if error else "INFO"
            filename_base = f"{self.debug_dir}/{timestamp}_{status}_{tag}"

            self.page.screenshot(path=f"{filename_base}.png", full_page=False)
            # HTML pomaga zrozumieć co widzi bot (Shadow DOM, iframe itp.)
            with open(f"{filename_base}.html", "w", encoding="utf-8") as f:
                f.write(self.page.content())
        except (OSError, PlaywrightError):
            pass

    @staticmethod
    def _human_delay(min_s: float = 1.0, max_s: float = 3.0) -> None:
        """Symuluje ludzkie opóźnienie między akcjami.
        
        Args:
            min_s: Minimalny czas oczekiwania w sekundach.
            max_s: Maksymalny czas oczekiwania w sekundach.
        """
        time.sleep(random.uniform(min_s, max_s))

    def _human_scroll(self) -> None:
        """Symuluje ludzkie przewijanie strony."""
        try:
            for _ in range(random.randint(3, 6)):
                self.page.mouse.wheel(0, random.randint(300, 700))
                time.sleep(random.uniform(0.5, 1.5))
        except PlaywrightError:
            pass

    def _safe_wait(self, locator: Locator, timeout: int = 2000) -> bool:
        """
        Bezpieczne oczekiwanie na element zamiast is_visible(timeout=...).
        Naprawia błąd 'unexpected keyword argument'.
        """
        try:
            locator.wait_for(state="visible", timeout=timeout)
            return True
        except PlaywrightError:
            return False

    def _handle_google_consent(self) -> bool:
        """
        Obsługa RODO Google.
        Zwraca True jeśli kliknięto, False jeśli nie znaleziono (co jest OK).
        """
        consent_selectors = [
            "button[id='L2AGLb']",  # Standard PL/EN
            "div[role='button']:has-text('Zaakceptuj wszystko')",
            "div[role='button']:has-text('Accept all')",
            "button:has-text('Zaakceptuj wszystko')",
            "form[action*='consent'] button"
        ]

        # Szybki skan (krótki timeout)
        for sel in consent_selectors:
            loc = self.page.locator(sel).first
            # Używamy własnego wrappera zamiast is_visible(timeout=...)
            if self._safe_wait(loc, timeout=1500):
                logger.info(f"🍪 [GOOGLE] Wykryto RODO: '{sel}'. Klikam.")
                try:
                    loc.click(force=True)
                    # Czekamy na zniknięcie
                    loc.wait_for(state="hidden", timeout=3000)
                    return True
                except PlaywrightError:
                    logger.warning("⚠️ [GOOGLE] Kliknięto RODO, ale błąd przy znikaniu.")
                    return True  # Zakładamy że kliknięcie przeszło

        return False

    def _simple_consent_click(self) -> None:
        """Próbuje kliknąć przycisk akceptacji RODO na różnych portalach."""
        common_selectors = [
            "button:has-text('Akceptuję')",
            "button:has-text('Zgadzam się')",
            "button[aria-label='Akceptuj wszystko']",
            ".rodo-popup-agree",
            "#onet-trust-accept-btn-handler"
        ]
        for sel in common_selectors:
            loc = self.page.locator(sel).first
            if self._safe_wait(loc, timeout=1000):
                try:
                    loc.click(force=True)
                    return
                except PlaywrightError:
                    pass

    # --- AKCJE PORTALOWE ---

    def action_visit_onet(self) -> None:
        """Odwiedza stronę główną Onet.pl."""
        logger.info("🍪 [WARMER] -> Onet")
        try:
            self.page.goto("https://www.onet.pl", timeout=20000)
            self._simple_consent_click()
            self._human_scroll()
        except PlaywrightError:
            pass

    def action_visit_wp(self) -> None:
        """Odwiedza stronę główną WP.pl."""
        logger.info("🍪 [WARMER] -> WP")
        try:
            self.page.goto("https://www.wp.pl", timeout=20000)
            self._simple_consent_click()
            self._human_scroll()
        except PlaywrightError:
            pass

    def action_visit_allegro_search(self) -> None:
        logger.info("🍪 [WARMER] -> Allegro")
        try:
            self.page.goto("https://allegro.pl", timeout=20000)
            self._simple_consent_click()

            search = self.page.get_by_placeholder("czego szukasz?")
            if self._safe_wait(search, timeout=3000):
                search.fill(random.choice(["laptop", "lego", "buty"]))
                self.page.keyboard.press("Enter")
                self._human_delay(2, 3)
                self._human_scroll()
        except Exception:
            pass

    def action_google_redirect(self) -> bool:
        """
        Scenariusz Golden Path z mechanizmami Fail-Over.
        """
        logger.info("🍪 [WARMER] Google -> Interia Redirect")
        try:
            self.page.goto("https://www.google.com", timeout=15000)

            # 1. RODO - Pierwsza próba
            self._handle_google_consent()

            # 2. Wyszukiwanie
            # Szukamy pola tekstowego uniwersalnym selektorem
            search_box = self.page.locator("textarea[name='q'], input[name='q']").first

            if not self._safe_wait(search_box, timeout=5000):
                logger.warning("⚠️ [GOOGLE] Nie widzę pola wyszukiwania. Możliwy blok RODO.")
                self._save_debug_snapshot("google_no_input", error=True)
                # Fallback: Próbujemy wejść bezpośrednio
                raise Exception("Search input not found")

            # Focus zamiast click (omija warstwy przechwytujące kliknięcia)
            search_box.focus()
            self.page.keyboard.type("poczta interia logowanie", delay=random.randint(50, 120))
            self._human_delay(0.5, 1.0)
            self.page.keyboard.press("Enter")

            # 3. Oczekiwanie na wyniki
            # Szukamy: #rso (standard), #search (stary), .g (klasa wyniku)
            results_loaded = False
            for res_sel in ["#rso", "#search", ".g", "div[data-header-feature]"]:
                if self._safe_wait(self.page.locator(res_sel).first, timeout=3000):
                    results_loaded = True
                    break

            if not results_loaded:
                # Ostatnia szansa: Może RODO wyskoczyło dopiero po Enterze?
                logger.info("❓ [GOOGLE] Brak wyników. Sprawdzam RODO ponownie...")
                if self._handle_google_consent():
                    # Jeśli kliknęliśmy RODO teraz, czekamy chwilę na wyniki
                    self.page.wait_for_timeout(2000)
                else:
                    logger.warning("⚠️ [GOOGLE] Brak wyników i brak RODO.")
                    self._save_debug_snapshot("google_no_results", error=True)
                    # Nie rzucamy błędu, tylko idziemy do fallbacku
                    pass

            # 4. Kliknięcie w link
            target_link = self.page.locator("a[href*='poczta.interia.pl']").first

            if self._safe_wait(target_link, timeout=3000):
                logger.info("🎯 [GOOGLE] Klikam w link Interii.")
                target_link.click()
                self.page.wait_for_load_state("domcontentloaded")
                return True
            else:
                logger.warning("⚠️ [GOOGLE] Link Interii nieznaleziony. Fallback Direct.")
                # Fallback Direct
                self.page.goto("https://poczta.interia.pl/", timeout=15000)
                return True  # Zwracamy True, bo cel (wejście na Interię) osiągnięty

        except Exception as e:
            logger.error(f"❌ Google Fail: {e}")
            # Ostateczny Fallback - żeby nie marnować profilu
            try:
                self.page.goto("https://poczta.interia.pl/", timeout=10000)
                logger.info("✅ [WARMER] Uratowano sesję wejściem bezpośrednim.")
                return True
            except PlaywrightError:
                return False

    def run_scenario(self) -> bool:
        # Losowy portal newsowy/zakupowy
        fillers = [self.action_visit_onet, self.action_visit_wp, self.action_visit_allegro_search]
        try:
            random.choice(fillers)()
            self._human_delay(2.0, 4.0)
        except (PlaywrightTimeout, Exception):
            pass

        # Google Path (z wbudowanym fallbackiem)
        return self.action_google_redirect()
