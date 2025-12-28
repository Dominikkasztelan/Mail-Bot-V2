import traceback
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

# Importuj logger z odpowiedniego modułu (zostanie stworzony później)
from src.logger_config import get_logger
logger = get_logger(__name__)

def create_stealth_browser():
    """Tworzy i konfiguruje przeglądarkę Chrome z trybem stealth"""
    try:
        options = Options()
        options.add_argument("--start-maximized")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)

        # Używaj ChromeDriverManager do automatycznego pobierania odpowiedniej wersji ChromeDriver
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)

        # Dodatkowe stealth patches
        driver.execute_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        )

        logger.info("✅ Chrome driver created successfully")
        logger.info("✅ Stealth patches applied successfully")
        logger.info("✅ Stealth browser setup complete")

        return driver
    except Exception as e:
        logger.error(f"❌ Error creating browser: {e}")
        logger.error(traceback.format_exc())
        raise