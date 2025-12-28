#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
captcha_handler.py - POPRAWIONA WERSJA
Obsługa CAPTCHA z uproszczoną logiką opartą na wykrywaniu tekstu "Przepisz kod z obrazka"
"""

import os
import time
import random
import traceback
import requests
from datetime import datetime
from selenium.webdriver.common.by import By

# Importuj funkcje z innych modułów
from src.user_actions import natural_click
from src.logger_config import get_logger

# Import nowego modułu do rozwiązywania CAPTCHA z ulepszoną obsługą błędów
try:
    from src.chatgpt_captcha_solver import solve_captcha_with_chatgpt

    CHATGPT_SOLVER_AVAILABLE = True
    logger = get_logger(__name__)
    logger.info("✅ ChatGPT CAPTCHA solver dostępny")
except ImportError as e:
    CHATGPT_SOLVER_AVAILABLE = False
    logger = get_logger(__name__)
    logger.warning(f"⚠️ ChatGPT CAPTCHA solver niedostępny: {e}")
except Exception as e:
    CHATGPT_SOLVER_AVAILABLE = False
    logger = get_logger(__name__)
    logger.error(f"❌ Błąd podczas importu ChatGPT solver'a: {e}")


def check_captcha_error_simple(driver):
    """
    UPROSZCZONA wersja sprawdzania błędu CAPTCHA
    Sprawdza tylko czy pojawił się tekst "Przepisz kod z obrazka"

    Returns:
        str: Tekst błędu jeśli znaleziono, None jeśli brak błędu
    """
    try:
        time.sleep(2)  # Daj czas na załadowanie komunikatu

        # GŁÓWNY WSKAŹNIK - tekst "Przepisz kod z obrazka"
        error_selectors = [
            "//text()[contains(., 'Przepisz kod z obrazka')]/..",
            "//*[contains(text(), 'Przepisz kod z obrazka')]",
            "//span[contains(text(), 'Przepisz kod z obrazka')]",
            "//div[contains(text(), 'Przepisz kod z obrazka')]",
            "//li[contains(text(), 'Przepisz kod z obrazka')]",
            "//p[contains(text(), 'Przepisz kod z obrazka')]"
        ]

        for selector in error_selectors:
            try:
                elements = driver.find_elements(By.XPATH, selector)
                for element in elements:
                    if element.is_displayed():
                        text = element.text.strip()
                        if "przepisz kod z obrazka" in text.lower():
                            # Sprawdź czy element ma kolor błędu (czerwony)
                            try:
                                color = driver.execute_script(
                                    "return window.getComputedStyle(arguments[0]).color;",
                                    element
                                )
                                logger.info(f"❌ Znaleziono błąd CAPTCHA: '{text}' (kolor: {color})")
                            except:
                                logger.info(f"❌ Znaleziono błąd CAPTCHA: '{text}'")
                            return text

            except Exception as e:
                logger.debug(f"Błąd przy selektorze {selector}: {e}")
                continue

        # Sprawdź przez JavaScript - bardziej niezawodne
        error_found = driver.execute_script("""
            function findCaptchaError() {
                const allElements = document.querySelectorAll('*');

                for (let element of allElements) {
                    if (element.offsetParent !== null) {  // Element widoczny
                        const text = element.textContent.toLowerCase().trim();

                        if (text.includes('przepisz kod z obrazka')) {
                            const style = window.getComputedStyle(element);
                            const color = style.color;

                            // Sprawdź czy to komunikat błędu (czerwony tekst)
                            const isRed = color.includes('rgb(255') || 
                                         color.includes('red') || 
                                         color.includes('#f') || 
                                         color.includes('#e') ||
                                         color.includes('#d') ||
                                         text.includes('błąd');

                            return {
                                text: element.textContent.trim(),
                                color: color,
                                isError: isRed
                            };
                        }
                    }
                }
                return null;
            }

            return findCaptchaError();
        """)

        if error_found and error_found['isError']:
            logger.info(
                f"❌ JavaScript: znaleziono błąd CAPTCHA '{error_found['text']}' (kolor: {error_found['color']})")
            return error_found['text']

        # Sprawdź kod źródłowy jako backup
        page_source = driver.page_source.lower()
        if "przepisz kod z obrazka" in page_source:
            logger.info("❌ Znaleziono 'przepisz kod z obrazka' w kodzie źródłowym")
            return "Przepisz kod z obrazka (znalezione w źródle)"

        logger.info("✅ Brak komunikatu 'Przepisz kod z obrazka' - CAPTCHA OK")
        return None

    except Exception as e:
        logger.warning(f"⚠️ Błąd podczas sprawdzania błędu CAPTCHA: {e}")
        return None


def check_form_submission_success(driver, timeout=10):
    """
    STARA funkcja - zostaje dla kompatybilności
    Sprawdza czy formularz został pomyślnie przesłany
    """
    try:
        start_time = time.time()

        while time.time() - start_time < timeout:
            current_url = driver.current_url.lower()

            # Sprawdź pozytywne wskaźniki sukcesu
            success_indicators = [
                "success", "sukces", "confirm", "potwierdz", "thank", "dziek",
                "welcome", "witaj", "complete", "finished", "utworzone"
            ]

            if any(indicator in current_url for indicator in success_indicators):
                return True, f"Sukces wykryty w URL: {current_url}"

            # Sprawdź komunikaty sukcesu na stronie
            success_selectors = [
                "//div[contains(text(), 'Gratulacje')]",
                "//div[contains(text(), 'Sukces')]",
                "//div[contains(text(), 'Konto zostało utworzone')]",
                "//div[contains(text(), 'Dziękujemy')]",
                "//div[contains(@class, 'success')]",
                "//h1[contains(text(), 'Sukces')]"
            ]

            for selector in success_selectors:
                try:
                    elements = driver.find_elements(By.XPATH, selector)
                    if elements and any(el.is_displayed() for el in elements):
                        return True, f"Sukces wykryty: {elements[0].text[:50]}"
                except:
                    continue

            # Sprawdź czy nie ma błędów - TYLKO przez naszą nową funkcję
            error_text = check_captcha_error_simple(driver)
            if error_text:
                return False, f"Błąd CAPTCHA: {error_text}"

            time.sleep(1)

        # Timeout - nie można określić statusu
        return None, "Timeout podczas sprawdzania statusu"

    except Exception as e:
        logger.error(f"❌ Błąd podczas sprawdzania sukcesu przesłania: {e}")
        return None, f"Błąd sprawdzania: {str(e)}"


def simplified_handle_captcha_and_submit(driver, max_attempts=2):
    """
    NOWA GŁÓWNA FUNKCJA - uproszczona obsługa CAPTCHA
    Oparta na prostej zasadzie: jeśli nie ma tekstu "Przepisz kod z obrazka" = sukces

    Args:
        driver: WebDriver Selenium
        max_attempts: Maksymalna liczba prób rozpoznania CAPTCHA

    Returns:
        bool: True jeśli przesłanie się powiodło (brak komunikatu błędu),
              False jeśli należy zrestartować proces
    """
    logger.info(f"🧩 Obsługa CAPTCHA (uproszczona wersja, max {max_attempts} prób)...")

    for attempt in range(1, max_attempts + 1):
        logger.info(f"Próba CAPTCHA #{attempt}/{max_attempts}...")

        try:
            # 1. Znajdź i zapisz obrazek CAPTCHA
            captcha_file_path = find_and_save_captcha(driver, max_retries=2)
            if not captcha_file_path:
                logger.warning("⚠️ Nie udało się pobrać obrazka CAPTCHA")
                if attempt < max_attempts:
                    refresh_captcha(driver)
                    time.sleep(2)
                    continue
                else:
                    logger.error("❌ Brak możliwości pobrania CAPTCHA - restart procesu")
                    return False

            # 2. Znajdź pole CAPTCHA
            captcha_field = None
            captcha_field_selectors = [
                (By.ID, "captchaIpl"),
                (By.NAME, "captchaIpl"),
                (By.XPATH,
                 "//input[contains(@class, 'account-input') and @type='text' and contains(@placeholder, 'kod')]"),
                (By.XPATH, "//input[contains(@class, 'account-input') and @type='text']"),
                (By.XPATH, "//input[@type='text' and contains(@aria-label, 'captcha')]")
            ]

            for selector_type, selector_value in captcha_field_selectors:
                try:
                    field = driver.find_element(selector_type, selector_value)
                    if field.is_displayed() and field.is_enabled():
                        captcha_field = field
                        logger.info(f"✅ Znaleziono pole CAPTCHA")
                        break
                except:
                    continue

            if not captcha_field:
                logger.error("❌ Nie znaleziono pola CAPTCHA - restart procesu")
                return False

            # 3. Wyczyść pole CAPTCHA
            clear_captcha_field(driver)
            time.sleep(random.uniform(0.5, 1.0))

            # 4. Rozpoznaj CAPTCHA
            captcha_code = None
            if CHATGPT_SOLVER_AVAILABLE and os.path.exists(captcha_file_path):
                try:
                    logger.info("🤖 Rozpoznaję CAPTCHA przez ChatGPT...")
                    captcha_code = solve_captcha_with_chatgpt(
                        captcha_file_path,
                        headless=True,
                        timeout=90
                    )

                    if captcha_code and len(captcha_code.strip()) >= 3:
                        captcha_code = captcha_code.strip()
                        # Oczyść kod z niepoządanych znaków
                        captcha_code = ''.join(c for c in captcha_code if c.isalnum())
                        logger.info(f"✅ ChatGPT rozpoznał: '{captcha_code}'")
                    else:
                        logger.warning("⚠️ ChatGPT zwrócił nieprawidłowy kod")
                        captcha_code = None

                except Exception as e:
                    logger.error(f"❌ Błąd ChatGPT solver: {e}")
                    captcha_code = None

            # Jeśli automatyczne rozpoznanie nie zadziałało, poproś użytkownika
            if not captcha_code:
                logger.info(f"👨‍💻 Wprowadź kod CAPTCHA z obrazka: {captcha_file_path}")
                try:
                    import webbrowser
                    webbrowser.open(f"file://{captcha_file_path}")
                except:
                    pass

                while True:
                    captcha_code = input("Kod CAPTCHA: ").strip()
                    if captcha_code and len(captcha_code) >= 3:
                        break
                    print("⚠️ Kod musi mieć co najmniej 3 znaki")

            # 5. Wprowadź kod CAPTCHA
            if captcha_field and captcha_code:
                try:
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", captcha_field)
                    time.sleep(0.5)
                    captcha_field.click()
                    time.sleep(0.3)

                    captcha_field.clear()
                    time.sleep(0.2)

                    # Wprowadzaj znaki jeden po drugim
                    for i, char in enumerate(captcha_code):
                        captcha_field.send_keys(char)
                        if i < len(captcha_code) - 1:
                            time.sleep(random.uniform(0.05, 0.25))

                    logger.info(f"✅ Wprowadzono kod CAPTCHA: '{captcha_code}'")

                except Exception as e:
                    logger.error(f"❌ Błąd wprowadzania CAPTCHA: {e}")
                    if attempt == max_attempts:
                        return False
                    continue

            # 6. Znajdź i kliknij przycisk submit
            submit_button = None
            submit_selectors = [
                "//button[contains(text(), 'ZAŁÓŻ DARMOWE KONTO')]",
                "//button[contains(@class, 'btn--primary')]",
                "//button[contains(@class, 'btn') and contains(@class, 'primary')]",
                "//input[@type='submit']",
                "//button[@type='submit']",
                "//form//button[last()]"
            ]

            for selector in submit_selectors:
                try:
                    button = driver.find_element(By.XPATH, selector)
                    if button and button.is_displayed() and button.is_enabled():
                        submit_button = button
                        break
                except:
                    continue

            if submit_button:
                try:
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", submit_button)
                    time.sleep(random.uniform(0.8, 1.5))

                    if natural_click(driver, submit_button):
                        logger.info("✅ Kliknięto przycisk submit")
                    else:
                        driver.execute_script("arguments[0].click();", submit_button)
                        logger.info("✅ Kliknięto przycisk submit (JavaScript)")

                    # 7. KLUCZOWE: Sprawdź czy pojawił się błąd "Przepisz kod z obrazka"
                    time.sleep(3)  # Daj czas na załadowanie odpowiedzi

                    error_message = check_captcha_error_simple(driver)

                    if error_message:
                        logger.warning(f"❌ Błąd CAPTCHA wykryty: {error_message}")

                        if attempt < max_attempts:
                            logger.info(f"🔄 Odświeżam CAPTCHA (próba {attempt + 1}/{max_attempts})")
                            if refresh_captcha(driver):
                                time.sleep(random.uniform(1, 2))
                                continue
                            else:
                                logger.error("❌ Nie udało się odświeżyć CAPTCHA")
                                return False
                        else:
                            logger.error(f"❌ Wyczerpano próby CAPTCHA ({max_attempts})")
                            return False
                    else:
                        # SUKCES! - Brak komunikatu "Przepisz kod z obrazka"
                        logger.info("🎉 SUKCES! Formularz przesłany bez błędu CAPTCHA")
                        return True

                except Exception as e:
                    logger.error(f"❌ Błąd obsługi przycisku submit: {e}")
                    if attempt == max_attempts:
                        return False
                    continue
            else:
                logger.error("❌ Nie znaleziono przycisku submit")
                return False

        except Exception as e:
            logger.error(f"❌ Błąd w próbie CAPTCHA {attempt}: {e}")
            logger.error(traceback.format_exc())

            if attempt == max_attempts:
                return False

            # Spróbuj odświeżyć CAPTCHA przed kolejną próbą
            try:
                refresh_captcha(driver)
                time.sleep(random.uniform(1, 2))
            except:
                pass

    logger.error(f"❌ Wszystkie próby CAPTCHA ({max_attempts}) zakończone niepowodzeniem")
    return False


def handle_captcha_and_submit(driver, max_attempts=2, chatgpt_timeout=90):
    """
    STARA FUNKCJA - przekierowanie do nowej implementacji
    Zostaje dla kompatybilności z istniejącym kodem
    """
    logger.info("🔄 Przekierowanie do nowej implementacji obsługi CAPTCHA...")
    return simplified_handle_captcha_and_submit(driver, max_attempts)


# Pozostałe funkcje pozostają bez zmian...

def find_and_save_captcha(driver, max_retries=3):
    """Znajduje i zapisuje obrazek CAPTCHA na dysk z mechanizmem ponownych prób"""
    logger.info("🔍 Szukam obrazka CAPTCHA...")

    for retry in range(max_retries):
        try:
            if retry > 0:
                logger.info(f"🔄 Próba {retry + 1}/{max_retries}...")
                time.sleep(random.uniform(1.0, 2.0))

            # Lista potencjalnych selektorów dla obrazka CAPTCHA
            captcha_img_selectors = [
                "//img[contains(@class, 'portal-captcha__img-image')]",
                "//img[contains(@class, 'captcha')]",
                "//div[contains(@class, 'captcha')]//img",
                "//div[contains(@class, 'portal-captcha')]//img",
                "//img[contains(@alt, 'przepisz kod z obrazka')]",
                "//img[contains(@src, 'captcha.interia.pl')]",
                "//img[contains(@src, 'captcha')]",
                "//div[contains(@class, 'captcha-container')]//img"
            ]

            captcha_img = None
            selected_selector = None

            # Próbuj różne selektory aż znajdziesz działający
            for selector in captcha_img_selectors:
                try:
                    elements = driver.find_elements(By.XPATH, selector)
                    for element in elements:
                        if element.is_displayed() and element.size['height'] > 10 and element.size['width'] > 10:
                            captcha_img = element
                            selected_selector = selector
                            logger.info(f"✅ Znaleziono obrazek CAPTCHA używając selektora: {selector}")
                            break
                    if captcha_img:
                        break
                except Exception as e:
                    logger.debug(f"Selektor {selector} nie zadziałał: {e}")
                    continue

            # Jeśli nie znaleziono obrazka, użyj JavaScript
            if not captcha_img:
                logger.info("⚠️ Nie znaleziono obrazka CAPTCHA używając selektorów XPath. Próbuję JavaScript...")
                captcha_img_src = driver.execute_script("""
                    function findCaptchaImage() {
                        // Szukaj obrazka captcha po atrybutach
                        let captchaImg = document.querySelector('img[alt*="przepisz kod" i]');
                        if (captchaImg && captchaImg.offsetParent !== null) return captchaImg.src;

                        // Szukaj po klasach
                        const classSelectors = [
                            'img.portal-captcha__img-image',
                            'img[class*="captcha"]',
                            '.captcha img',
                            '.portal-captcha img'
                        ];

                        for (const selector of classSelectors) {
                            captchaImg = document.querySelector(selector);
                            if (captchaImg && captchaImg.offsetParent !== null) return captchaImg.src;
                        }

                        // Szukaj po url obrazka
                        const images = document.querySelectorAll('img');
                        for (let img of images) {
                            if (img.src && img.offsetParent !== null) {
                                const src = img.src.toLowerCase();
                                if (src.includes('captcha') || 
                                    src.includes('verification') || 
                                    src.includes('challenge')) {
                                    return img.src;
                                }
                            }
                        }

                        // Ostatnia szansa - szukaj obrazków w kontenerach captcha
                        const captchaContainers = document.querySelectorAll('[class*="captcha"], [id*="captcha"]');
                        for (const container of captchaContainers) {
                            const img = container.querySelector('img');
                            if (img && img.offsetParent !== null && img.src) {
                                return img.src;
                            }
                        }

                        return null;
                    }

                    return findCaptchaImage();
                """)

                if captcha_img_src:
                    logger.info(f"✅ Znaleziono URL obrazka CAPTCHA przez JavaScript: {captcha_img_src}")

                    # Zapisz obrazek bezpośrednio z URL
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    captcha_filename = f"captcha_{timestamp}.jpg"

                    try:
                        headers = {
                            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                        }
                        response = requests.get(captcha_img_src, stream=True, headers=headers, timeout=10)
                        if response.status_code == 200:
                            with open(captcha_filename, 'wb') as file:
                                for chunk in response.iter_content(1024):
                                    file.write(chunk)
                            logger.info(f"✅ Zapisano obrazek CAPTCHA do pliku: {os.path.abspath(captcha_filename)}")
                            return os.path.abspath(captcha_filename)
                        else:
                            logger.error(
                                f"❌ Nie udało się pobrać obrazka CAPTCHA. Kod odpowiedzi: {response.status_code}")
                    except Exception as e:
                        logger.error(f"❌ Błąd podczas zapisywania obrazka CAPTCHA z URL: {e}")
                        continue
                else:
                    logger.warning("⚠️ Nie znaleziono URL obrazka CAPTCHA przez JavaScript")
                    continue

            # Jeśli znaleziono element obrazka, pobierz jego URL i zapisz
            if captcha_img:
                captcha_src = captcha_img.get_attribute("src")
                if captcha_src:
                    logger.info(f"✅ URL obrazka CAPTCHA: {captcha_src}")

                    # Sprawdź czy obrazek ma odpowiedni rozmiar
                    img_size = captcha_img.size
                    if img_size['height'] < 10 or img_size['width'] < 10:
                        logger.warning(f"⚠️ Obrazek CAPTCHA ma podejrzanie mały rozmiar: {img_size}")
                        continue

                    # Zapisz obrazek z lepszą obsługą błędów
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    captcha_filename = f"captcha_{timestamp}.jpg"

                    try:
                        headers = {
                            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                            'Referer': driver.current_url
                        }
                        response = requests.get(captcha_src, stream=True, headers=headers, timeout=15)
                        if response.status_code == 200:
                            with open(captcha_filename, 'wb') as file:
                                for chunk in response.iter_content(1024):
                                    file.write(chunk)

                            # Sprawdź czy plik został poprawnie zapisany
                            if os.path.exists(captcha_filename) and os.path.getsize(captcha_filename) > 100:
                                logger.info(f"✅ Zapisano obrazek CAPTCHA do pliku: {os.path.abspath(captcha_filename)}")
                                return os.path.abspath(captcha_filename)
                            else:
                                logger.warning("⚠️ Zapisany plik CAPTCHA jest pusty lub uszkodzony")
                                if os.path.exists(captcha_filename):
                                    os.remove(captcha_filename)
                                continue
                        else:
                            logger.error(
                                f"❌ Nie udało się pobrać obrazka CAPTCHA. Kod odpowiedzi: {response.status_code}")
                    except Exception as e:
                        logger.error(f"❌ Błąd podczas zapisywania obrazka CAPTCHA: {e}")
                        continue
                else:
                    logger.warning("⚠️ Nie udało się pobrać URL obrazka CAPTCHA")

            # Jeśli dotarliśmy tutaj, znaczy że ta próba się nie powiodła
            if retry < max_retries - 1:
                logger.info(f"⚠️ Próba {retry + 1} nieudana, ponawiam...")
                try:
                    refresh_captcha(driver)
                except:
                    pass
            else:
                logger.error("❌ Wszystkie próby znalezienia CAPTCHA zakończone niepowodzeniem")

        except Exception as e:
            logger.error(f"❌ Błąd podczas wyszukiwania i zapisywania obrazka CAPTCHA (próba {retry + 1}): {e}")
            if retry == max_retries - 1:
                logger.error(traceback.format_exc())

    return None


def refresh_captcha(driver, max_attempts=3):
    """Odświeża obrazek CAPTCHA z wieloma próbami"""
    logger.info("🔄 Próba odświeżenia obrazka CAPTCHA...")

    for attempt in range(max_attempts):
        try:
            if attempt > 0:
                logger.info(f"🔄 Próba odświeżenia {attempt + 1}/{max_attempts}...")
                time.sleep(random.uniform(1.0, 2.0))

            # Rozszerzone selektory dla przycisku odświeżania CAPTCHA
            refresh_selectors = [
                "//button[contains(@class, 'portal-captcha__img-refresh')]",
                "//button[contains(@class, 'portal-captcha__refresh')]",
                "//button[contains(@class, 'captcha-refresh')]",
                "//button[contains(@title, 'Odśwież')]",
                "//button[contains(@title, 'Refresh')]",
                "//div[contains(@class, 'portal-captcha')]//button",
                "//div[contains(@class, 'captcha')]//button",
                "//button[contains(@class, 'icon') and ancestor::div[contains(@class, 'captcha')]]",
                "//span[contains(@class, 'icon-refresh')]/parent::button",
                "//i[contains(@class, 'refresh')]/parent::button",
                "//button[contains(@aria-label, 'Refresh')]",
                "//button[contains(@aria-label, 'Odśwież')]",
                "//a[contains(@class, 'refresh')]",
                "//div[contains(@class, 'refresh')][@role='button']"
            ]

            refresh_button = None

            # Próbuj znaleźć przycisk odświeżania
            for selector in refresh_selectors:
                try:
                    elements = driver.find_elements(By.XPATH, selector)
                    for element in elements:
                        if element.is_displayed() and element.is_enabled():
                            element_location = element.location
                            if element_location['x'] >= 0 and element_location['y'] >= 0:
                                refresh_button = element
                                logger.info(f"✅ Znaleziono przycisk odświeżania CAPTCHA: {selector}")
                                break
                    if refresh_button:
                        break
                except Exception as e:
                    logger.debug(f"Selektor {selector} nie zadziałał: {e}")
                    continue

            # Jeśli nie znaleziono standardowego przycisku, użyj JavaScript
            if not refresh_button:
                logger.info("⚠️ Nie znaleziono przycisku odświeżania przez selektory, próbuję JavaScript...")

                refresh_clicked = driver.execute_script("""
                    function refreshCaptcha() {
                        // Szukaj przycisku odświeżania
                        const possibleSelectors = [
                            '.portal-captcha__img-refresh',
                            '.portal-captcha__refresh', 
                            '.captcha-refresh',
                            '[title*="Odśwież" i]',
                            '[title*="Refresh" i]',
                            '[aria-label*="Odśwież" i]',
                            '[aria-label*="Refresh" i]'
                        ];

                        for (const selector of possibleSelectors) {
                            const button = document.querySelector(selector);
                            if (button && button.offsetParent !== null) {
                                button.scrollIntoView({block: 'center'});
                                button.click();
                                return `Kliknięto przez selektor: ${selector}`;
                            }
                        }

                        // Alternatywna metoda
                        const captchaContainers = [
                            '.portal-captcha-container', 
                            '.captcha-container', 
                            '[class*="captcha"]',
                            '[id*="captcha"]'
                        ];

                        for (const containerSelector of captchaContainers) {
                            const captchaContainer = document.querySelector(containerSelector);
                            if (captchaContainer) {
                                const buttons = captchaContainer.querySelectorAll('button, a[role="button"], div[role="button"]');
                                for (const button of buttons) {
                                    if (button.offsetParent !== null) {
                                        const buttonText = button.textContent.toLowerCase();
                                        const buttonTitle = (button.title || '').toLowerCase();
                                        const buttonClass = button.className.toLowerCase();

                                        if (buttonTitle.includes('odśwież') || 
                                            buttonTitle.includes('refresh') ||
                                            buttonClass.includes('refresh') ||
                                            buttonText.includes('odśwież')) {
                                            button.scrollIntoView({block: 'center'});
                                            button.click();
                                            return `Kliknięto przycisk z kontekstu CAPTCHA: ${button.className}`;
                                        }
                                    }
                                }

                                // Ostatnia próba - kliknij pierwszy widoczny przycisk w kontenerze CAPTCHA
                                const firstButton = captchaContainer.querySelector('button');
                                if (firstButton && firstButton.offsetParent !== null) {
                                    firstButton.scrollIntoView({block: 'center'});
                                    firstButton.click();
                                    return `Kliknięto pierwszy przycisk w kontenerze CAPTCHA`;
                                }
                            }
                        }

                        // Jeśli wszystko zawodzi, spróbuj odświeżyć obrazek bezpośrednio
                        const captchaImages = document.querySelectorAll('img[src*="captcha"], img[class*="captcha"]');
                        for (const img of captchaImages) {
                            if (img.offsetParent !== null) {
                                const originalSrc = img.src;
                                const newSrc = originalSrc.includes('?') ? originalSrc + '&t=' + Date.now() : originalSrc + '?t=' + Date.now();
                                img.src = newSrc;
                                return `Odświeżono obrazek CAPTCHA bezpośrednio: ${newSrc}`;
                            }
                        }

                        return null;
                    }

                    return refreshCaptcha();
                """)

                if refresh_clicked:
                    logger.info(f"✅ {refresh_clicked}")
                    time.sleep(random.uniform(2.0, 3.0))
                    return True
                else:
                    logger.warning("⚠️ Nie udało się odświeżyć CAPTCHA przez JavaScript w tej próbie")
                    continue

            # Jeśli znaleziono przycisk, kliknij go
            if refresh_button:
                try:
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", refresh_button)
                    time.sleep(random.uniform(0.5, 1.0))

                    if natural_click(driver, refresh_button):
                        logger.info("✅ Kliknięto przycisk odświeżania CAPTCHA")
                        time.sleep(random.uniform(2.0, 3.0))
                        return True
                    else:
                        logger.warning("⚠️ Natural click nie powiódł się, próbuję JavaScript")
                        driver.execute_script("arguments[0].click();", refresh_button)
                        logger.info("✅ Kliknięto przycisk odświeżania przez JavaScript")
                        time.sleep(random.uniform(2.0, 3.0))
                        return True

                except Exception as e:
                    logger.warning(f"⚠️ Błąd podczas klikania przycisku odświeżania (próba {attempt + 1}): {e}")
                    continue

        except Exception as e:
            logger.error(f"❌ Błąd podczas odświeżania CAPTCHA (próba {attempt + 1}): {e}")
            continue

    logger.error(f"❌ Nie udało się odświeżyć CAPTCHA po {max_attempts} próbach")
    return False


def clear_captcha_field(driver):
    """Czyści pole CAPTCHA przed wprowadzeniem nowego kodu"""
    logger.info("🧹 Czyszczenie pola CAPTCHA...")

    try:
        # Znajdź pole CAPTCHA z rozszerzonymi selektorami
        captcha_field_selectors = [
            "//input[@id='captchaIpl']",
            "//input[@name='captchaIpl']",
            "//input[contains(@class, 'captcha')]",
            "//input[contains(@placeholder, 'kod')]",
            "//input[contains(@placeholder, 'captcha')]",
            "//input[contains(@placeholder, 'Kod z obrazka')]",
            "//input[contains(@aria-label, 'captcha')]",
            "//input[contains(@aria-label, 'kod')]"
        ]

        captcha_field = None
        for selector in captcha_field_selectors:
            try:
                elements = driver.find_elements(By.XPATH, selector)
                for element in elements:
                    if element.is_displayed() and element.is_enabled():
                        captcha_field = element
                        logger.info(f"✅ Znaleziono pole CAPTCHA: {selector}")
                        break
                if captcha_field:
                    break
            except:
                continue

        if captcha_field:
            # Wielokrotne czyszczenie pola na różne sposoby
            try:
                # Metoda 1: Standardowe clear()
                captcha_field.clear()
                time.sleep(0.1)

                # Metoda 2: Select all + delete
                captcha_field.send_keys("\ue009a")  # Ctrl+A
                time.sleep(0.1)
                captcha_field.send_keys("\ue017")  # Delete
                time.sleep(0.1)

                # Metoda 3: JavaScript
                driver.execute_script("arguments[0].value = '';", captcha_field)
                time.sleep(0.1)

                # Metoda 4: Focus i backspace wielokrotnie
                captcha_field.click()
                for _ in range(10):  # Usuń do 10 znaków
                    captcha_field.send_keys("\ue003")  # Backspace

                # Weryfikacja czy pole jest puste
                current_value = captcha_field.get_attribute("value")
                if current_value:
                    logger.warning(
                        f"⚠️ Pole CAPTCHA nie zostało całkowicie wyczyszczone. Pozostała wartość: '{current_value}'")
                    # Ostateczne czyszczenie przez JavaScript
                    driver.execute_script("""
                        arguments[0].value = '';
                        arguments[0].dispatchEvent(new Event('input', { bubbles: true }));
                        arguments[0].dispatchEvent(new Event('change', { bubbles: true }));
                    """, captcha_field)
                else:
                    logger.info("✅ Pole CAPTCHA zostało wyczyszczone")

                return True
            except Exception as e:
                logger.warning(f"⚠️ Błąd podczas czyszczenia pola CAPTCHA: {e}")
                return False
        else:
            logger.warning("⚠️ Nie znaleziono pola CAPTCHA do wyczyszczenia")
            return False

    except Exception as e:
        logger.warning(f"⚠️ Błąd podczas czyszczenia pola CAPTCHA: {e}")
        return False


# FUNKCJE TESTOWE I DEBUGOWANIA

def test_current_page_for_captcha_error(driver):
    """
    Testuje aktualną stronę pod kątem błędu CAPTCHA
    Uruchom po przesłaniu formularza z błędną CAPTCHA
    """
    print("\n" + "=" * 60)
    print("🧪 TEST WYKRYWANIA BŁĘDU CAPTCHA")
    print("=" * 60)

    # Podstawowe info
    print(f"📍 URL: {driver.current_url}")
    print(f"📄 Tytuł: {driver.title}")

    # Zapisz zrzut ekranu
    driver.save_screenshot("test_captcha_error_detection.png")
    print(f"📸 Zrzut ekranu: test_captcha_error_detection.png")

    # TEST 1: Sprawdź naszą funkcję
    print("\n🔍 TEST 1: check_captcha_error_simple()")
    error = check_captcha_error_simple(driver)
    if error:
        print(f"✅ WYKRYTO BŁĄD: '{error}'")
    else:
        print("❌ NIE WYKRYTO BŁĘDU")

    # TEST 2: Wszystkie teksty z "przepisz"
    print("\n🔍 TEST 2: Wszystkie teksty zawierające 'przepisz'")
    przepisz_texts = driver.execute_script("""
        const elements = document.querySelectorAll('*');
        const results = [];

        for (let el of elements) {
            if (el.offsetParent !== null) {  // widoczny
                const text = el.textContent.toLowerCase();
                if (text.includes('przepisz')) {
                    const style = window.getComputedStyle(el);
                    results.push({
                        text: el.textContent.trim(),
                        tag: el.tagName,
                        color: style.color,
                        background: style.backgroundColor,
                        visible: true
                    });
                }
            }
        }
        return results;
    """)

    if przepisz_texts:
        for i, item in enumerate(przepisz_texts):
            print(f"   {i + 1}. '{item['text']}' ({item['tag']}, kolor: {item['color']})")
    else:
        print("   Nie znaleziono tekstów z 'przepisz'")

    # TEST 3: Sprawdź kod strony
    print("\n🔍 TEST 3: Kod źródłowy strony")
    page_source = driver.page_source.lower()
    if "przepisz kod z obrazka" in page_source:
        print("✅ Znaleziono 'przepisz kod z obrazka' w kodzie źródłowym")
    else:
        print("❌ NIE znaleziono 'przepisz kod z obrazka' w kodzie źródłowym")

    # TEST 4: Sprawdź czy formularz nadal istnieje
    print("\n🔍 TEST 4: Stan formularza")
    captcha_field = driver.find_elements(By.ID, "captchaIpl")
    if captcha_field:
        print("📝 Pole CAPTCHA nadal istnieje")
    else:
        print("❌ Pole CAPTCHA zniknęło")

    registration_form = driver.find_elements(By.XPATH, "//input[@name='konto' or @id='konto']")
    if registration_form:
        print("📝 Formularz rejestracji nadal istnieje")
    else:
        print("❌ Formularz rejestracji zniknął")

    print("\n" + "=" * 60)
    print("🏁 KONIEC TESTU")
    print("=" * 60)

    return error is not None


def debug_captcha_detection(driver):
    """
    Funkcja debugowania do sprawdzenia wszystkich aspektów wykrywania CAPTCHA
    """
    logger.info("🔍 DEBUGOWANIE WYKRYWANIA CAPTCHA")

    # Sprawdź wszystkie możliwe sposoby wykrywania błędu
    methods = {
        "XPath selectors": check_captcha_error_simple,
        "Page source": lambda d: "przepisz kod z obrazka" in d.page_source.lower(),
        "JavaScript": lambda d: d.execute_script("""
            return document.body.textContent.toLowerCase().includes('przepisz kod z obrazka');
        """)
    }

    results = {}
    for method_name, method_func in methods.items():
        try:
            result = method_func(driver)
            results[method_name] = result
            logger.info(f"{method_name}: {result}")
        except Exception as e:
            results[method_name] = f"ERROR: {e}"
            logger.error(f"{method_name}: ERROR - {e}")

    return results

# Przykład użycia w main.py:
# if __name__ == "__main__":
#     # Po przesłaniu formularza z błędną CAPTCHA:
#     test_current_page_for_captcha_error(driver)