import time
import traceback
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Importuj funkcje z innych modułów
from src.user_actions import natural_click
from src.debug_utils import debug_page_elements
from src.logger_config import get_logger

logger = get_logger(__name__)

def handle_gdpr_screen(driver, timeout=20):
    """Obsługuje ekran zgody GDPR"""
    logger.info("🍪 Obsługiwanie ekranu zgody GDPR...")
    try:
        logger.info("🔍 Szukam przycisku 'PRZEJDŹ DO SERWISU'...")

        # Debugowanie elementów strony
        debug_page_elements(driver)

        # Elastyczne wyszukiwanie przycisku GDPR przy użyciu wielu strategii
        gdpr_button = None

        # Strategia 1: Tekst przycisku
        try:
            gdpr_button = WebDriverWait(driver, timeout).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'PRZEJDŹ DO SERWISU')]"))
            )
            logger.info("✅ Znaleziono element używając tekstu przycisku")
        except:
            pass

        # Strategia 2: Klasa przycisku
        if not gdpr_button:
            try:
                gdpr_button = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(@class, 'rodo-popup-main-agree')]"))
                )
                logger.info(
                    "✅ Znaleziono element używając selektora: //button[contains(@class, 'rodo-popup-main-agree')]")
            except:
                pass

        # Strategia 3: Atrybut aria-label
        if not gdpr_button:
            try:
                gdpr_button = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[@aria-label='Zgoda']"))
                )
                logger.info("✅ Znaleziono element używając aria-label")
            except:
                pass

        # Strategia 4: Sprawdź w iframe, jeśli istnieje
        if not gdpr_button:
            iframes = driver.find_elements(By.TAG_NAME, "iframe")
            for iframe in iframes:
                try:
                    iframe_src = iframe.get_attribute("src")
                    if "rodo" in str(iframe_src).lower():
                        logger.info(f"🔍 Przełączam się do iframe GDPR: {iframe_src}")
                        driver.switch_to.frame(iframe)
                        gdpr_button = WebDriverWait(driver, 5).until(
                            EC.element_to_be_clickable((By.XPATH,
                                                        "//button[contains(text(), 'PRZEJDŹ DO SERWISU') or contains(@class, 'rodo-popup-main-agree')]"))
                        )
                        logger.info("✅ Znaleziono przycisk GDPR w iframe")
                        break
                except:
                    driver.switch_to.default_content()
                    continue

        if gdpr_button:
            logger.info("🖱️ Moving mouse naturally to target...")
            natural_click(driver, gdpr_button)
            logger.info("✅ Kliknięto element GDPR")
            # Przełącz z powrotem do głównej zawartości, jeśli byliśmy w iframe
            driver.switch_to.default_content()
            logger.info("✅ Ekran GDPR obsłużony pomyślnie")
            return True
        else:
            logger.error("❌ Nie znaleziono przycisku GDPR")
            return False
    except Exception as e:
        logger.error(f"❌ Błąd podczas obsługi ekranu GDPR: {e}")
        logger.error(traceback.format_exc())
        return False

def check_popups(driver):
    """Sprawdza i obsługuje wyskakujące okna"""
    logger.info("🔍 Sprawdzam wyskakujące okna...")
    try:
        # Lista możliwych przycisków zamknięcia popupów
        popup_selectors = [
            "//button[contains(@class, 'close')]",
            "//div[contains(@class, 'popup')]//button",
            "//div[contains(@class, 'modal')]//button",
            "//button[contains(text(), 'Zamknij')]",
            "//button[contains(text(), 'Close')]",
            "//span[contains(@class, 'close')]",
            "//div[contains(@class, 'popup')]//span[contains(@class, 'close')]"
        ]

        popups_found = False

        for selector in popup_selectors:
            popup_buttons = driver.find_elements(By.XPATH, selector)
            for button in popup_buttons:
                if button.is_displayed():
                    try:
                        natural_click(driver, button)
                        logger.info(f"✅ Zamknięto popup używając selektora: {selector}")
                        popups_found = True
                        time.sleep(1)  # Poczekaj na zamknięcie popupu
                    except:
                        pass

        if not popups_found:
            logger.info("ℹ️ Nie wykryto żadnych wyskakujących okien")

        return True
    except Exception as e:
        logger.warning(f"⚠️ Błąd podczas sprawdzania popupów: {e}")
        return False