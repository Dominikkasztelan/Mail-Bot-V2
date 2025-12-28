import time
import random
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys

# Importuj logger z odpowiedniego modułu
from src.logger_config import get_logger
logger = get_logger(__name__)

def natural_click(driver, element, max_attempts=3):
    """Wykonuje naturalne kliknięcie na element z losowym opóźnieniem"""
    for attempt in range(1, max_attempts + 1):
        try:
            # Symulacja losowego opóźnienia ludzkiego
            time.sleep(random.uniform(0.3, 1.0))

            # Płynne przesunięcie myszy do elementu
            actions = ActionChains(driver)
            actions.move_to_element(element)

            # Dodaj losowe mikroruchy dla większego realizmu
            offset_x = random.randint(-3, 3)
            offset_y = random.randint(-3, 3)
            actions.move_by_offset(offset_x, offset_y)

            # Wykonaj kliknięcie
            actions.click()
            actions.perform()

            logger.info(f"✅ Natural click successful on attempt {attempt}")
            return True
        except Exception as e:
            if attempt == max_attempts:
                logger.error(f"❌ Failed to click element after {max_attempts} attempts: {e}")
                return False
            logger.warning(f"⚠️ Click attempt {attempt} failed, retrying...")
            time.sleep(random.uniform(1.0, 2.0))

def click_username_field(driver, max_attempts=3):
    """Kliknij w pole 'Nazwa konta' w sposób naśladujący naturalnego użytkownika"""
    logger.info("🖱️ Próba kliknięcia w pole 'Nazwa konta'...")

    for attempt in range(1, max_attempts + 1):
        try:
            # Lista potencjalnych selektorów dla pola "Nazwa konta"
            selectors = [
                (By.ID, "konto"),
                (By.NAME, "konto"),
                (By.CSS_SELECTOR, "input[name='login-fake']"),
                (By.CSS_SELECTOR, "input._2E5nlbjiri2rnh[type='text']"),
                (By.XPATH, "//input[contains(@class, '_2E5nlbjiri2rnh')][@type='text']"),
                (By.XPATH, "//label[contains(text(), 'Nazwa konta')]/following-sibling::input"),
                (By.XPATH, "//div[contains(@class, 'account-input')]/input[contains(@class, 'input--fake')]"),
                (By.CSS_SELECTOR, "input[name='login']"),
                (By.CSS_SELECTOR, "input[id='konto']"),
                (By.XPATH, "//input[@name='konto']")
            ]

            # Próbuj różne selektory aż znajdziesz działający
            username_field = None
            for selector_type, selector_value in selectors:
                try:
                    element = WebDriverWait(driver, 3).until(
                        EC.presence_of_element_located((selector_type, selector_value))
                    )
                    if element.is_displayed():
                        username_field = element
                        logger.info(f"✅ Znaleziono pole 'Nazwa konta' używając: {selector_type}={selector_value}")
                        break
                except:
                    continue

            # Jeśli wszystkie selektory zawodzą, spróbuj użyć JavaScriptu
            if not username_field:
                logger.info("⚠️ Standardowe metody nie zadziałały, próbuję przez JavaScript...")
                username_field = driver.execute_script("""
                    // Znajdź pola z odpowiednimi atrybutami
                    let inputs = document.querySelectorAll("input[type='text']");

                    // Szukaj po tekście etykiety
                    for (let input of inputs) {
                        let label = document.querySelector(`label[for='${input.id}']`);
                        if (label && label.textContent.includes('Nazwa konta')) {
                            return input;
                        }
                    }

                    // Szukaj po sąsiadujących elementach
                    for (let input of inputs) {
                        let parent = input.parentElement;
                        if (parent.textContent.includes('Nazwa konta')) {
                            return input;
                        }
                    }

                    // Jeśli nie znaleziono dokładnie, spróbuj znaleźć input z odpowiednim placeholderem
                    for (let input of inputs) {
                        if (input.placeholder && input.placeholder.toLowerCase().includes('nazwa konta')) {
                            return input;
                        }
                    }

                    // Zwróć input z klasy widocznej na zrzucie ekranu
                    const specificInput = document.querySelector("input._2E5nlbjiri2rnh[type='text']");
                    if (specificInput) return specificInput;

                    // Zwróć pierwszy input typu text jako ostateczność
                    return inputs.length > 0 ? inputs[0] : null;
                """)

                if username_field:
                    logger.info("✅ Znaleziono pole 'Nazwa konta' przez JavaScript")

            # Jeśli nie znaleziono pola, zwróć błąd
            if not username_field:
                logger.error("❌ Nie udało się znaleźć pola 'Nazwa konta' w próbie " + str(attempt))
                if attempt == max_attempts:
                    return False
                time.sleep(random.uniform(1.0, 2.0))
                continue

            # Przewiń do elementu
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", username_field)
            time.sleep(random.uniform(0.5, 1.0))

            # Wykonaj naturalne kliknięcie
            if natural_click(driver, username_field):
                logger.info("✅ Kliknięto pole 'Nazwa konta' w sposób naśladujący naturalnego użytkownika")

                # Symulacja skupienia na polu - migający kursor
                time.sleep(random.uniform(0.3, 0.7))

                # Dodatkowa weryfikacja czy pole jest aktywne
                active_element = driver.switch_to.active_element
                if active_element == username_field:
                    logger.info("✅ Pole 'Nazwa konta' jest aktywne")

                return True
            else:
                logger.warning(f"⚠️ Próba kliknięcia {attempt} nie powiodła się, ponawiam...")
                time.sleep(random.uniform(1.0, 2.0))

        except Exception as e:
            logger.warning(f"⚠️ Błąd podczas próby kliknięcia w pole 'Nazwa konta': {e}")
            if attempt == max_attempts:
                logger.error(f"❌ Nie udało się kliknąć w pole 'Nazwa konta' po {max_attempts} próbach")
                return False
            time.sleep(random.uniform(1.0, 2.0))

    return False

def browse_naturally(driver):
    """Symuluje naturalne przeglądanie strony"""
    logger.info("👀 Naturally browsing the page...")
    try:
        # Symuluj naturalne przewijanie strony
        scroll_heights = [300, 500, 800, 500, 200]
        for height in scroll_heights:
            driver.execute_script(f"window.scrollTo(0, {height});")
            time.sleep(random.uniform(0.5, 1.5))

        return True
    except Exception as e:
        logger.warning(f"⚠️ Błąd podczas naturalnego przeglądania strony: {e}")
        return False

def apply_space_delete_trick(driver, element):
    """
    Aplikuje trik z dodaniem spacji i jej usunięciem aby ominąć mechanizm anty-botowy
    """
    try:
        logger.info("🔑 Stosowanie triku ze spacją dla omijania mechanizmu anty-botowego...")

        # Upewnij się, że element jest widoczny
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
        time.sleep(random.uniform(0.3, 0.7))

        # Kliknij w element, aby uzyskać fokus
        actions = ActionChains(driver)
        actions.move_to_element(element).click().perform()
        time.sleep(random.uniform(0.3, 0.7))

        # Dodaj spację
        actions = ActionChains(driver)
        actions.send_keys(Keys.SPACE)
        actions.perform()
        time.sleep(random.uniform(0.3, 0.7))

        # Usuń spację
        actions = ActionChains(driver)
        actions.send_keys(Keys.BACKSPACE)
        actions.perform()
        time.sleep(random.uniform(0.3, 0.7))

        logger.info("✅ Trik ze spacją pomyślnie zastosowany")
        return True
    except Exception as e:
        logger.error(f"❌ Błąd podczas stosowania triku ze spacją: {e}")
        return False

def wait_for_element(driver, by, value, timeout=10, clickable=False):
    """Czeka na pojawienie się elementu z obsługą błędów"""
    try:
        if clickable:
            return WebDriverWait(driver, timeout).until(
                EC.element_to_be_clickable((by, value))
            )
        else:
            return WebDriverWait(driver, timeout).until(
                EC.presence_of_element_located((by, value))
            )
    except TimeoutException:
        logger.warning(f"⚠️ Timeout podczas oczekiwania na element: {by}={value}")
        return None
    except Exception as e:
        logger.warning(f"⚠️ Błąd podczas oczekiwania na element: {by}={value}, {e}")
        return None

def find_element_with_multiple_strategies(driver, strategies, timeout=5):
    """Znajduje element używając wielu strategii wyszukiwania"""
    for strategy in strategies:
        by, value = strategy
        element = wait_for_element(driver, by, value, timeout)
        if element:
            logger.info(f"✅ Znaleziono element używając: {by}={value}")
            return element
    return None