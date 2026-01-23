# tests/conftest.py
import sys
from pathlib import Path

# 1. Dodajemy katalog główny projektu do ścieżki Pythona
# Dzięki temu w testach możemy robić "from src.identity_manager import ..."
# Rozwiązuje problem "ModuleNotFoundError"
ROOT_DIR = Path(__file__).parent.parent
sys.path.append(str(ROOT_DIR))

# 2. Tutaj w przyszłości możemy dodać globalne mocki
# np. żeby żaden test przypadkiem nie wysłał requestu do prawdziwego API, jeśli zapomnimy go zmockować

import pytest
from src.logger_config import get_logger

logger = get_logger("TestRunner")

@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    # Execute all other hooks to obtain the report object
    outcome = yield
    rep = outcome.get_result()

    # Check if test failed
    if rep.when == "call" and rep.failed:
        logger.error(f"❌ Test failed: {item.name}")
        
        # Try to retrieve 'page' fixture from the test item
        page = item.funcargs.get("page")
        if page:
            try:
                screenshot_path = f"logs/fail_{item.name}.png"
                page.screenshot(path=screenshot_path, full_page=True)
                logger.info(f"📸 Screenshot saved to {screenshot_path}")
            except Exception as e:
                logger.warning(f"Failed to take screenshot: {e}")

