#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Moduł do rozwiązywania CAPTCHA przez ChatGPT
Zawiera funkcje do komunikacji z ChatGPT w celu rozpoznawania tekstu z obrazu
"""

import time
import random
import base64
import os
import traceback
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains

# Import z głównego modułu (jeśli dostępny)
try:
    from src.logger_config import get_logger

    logger = get_logger(__name__)
except ImportError:
    import logging

    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(name)s - %(message)s'))
        logger.addHandler(handler)


class ChatGPTCaptchaSolver:
    """Klasa do rozwiązywania CAPTCHA przez ChatGPT"""

    # Selektory dla ChatGPT
    INPUT_FIELD_SELECTORS = [
        "//textarea[contains(@placeholder, 'Send a message')]",
        "//div[contains(@class, 'input')]//textarea",
        "textarea[placeholder*='message' i]",
        "#prompt-textarea"
    ]

    # Selektory dla odpowiedzi - POPRAWIONE SELEKTORY
    RESPONSE_SELECTORS = [
        "//div[contains(@class, 'markdown') and not(ancestor::div[contains(@data-message-author-role, 'user')])]",
        "//div[@data-message-author-role='assistant']//div[contains(@class, 'markdown')]/p",
        "//div[@data-message-author-role='assistant']//div[contains(@class, 'markdown')]",
        "//div[@data-message-author-role='assistant']//div/p",
        "//div[@data-message-author-role='assistant']//p",
        "//article//div[contains(@class, 'markdown')]/p",
        "//article//div[contains(@class, 'prose')]/p",
        "//article//div[contains(@class, 'prose')]",
        "//div[@data-message-author-role='assistant' and contains(@class, 'message')]//div[contains(@class, 'text-message')]",
        "[data-message-author-role='assistant'] p",
        "[data-message-author-role='assistant'] div.prose"
    ]

    # Selektory dla wskaźników ładowania odpowiedzi
    RESPONSE_LOADING_SELECTORS = [
        "//button[contains(text(), 'Stop generating')]",
        "//button[contains(text(), 'Stop')]",
        "//button[contains(@aria-label, 'Stop')]",
        "//div[contains(@class, 'result-streaming')]",
        "//div[contains(@class, 'streaming')]",
        "//div[contains(@class, 'thinking')]",
    ]

    # User agents
    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ]

    def __init__(self, headless=False, timeout=60):
        """Inicjalizuje solver CAPTCHA"""
        self.driver = None
        self.headless = headless  # Domyślnie ustawione na False
        self.timeout = timeout
        self.chatgpt_url = "https://chatgpt.com/"

    def __enter__(self):
        """Kontekst menedżer - inicjalizacja"""
        # Zawsze inicjalizuj nową przeglądarkę przy tworzeniu obiektu
        self._setup_browser()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Kontekst menedżer - czyszczenie"""
        if self.driver:
            try:
                self.driver.quit()
                logger.info("✅ Przeglądarka ChatGPT zamknięta")
            except Exception as e:
                logger.error(f"❌ Błąd podczas zamykania przeglądarki: {e}")

    def _setup_browser(self):
        """Konfiguruje stealth browser"""
        try:
            options = uc.ChromeOptions()
            options.add_argument(f"--user-agent={random.choice(self.USER_AGENTS)}")

            # Zwiększ rozdzielczość okna dla lepszej widoczności
            options.add_argument("--window-size=1920,1080")

            # Tryb headless jeśli potrzebny
            if self.headless:
                options.add_argument("--headless")

            # Podstawowe opcje
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_argument("--no-first-run")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-popup-blocking")

            # Usunięcie istniejącego drivera jeśli istnieje
            if self.driver:
                try:
                    self.driver.quit()
                except:
                    pass
                self.driver = None

            # Tworzenie driver
            self.driver = uc.Chrome(options=options)
            logger.info("✅ Chrome driver dla ChatGPT utworzony pomyślnie")

            # Ustaw rozmiar okna
            self.driver.set_window_size(1920, 1080)

            # JavaScript stealth patches
            self.driver.execute_script("""
                // Usuń webdriver property
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined,
                });

                // Usuń automation ślady
                if (window.cdc_adoQpoasnfa76pfcZLmcfl_Array) delete window.cdc_adoQpoasnfa76pfcZLmcfl_Array;
                if (window.cdc_adoQpoasnfa76pfcZLmcfl_Promise) delete window.cdc_adoQpoasnfa76pfcZLmcfl_Promise;
                if (window.cdc_adoQpoasnfa76pfcZLmcfl_Symbol) delete window.cdc_adoQpoasnfa76pfcZLmcfl_Symbol;

                // Realistyczne plugins
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [1, 2, 3, 4, 5],
                });
            """)

            logger.info("✅ Stealth patches dla ChatGPT zastosowane pomyślnie")
            return True
        except Exception as e:
            logger.error(f"❌ Błąd podczas tworzenia przeglądarki ChatGPT: {e}")
            logger.error(traceback.format_exc())
            return False

    def _random_sleep(self, min_seconds=0.2, max_seconds=0.8):
        """Losowe opóźnienie imitujące ludzkie zachowanie"""
        time.sleep(random.uniform(min_seconds, max_seconds))

    def _human_like_typing(self, element, text):
        """Symuluje ludzkie wpisywanie tekstu"""
        for char in text:
            element.send_keys(char)
            # Różne prędkości pisania
            time.sleep(random.uniform(0.01, 0.08))

            # Czasami zrób pauzę (zastanawianie się)
            if random.random() < 0.05:
                time.sleep(random.uniform(0.1, 0.3))

    def _handle_popups(self):
        """Obsługuje wyskakujące okna - AGRESYWNA WERSJA"""

        # Najpierw spróbuj zamknąć przez klawisz ESC (wielokrotnie)
        try:
            from selenium.webdriver.common.keys import Keys
            for _ in range(3):  # 3x ESC dla pewności
                self.driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)
                time.sleep(0.2)
            logger.info("✅ Wysłano wielokrotne ESC dla zamknięcia popup'ów")
        except:
            pass

        popup_selectors = [
            # Nowy popup GPT-5 - ROZSZERZONE SELEKTORY
            "//button[contains(@aria-label, 'Close') or contains(@class, 'close')]",
            "//div[contains(@role, 'dialog')]//button[contains(@aria-label, 'Close')]",
            "//div[contains(@class, 'modal')]//button[contains(@aria-label, 'Close')]",

            # Popup GPT-5 - przyciski tekstowe (POLSKIE I ANGIELSKIE)
            "//button[contains(text(), 'Zarejestruj się za darmo')]",
            "//button[contains(text(), 'Continue without subscribing')]",
            "//button[contains(text(), 'Maybe later')]",
            "//button[contains(text(), 'Skip')]",
            "//button[contains(text(), 'Not now')]",
            "//button[contains(text(), 'Nie teraz')]",
            "//button[contains(text(), 'Później')]",

            # Ogólne selektory popup'ów - ROZSZERZONE
            "//button[contains(@class, 'close')]",
            "//button[contains(text(), 'Accept')]",
            "//button[contains(text(), 'Continue')]",
            "//button[contains(text(), 'OK')]",
            "//button[contains(text(), 'Got it')]",
            "//button[contains(text(), 'Dismiss')]",
            "//button[contains(text(), 'No thanks')]",

            # Specyficzne selektory dla ChatGPT - WIĘCEJ OPCJI
            "//div[contains(@class, 'radix-dialog-overlay')]//button",
            "//div[contains(@data-radix-collection-item)]//button[last()]",
            "[data-testid='close-button']",
            "[aria-label*='close' i]",
            ".modal-close",
            ".dialog-close",

            # NOWE - przycisk X w prawym górnym rogu
            "//button[text()='×']",
            "//button[contains(@class, 'close') and contains(text(), '×')]",
            "//span[text()='×']/parent::button"
        ]

        popup_closed = False

        # Następnie próbuj selektorów - KAŻDY 3 RAZY
        for selector in popup_selectors:
            for attempt in range(3):  # 3 próby dla każdego selektora
                try:
                    if selector.startswith("//"):
                        elements = self.driver.find_elements(By.XPATH, selector)
                    else:
                        elements = self.driver.find_elements(By.CSS_SELECTOR, selector)

                    for element in elements:
                        if element.is_displayed() and element.is_enabled():
                            try:
                                # Sprawdź czy to nie przycisk "Zaloguj się" - tego nie chcemy klikać
                                element_text = element.text.lower() if hasattr(element, 'text') else ""
                                if "zaloguj się" in element_text and "za darmo" not in element_text:
                                    continue

                                # Przewiń do elementu
                                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
                                time.sleep(0.2)

                                element.click()
                                logger.info(f"✅ Zamknięto popup używając selektora: {selector} (próba {attempt + 1})")
                                popup_closed = True
                                self._random_sleep(0.3, 0.7)
                                return True  # Sukces - popup zamknięty
                            except Exception as e:
                                logger.debug(f"Błąd kliknięcia elementu: {e}")
                                pass
                except Exception:
                    continue

        # JavaScript fallback - BARDZO AGRESYWNY
        try:
            popup_closed_js = self.driver.execute_script("""
                function aggressivePopupCloser() {
                    let closed = false;

                    // 1. NAJPIERW - wyślij ESC do wszystkich elementów
                    const escEvent = new KeyboardEvent('keydown', {
                        key: 'Escape',
                        keyCode: 27,
                        which: 27,
                        bubbles: true
                    });
                    document.dispatchEvent(escEvent);

                    // 2. Znajdź i zamknij popup'y GPT-5 - WSZYSTKIE MOŻLIWE WARIANTY
                    const closeSelectors = [
                        'button[aria-label*="Close" i]', 
                        'button[aria-label*="close" i]',
                        'button[class*="close"]',
                        'button:contains("×")',
                        '[data-testid="close-button"]',
                        '.close',
                        '.modal-close',
                        '.dialog-close'
                    ];

                    for (const selector of closeSelectors) {
                        const buttons = document.querySelectorAll(selector);
                        for (const btn of buttons) {
                            if (btn.offsetParent !== null) {
                                try {
                                    btn.click();
                                    closed = true;
                                    console.log('Closed popup with selector:', selector);
                                } catch(e) {}
                            }
                        }
                    }

                    // 3. Znajdź modals/dialogi i WYMUŚ ich zamknięcie
                    const modalSelectors = [
                        '[role="dialog"]', 
                        '.modal', 
                        '.popup', 
                        '[class*="modal"]', 
                        '[class*="popup"]', 
                        '[class*="dialog"]',
                        '[class*="overlay"]'
                    ];

                    for (const selector of modalSelectors) {
                        const modals = document.querySelectorAll(selector);
                        for (const modal of modals) {
                            if (modal.offsetParent !== null) {
                                // Najpierw spróbuj znaleźć przycisk zamknięcia
                                const closeBtn = modal.querySelector('button[aria-label*="close" i], button[class*="close"], .close, [data-testid="close"]');
                                if (closeBtn) {
                                    try {
                                        closeBtn.click();
                                        closed = true;
                                        console.log('Closed modal via close button');
                                        continue;
                                    } catch(e) {}
                                }

                                // Jeśli nie znaleziono przycisku, UKRYJ modal
                                try {
                                    modal.style.display = 'none';
                                    modal.style.visibility = 'hidden';
                                    modal.style.opacity = '0';
                                    modal.style.zIndex = '-9999';
                                    modal.remove(); // USUŃ z DOM
                                    closed = true;
                                    console.log('Forcefully removed modal');
                                } catch(e) {}
                            }
                        }
                    }

                    // 4. Szukaj przycisków z tekstem (POLSKIE I ANGIELSKIE)
                    const buttonTexts = [
                        'continue', 'skip', 'maybe later', 'za darmo', 'nie teraz', 'później',
                        'dismiss', 'close', 'cancel', 'anuluj', 'zamknij'
                    ];

                    const allButtons = document.querySelectorAll('button');
                    for (const btn of allButtons) {
                        if (btn.offsetParent !== null) {
                            const text = btn.textContent.toLowerCase();
                            for (const buttonText of buttonTexts) {
                                if (text.includes(buttonText) && !text.includes('zaloguj się')) {
                                    try {
                                        btn.click();
                                        closed = true;
                                        console.log('Clicked button with text:', text);
                                        break;
                                    } catch(e) {}
                                }
                            }
                        }
                    }

                    // 5. OSTATECZNOŚĆ - usuń wszystkie overlay'e z wysokim z-index
                    const allElements = document.querySelectorAll('*');
                    for (const el of allElements) {
                        const style = window.getComputedStyle(el);
                        if ((style.position === 'fixed' || style.position === 'absolute') && 
                            parseInt(style.zIndex) > 1000) {
                            try {
                                el.style.display = 'none';
                                el.remove();
                                closed = true;
                                console.log('Removed high z-index overlay');
                            } catch(e) {}
                        }
                    }

                    return closed ? 'Successfully closed popups' : null;
                }

                return aggressivePopupCloser();
            """)

            if popup_closed_js:
                logger.info(f"✅ {popup_closed_js}")
                popup_closed = True
                self._random_sleep(0.5, 1.0)

        except Exception as e:
            logger.warning(f"⚠️ Błąd podczas JavaScript popup closer: {e}")

        # DODATKOWY FALLBACK - kliknij poza popup'em
        if not popup_closed:
            try:
                # Kliknij w środek strony, żeby zamknąć popup'y
                self.driver.execute_script(
                    "document.elementFromPoint(window.innerWidth/2, window.innerHeight/2).click();")
                logger.info("✅ Kliknięto w środek strony dla zamknięcia popup'ów")
                time.sleep(0.5)
            except:
                pass

        return popup_closed

    def _find_input_field(self):
        """Znajduje pole wprowadzania tekstu"""
        # Najpierw sprawdź popup'y
        self._handle_popups()

        for selector in self.INPUT_FIELD_SELECTORS:
            try:
                if selector.startswith("//"):
                    input_field = WebDriverWait(self.driver, 10).until(
                        EC.element_to_be_clickable((By.XPATH, selector))
                    )
                else:
                    input_field = WebDriverWait(self.driver, 10).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                    )
                logger.info(f"✅ Znaleziono pole tekstowe ChatGPT używając selektora: {selector}")
                return input_field
            except:
                continue

        # Jeśli nie znaleziono standardowymi selektorami, użyj JavaScript
        try:
            logger.info("⚠️ Standardowe selektory nie zadziałały, próbuję JavaScript...")
            # Najpierw sprawdź popup'y ponownie
            self._handle_popups()

            input_field = self.driver.execute_script("""
                // Znajdź pole tekstowe na różne sposoby
                let textareas = document.querySelectorAll('textarea');
                for (let textarea of textareas) {
                    if (textarea.offsetParent !== null && 
                        (textarea.placeholder.toLowerCase().includes('message') || 
                         textarea.placeholder.toLowerCase().includes('send') ||
                         textarea.id.includes('prompt'))) {
                        return textarea;
                    }
                }

                // Szukaj contenteditable div
                let editables = document.querySelectorAll('[contenteditable="true"]');
                for (let editable of editables) {
                    if (editable.offsetParent !== null && 
                        editable.getAttribute('data-testid') !== null) {
                        return editable;
                    }
                }

                // Ostatnia szansa - weź pierwszą widoczną textarea
                for (let textarea of textareas) {
                    if (textarea.offsetParent !== null) {
                        return textarea;
                    }
                }

                return null;
            """)

            if input_field:
                logger.info("✅ Znaleziono pole tekstowe przez JavaScript")
                return input_field

        except Exception as e:
            logger.error(f"❌ Błąd podczas wyszukiwania pola tekstowego przez JavaScript: {e}")

        return None

    def _wait_for_response(self, timeout=60):
        """Czeka na odpowiedź od ChatGPT"""
        start_time = time.time()

        # Czekaj na zniknięcie wskaźników ładowania
        while time.time() - start_time < timeout:
            loading_indicators_found = False

            # Sprawdź wskaźniki ładowania
            for selector in self.RESPONSE_LOADING_SELECTORS:
                try:
                    if selector.startswith("//"):
                        elements = self.driver.find_elements(By.XPATH, selector)
                    else:
                        elements = self.driver.find_elements(By.CSS_SELECTOR, selector)

                    if elements and any(el.is_displayed() for el in elements):
                        loading_indicators_found = True
                        break
                except:
                    continue

            if not loading_indicators_found:
                # Daj dodatkowy czas na stabilizację odpowiedzi
                self._random_sleep(1.5, 2.0)
                return True

            self._random_sleep(0.5, 0.7)

        return False

    def _read_response(self):
        """Odczytuje odpowiedź z ChatGPT - POPRAWIONA WERSJA"""
        response_text = ""

        # Dodatkowy czas na załadowanie odpowiedzi
        self._random_sleep(2.0, 3.0)

        # Wykonaj zrzut ekranu dla debugowania
        try:
            self.driver.save_screenshot("chatgpt_response.png")
            logger.info(f"✅ Zapisano zrzut ekranu odpowiedzi: chatgpt_response.png")
        except:
            pass

        # Sprawdź różne selektory odpowiedzi
        for selector in self.RESPONSE_SELECTORS:
            try:
                if selector.startswith("//"):
                    elements = self.driver.find_elements(By.XPATH, selector)
                else:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)

                # Szukaj elementów z tekstem
                for element in elements:
                    if element.is_displayed():
                        text = element.text.strip()
                        if text and len(text) > 1:  # Zredukowano minimalną długość
                            logger.info(f"✅ Znaleziono odpowiedź używając selektora: {selector}")
                            logger.info(f"✅ Surowa odpowiedź: '{text}'")
                            response_text = text
                            break

                if response_text:
                    break
            except Exception as e:
                logger.debug(f"Błąd przy selektorze {selector}: {e}")
                continue

        # WAŻNE: Sprawdzenie czy nie wyciągnęliśmy zapytania zamiast odpowiedzi
        if response_text and ("znajduje się na tym obrazie" in response_text or "rozpoznanym tekst" in response_text):
            logger.warning(f"⚠️ Wykryto tekst zapytania zamiast odpowiedzi: '{response_text}'")
            # Spróbuj alternatywną metodę przez JavaScript
            try:
                response_text = self.driver.execute_script("""
                    // Szukaj odpowiedzi asystenta
                    const assistantMessages = document.querySelectorAll('[data-message-author-role="assistant"]');
                    if (assistantMessages.length > 0) {
                        // Znajdź ostatnią odpowiedź
                        const lastMessage = assistantMessages[assistantMessages.length - 1];
                        // Wyciągnij sam tekst z odpowiedzi
                        return lastMessage.textContent.trim();
                    }
                    return "";
                """)
                logger.info(f"✅ Odpowiedź znaleziona przez JavaScript: '{response_text}'")
            except Exception as e:
                logger.error(f"❌ Błąd podczas próby pobrania odpowiedzi przez JavaScript: {e}")

        # Jeśli odpowiedź wciąż zawiera tekst zapytania, zwróć pustą odpowiedź
        if response_text and ("znajduje się na tym obrazie" in response_text or "rozpoznanym tekst" in response_text):
            logger.warning("⚠️ Wciąż wykryto tekst zapytania - zwracam pustą odpowiedź")
            return ""

        # Wyodrębnij tylko tekst CAPTCHA z odpowiedzi
        if response_text:
            # Wyczyść odpowiedź
            # Usuń typowe frazy wstępu
            captcha_prefixes = [
                "Na obrazku znajduje się tekst:",
                "Tekst na obrazku:",
                "Rozpoznany tekst:",
                "Tekst z CAPTCHA:",
                "CAPTCHA:",
                "Na obrazku widać:",
                "Widzę tekst:",
                "Tekst to:",
                "Na obrazku jest:"
            ]

            # Spróbuj usunąć prefiksy
            cleaned_text = response_text
            for prefix in captcha_prefixes:
                if prefix.lower() in response_text.lower():
                    parts = response_text.lower().split(prefix.lower(), 1)
                    if len(parts) > 1:
                        cleaned_text = parts[1].strip()
                        break

            # Filtruj odpowiedź, aby wyodrębnić tekst CAPTCHA
            # Usuń niepotrzebne znaki
            cleaned_text = cleaned_text.replace('"', '').replace("'", '').strip()

            # Usuń tekst przed pierwszym cudzysłowiem i po ostatnim (jeśli są)
            if '"' in cleaned_text:
                cleaned_text = cleaned_text.split('"')[1]

            # Jeśli jest wiele linii, weź tylko pierwszą
            cleaned_text = cleaned_text.split('\n')[0].strip()

            # Dodatkowe czyszczenie - usuń wszystko po kropce, przecinku itp.
            for separator in ['.', ',', ':', ';', ' - ']:
                if separator in cleaned_text:
                    cleaned_text = cleaned_text.split(separator)[0].strip()

            # Walidacja - jeśli tekst jest zbyt długi, weź tylko pierwsze kilka znaków
            # Typowe kody CAPTCHA mają 4-8 znaków
            if len(cleaned_text) > 15:
                # Szukaj krótszego ciągu znaków jako CAPTCHA (często są cyfry/litery w cudzysłowie)
                import re
                captcha_patterns = [
                    r'"([A-Za-z0-9]+)"',  # Coś w cudzysłowie
                    r'\'([A-Za-z0-9]+)\'',  # Coś w apostrofach
                    r'[\s:]([A-Za-z0-9]{4,8})[\s\.]',  # 4-8 znaków alfanumerycznych
                    r'([A-Z0-9]{4,8})'  # 4-8 znaków wielkich liter/cyfr
                ]

                for pattern in captcha_patterns:
                    matches = re.findall(pattern, response_text)
                    if matches:
                        cleaned_text = matches[0]
                        logger.info(f"✅ Znaleziono wzorzec CAPTCHA: '{cleaned_text}'")
                        break

                # Jeśli wciąż zbyt długi, ogranicz
                if len(cleaned_text) > 15:
                    # Ostateczna próba - weź tylko alfanumeryczne znaki
                    alpha_numeric = ''.join(c for c in cleaned_text if c.isalnum())
                    if 4 <= len(alpha_numeric) <= 10:
                        cleaned_text = alpha_numeric
                    else:
                        # Ostateczne rozwiązanie - ograniczenie długości
                        cleaned_text = cleaned_text[:8]

            logger.info(f"✅ Wyodrębniony tekst CAPTCHA: '{cleaned_text}'")
            return cleaned_text

        logger.warning("⚠️ Nie znaleziono odpowiedzi od ChatGPT")
        return ""

    def _encode_image_to_base64(self, image_path):
        """Konwertuje obraz do formatu base64"""
        try:
            with open(image_path, 'rb') as image_file:
                encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
                logger.info(f"✅ Zakodowano obraz: {image_path}")
                return encoded_string
        except Exception as e:
            logger.error(f"❌ Błąd podczas kodowania obrazu: {e}")
            return None

    def _upload_image(self, input_field, image_path):
        """Wysyła obraz do ChatGPT"""
        try:
            # Znajdź i kliknij przycisk uploadu
            upload_button = None
            upload_selectors = [
                "//button[contains(@aria-label, 'Upload')]",
                "//button[contains(@aria-label, 'Prześlij')]",
                "//button[contains(@aria-label, 'image')]",
                "//button[contains(@aria-label, 'obraz')]",
                "//button[contains(@title, 'Upload')]",
                "//button[contains(@title, 'Prześlij')]",
                "//button[contains(@class, 'upload')]",
                "//button[contains(@class, 'image')]",
                "//button[contains(@data-testid, 'file-upload')]"
            ]

            for selector in upload_selectors:
                try:
                    elements = self.driver.find_elements(By.XPATH, selector)
                    for element in elements:
                        if element.is_displayed():
                            upload_button = element
                            logger.info(f"✅ Znaleziono przycisk przesyłania obrazów: {selector}")
                            break
                    if upload_button:
                        break
                except:
                    continue

            if not upload_button:
                # Szukaj pola input[type=file]
                try:
                    file_input = self.driver.find_element(By.XPATH, "//input[@type='file']")
                    logger.info("📎 Znaleziono input typu file, używam send_keys...")
                    file_input.send_keys(os.path.abspath(image_path))
                    logger.info("✅ Przesłano obraz przez input file")
                    return True
                except:
                    pass

            if upload_button:
                # Kliknij przycisk uploadu
                logger.info("🖱️ Klikam przycisk przesyłania obrazu...")
                upload_button.click()
                self._random_sleep(0.5, 1.0)

                # Sprawdź, czy pojawił się input typu file
                try:
                    file_input = self.driver.find_element(By.XPATH, "//input[@type='file']")
                    file_input.send_keys(os.path.abspath(image_path))
                    self._random_sleep(0.5, 1.0)
                    return True
                except:
                    # Jeśli nie można znaleźć pola file, spróbuj metody Clipboard
                    logger.info("📋 Próbuję metodę schowka (clipboard API)...")

                    # Zakoduj obraz do base64
                    image_base64 = self._encode_image_to_base64(image_path)
                    if not image_base64:
                        return False

                    # Użyj JavaScript, aby skopiować obraz do schowka
                    clipboard_js = f"""
                        try {{
                            // Utwórz obiekt Blob reprezentujący obraz
                            const base64Data = "{image_base64}";
                            const byteCharacters = atob(base64Data);
                            const byteArrays = [];

                            for (let i = 0; i < byteCharacters.length; i++) {{
                                byteArrays.push(byteCharacters.charCodeAt(i));
                            }}

                            const byteArray = new Uint8Array(byteArrays);
                            const blob = new Blob([byteArray], {{type: 'image/jpeg'}});

                            // Utwórz obiekt ClipboardItem
                            const item = new ClipboardItem({{'image/jpeg': blob}});

                            // Zapisz w schowku
                            navigator.clipboard.write([item])
                                .then(() => console.log('Image copied to clipboard'))
                                .catch(err => console.error('Error copying image:', err));

                            return true;
                        }} catch (e) {{
                            console.error(e);
                            return false;
                        }}
                    """

                    success = self.driver.execute_script(clipboard_js)
                    if success:
                        logger.info("✅ Obraz skopiowany do schowka")

                        # Wklej obraz do ChatGPT
                        self._random_sleep(0.3, 0.7)
                        logger.info("📋 Wklejam obraz ze schowka (Ctrl+V)...")
                        actions = ActionChains(self.driver)
                        actions.key_down(Keys.CONTROL).send_keys('v').key_up(Keys.CONTROL).perform()
                        self._random_sleep(0.5, 1.0)
                        return True

            logger.warning("⚠️ Nie udało się przesłać obrazu automatycznie")
            return False

        except Exception as e:
            logger.error(f"❌ Błąd podczas przesyłania obrazu: {e}")
            return False

    def _send_message_with_image(self, message, image_path):
        """Wysyła wiadomość z obrazem do ChatGPT"""
        try:
            # AGRESYWNE sprawdzanie popup'ów przed rozpoczęciem
            for i in range(5):  # 5 prób zamknięcia popup'ów
                if self._handle_popups():
                    logger.info(f"✅ Zamknięto popup w próbie {i + 1}")
                time.sleep(0.5)

            # Znajdź pole wprowadzania tekstu
            input_field = self._find_input_field()
            if not input_field:
                logger.error("❌ Nie znaleziono pola wprowadzania tekstu")
                return False

            # DODATKOWE sprawdzenie popup'ów przed kliknięciem
            self._handle_popups()
            time.sleep(1.0)

            # Spróbuj kliknąć w pole tekstowe z retry
            click_success = False
            for attempt in range(3):
                try:
                    # Sprawdź popup'y przed każdą próbą kliknięcia
                    self._handle_popups()

                    # Przewiń do pola i kliknij
                    self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", input_field)
                    time.sleep(0.5)

                    input_field.click()
                    click_success = True
                    logger.info(f"✅ Kliknięto pole tekstowe w próbie {attempt + 1}")
                    break
                except Exception as e:
                    logger.warning(f"⚠️ Próba kliknięcia {attempt + 1} nie powiodła się: {e}")
                    # Agresywne zamykanie popup'ów po błędzie
                    self._handle_popups()

                    # Spróbuj zamknąć popup'y JavaScript'em
                    self.driver.execute_script("""
                        // Znajdź i ukryj wszystkie overlay'e
                        const overlays = document.querySelectorAll('[class*="overlay"], [class*="modal"], [class*="dialog"], [style*="position: fixed"]');
                        overlays.forEach(overlay => {
                            if (overlay.style.zIndex > 1000) {
                                overlay.style.display = 'none';
                            }
                        });

                        // Naciśnij ESC
                        document.body.dispatchEvent(new KeyboardEvent('keydown', {key: 'Escape'}));
                    """)
                    time.sleep(1.0)

                    if attempt == 2:
                        logger.error("❌ Nie udało się kliknąć w pole tekstowe po 3 próbach")
                        return False

            if not click_success:
                return False

            self._random_sleep(0.3, 0.5)

            # Sprawdź popup'y po kliknięciu w pole
            self._handle_popups()

            # Prześlij obraz
            if not self._upload_image(input_field, image_path):
                logger.error(f"❌ Nie udało się przesłać obrazu: {image_path}")
                return False

            # Daj czas na przetworzenie obrazu i sprawdź popup'y
            self._random_sleep(1.0, 2.0)
            self._handle_popups()

            # Wpisz pytanie
            self._human_like_typing(input_field, message)

            # Poczekaj chwilę przed naciśnięciem Enter
            self._random_sleep(0.3, 0.7)

            # Naciśnij Enter
            logger.info("⏎ Naciskam Enter...")
            input_field.send_keys(Keys.RETURN)

            # Sprawdź popup'y po wysłaniu wiadomości
            self._random_sleep(1.0, 1.5)
            self._handle_popups()

            # Czekaj na odpowiedź
            if not self._wait_for_response(self.timeout):
                logger.warning(f"⚠️ Timeout podczas oczekiwania na odpowiedź")
                return False

            # Sprawdź popup'y przed odczytaniem odpowiedzi
            self._handle_popups()

            # Odczytaj odpowiedź
            response = self._read_response()
            if not response:
                logger.warning("⚠️ Nie otrzymano odpowiedzi od ChatGPT")
                return False

            logger.info(f"✅ Otrzymano odpowiedź: '{response}'")
            return response

        except Exception as e:
            logger.error(f"❌ Błąd podczas wysyłania wiadomości: {e}")
            return False

    def solve_captcha(self, captcha_image_path):
        """
        Rozwiązuje CAPTCHA używając ChatGPT

        Args:
            captcha_image_path: Ścieżka do obrazu CAPTCHA

        Returns:
            str: Rozwiązany tekst CAPTCHA lub None w przypadku błędu
        """
        logger.info("🧩 Rozpoczynam rozwiązywanie CAPTCHA przez ChatGPT...")

        if not os.path.exists(captcha_image_path):
            logger.error(f"❌ Plik obrazu CAPTCHA nie istnieje: {captcha_image_path}")
            return None

        try:
            # Zawsze inicjuj nową instancję przeglądarki dla każdego rozwiązania CAPTCHA
            if self.driver:
                try:
                    self.driver.quit()
                except:
                    pass
                self.driver = None

            # Utwórz nową przeglądarkę
            if not self._setup_browser():
                logger.error("❌ Nie udało się utworzyć przeglądarki. Kończę.")
                return None

            # Otwórz ChatGPT
            logger.info("🌐 Otwieram ChatGPT...")
            if self.driver is not None:
                self.driver.get(self.chatgpt_url)
            else:
                logger.error("❌ Driver jest None - nie można otworzyć ChatGPT")
                return None

            self._random_sleep(5.0, 7.0)  # Dłuższy czas na załadowanie strony

            # AGRESYWNA obsługa popup'ów na początku
            logger.info("🔥 Agresywna obsługa popup'ów na starcie...")
            for i in range(10):  # 10 prób zamknięcia popup'ów!
                popup_closed = self._handle_popups()
                if popup_closed:
                    logger.info(f"✅ Zamknięto popup w próbie {i + 1}")
                time.sleep(0.5)

            # Dodatkowe sprawdzenie popup'ów po załadowaniu
            self._random_sleep(2.0, 3.0)
            self._handle_popups()

            # Sformułuj zapytanie do rozpoznania CAPTCHA - bardziej precyzyjne zapytanie
            prompt = "bez żadnych dodatkowych komentarzy tekst odpowiedni musi być w cudzysłowach oraz sam tekst na zdjęciu liczy 6 znaków."

            # Wyślij obraz i zapytanie do ChatGPT
            logger.info(f"📤 Wysyłam obraz CAPTCHA do ChatGPT: {captcha_image_path}")
            captcha_text = self._send_message_with_image(prompt, captcha_image_path)

            if captcha_text:
                # Oczyść rozpoznany tekst
                captcha_text = captcha_text.strip()

                # Usuń wszystkie białe znaki
                captcha_text = ''.join(captcha_text.split())

                # Zastosuj dodatkowe filtry
                # Usuń wszystkie nieistotne znaki
                captcha_text = ''.join(c for c in captcha_text if c.isalnum() or c in '-_+!?=')

                logger.info(f"✅ Rozpoznany tekst CAPTCHA: '{captcha_text}'")
                return captcha_text
            else:
                logger.error("❌ Nie udało się rozpoznać tekstu CAPTCHA")
                # Spróbuj zrobić zrzut ekranu dla późniejszej analizy
                try:
                    if self.driver is not None:
                        self.driver.save_screenshot("chatgpt_response.png")
                        logger.info(f"✅ Zapisano zrzut ekranu odpowiedzi: chatgpt_response.png")
                except Exception as e:
                    logger.error(f"❌ Błąd podczas zapisywania zrzutu ekranu: {e}")
                    pass

                # W przypadku błędu, poproś użytkownika o ręczne wprowadzenie
                print("\nNie udało się automatycznie rozpoznać CAPTCHA. Sprawdź obraz:")
                print(f"Ścieżka do obrazu: {os.path.abspath(captcha_image_path)}")
                manual_captcha = input("Proszę wprowadź kod CAPTCHA ręcznie: ")
                if manual_captcha:
                    return manual_captcha.strip()
                return None

        except Exception as e:
            logger.error(f"❌ Błąd podczas rozwiązywania CAPTCHA: {e}")
            logger.error(traceback.format_exc())
            return None
        finally:
            # Zamknij przeglądarkę po użyciu
            if self.driver:
                try:
                    self.driver.quit()
                    logger.info("✅ Przeglądarka ChatGPT zamknięta")
                except:
                    pass
                self.driver = None


# Funkcja pomocnicza do łatwego użycia solvera
def solve_captcha_with_chatgpt(captcha_image_path, headless=False, timeout=60):
    """
    Funkcja pomocnicza do łatwego rozwiązywania CAPTCHA przez ChatGPT

    Args:
        captcha_image_path: Ścieżka do obrazu CAPTCHA
        headless: Czy uruchomić przeglądarkę w trybie headless (domyślnie False)
        timeout: Maksymalny czas oczekiwania na odpowiedź

    Returns:
        str: Rozwiązany tekst CAPTCHA lub None w przypadku błędu
    """
    # Zawsze tworzy nową instancję solvera
    solver = ChatGPTCaptchaSolver(headless=headless, timeout=timeout)
    try:
        return solver.solve_captcha(captcha_image_path)
    finally:
        # Upewnij się, że przeglądarka jest zamknięta
        if solver.driver:
            try:
                solver.driver.quit()
            except:
                pass


# Przykład użycia
if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        captcha_path = sys.argv[1]
        print(f"Rozpoznaję CAPTCHA z pliku: {captcha_path}")
        result = solve_captcha_with_chatgpt(captcha_path, headless=False)
        print(f"Wynik: {result}")
    else:
        print("Podaj ścieżkę do pliku CAPTCHA jako argument")