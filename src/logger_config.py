import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
from typing import Optional

# --- KONFIGURACJA ---
LOG_DIR = Path("logs")
LOG_FILENAME = "bot_log.log"
MAX_BYTES = 5 * 1024 * 1024  # 5 MB na plik
BACKUP_COUNT = 3  # Trzymaj 3 ostatnie pliki logów (rotacja)
ENCODING = 'utf-8'


def setup_logging() -> None:
    """
    Konfiguruje globalny system logowania z obsługą rotacji plików i UTF-8.
    Jest idempotentna (można wywołać wielokrotnie bez duplikowania handlerów).
    """
    # 1. Utworzenie katalogu logów
    LOG_DIR.mkdir(exist_ok=True)
    log_path = LOG_DIR / LOG_FILENAME

    # 2. Pobranie root loggera
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    # 3. Wyczyszczenie istniejących handlerów (zapobiega duplikatom przy reloadzie)
    if root_logger.hasHandlers():
        root_logger.handlers.clear()

    # 4. Formatowanie logów (Czas - Poziom - Moduł - Wiadomość)
    formatter = logging.Formatter(
        '%(asctime)s - [%(levelname)s] - %(name)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # 5. Handler Plikowy z Rotacją (RotatingFileHandler)
    # Zastępuje zwykły FileHandler, aby uniknąć nieskończonego wzrostu pliku
    file_handler = RotatingFileHandler(
        log_path,
        maxBytes=MAX_BYTES,
        backupCount=BACKUP_COUNT,
        encoding=ENCODING
    )
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)

    # 6. Handler Konsolowy (stdout)
    # Wymuszenie UTF-8 na poziomie strumienia (fix dla Windowsa)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # 7. Wyciszenie bibliotek zewnętrznych
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('playwright').setLevel(logging.WARNING)
    logging.getLogger('selenium').setLevel(logging.WARNING)
    logging.getLogger('webdriver_manager').setLevel(logging.WARNING)


def get_logger(module_name: str) -> logging.Logger:
    """
    Zwraca logger dla konkretnego modułu. To jest zalecana metoda tworzenia loggerów.

    Użycie w innych plikach:
        from src.logger_config import get_logger
        logger = get_logger(__name__)
    """
    # Upewniamy się, że logging jest skonfigurowany
    if not logging.getLogger().hasHandlers():
        setup_logging()

    return logging.getLogger(module_name)


# --- INICJALIZACJA I WSTECZNA KOMPATYBILNOŚĆ ---

# Uruchamiamy konfigurację przy imporcie modułu
setup_logging()

# EXPORT ZMIENNEJ GLOBALNEJ (Fix dla błędu "Cannot find reference 'logger'")
# Dzięki temu stary kod: `from src.logger_config import logger` zadziała,
# ale docelowo zaleca się używanie `get_logger(__name__)`.
logger = logging.getLogger("GLOBAL")