import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
from typing import Optional

# Import konfiguracji zamiast hardcodowania
from src.config import LOGGING_CONFIG


def setup_logging() -> None:
    """
    Konfiguruje globalny system logowania z obsługą rotacji plików i UTF-8.
    Pobiera ustawienia z src.config.LOGGING_CONFIG.
    Jest idempotentna (można wywołać wielokrotnie bez duplikowania handlerów).
    """
    # 1. Pobranie konfiguracji
    log_dir_path = Path(LOGGING_CONFIG["LOG_DIR"])
    log_filename = str(LOGGING_CONFIG["LOG_FILENAME"])
    max_bytes = int(LOGGING_CONFIG["MAX_BYTES"])
    backup_count = int(LOGGING_CONFIG["BACKUP_COUNT"])
    encoding = str(LOGGING_CONFIG["ENCODING"])
    log_level = str(LOGGING_CONFIG["LEVEL"]).upper()

    # 2. Utworzenie katalogu logów
    log_dir_path.mkdir(exist_ok=True)
    log_path = log_dir_path / log_filename

    # 3. Pobranie root loggera
    root_logger = logging.getLogger()

    # Ustawienie poziomu logowania na podstawie configu
    level = getattr(logging, log_level, logging.INFO)
    root_logger.setLevel(level)

    # 4. Wyczyszczenie istniejących handlerów (zapobiega duplikatom przy reloadzie/multiprocessingu)
    if root_logger.hasHandlers():
        root_logger.handlers.clear()

    # 5. Formatowanie logów (Czas - Poziom - Moduł - Wiadomość)
    formatter = logging.Formatter(
        '%(asctime)s - [%(levelname)s] - %(name)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # 6. Handler Plikowy z Rotacją (RotatingFileHandler)
    file_handler = RotatingFileHandler(
        log_path,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding=encoding
    )
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)

    # 7. Handler Konsolowy (stdout)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # 8. Wyciszenie bibliotek zewnętrznych (zbyt gadatliwe na INFO)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('playwright').setLevel(logging.WARNING)
    logging.getLogger('selenium').setLevel(logging.WARNING)
    logging.getLogger('webdriver_manager').setLevel(logging.WARNING)
    logging.getLogger('google.genai').setLevel(logging.WARNING)
    logging.getLogger('httpcore').setLevel(logging.WARNING)
    logging.getLogger('httpx').setLevel(logging.WARNING)


def get_logger(module_name: str) -> logging.Logger:
    """
    Zwraca logger dla konkretnego modułu. To jest zalecana metoda tworzenia loggerów.

    Args:
        module_name (str): Nazwa modułu, zazwyczaj __name__.

    Returns:
        logging.Logger: Skonfigurowany obiekt loggera.
    """
    # Upewniamy się, że logging jest skonfigurowany (Lazy Init)
    if not logging.getLogger().hasHandlers():
        setup_logging()

    return logging.getLogger(module_name)


# --- INICJALIZACJA I WSTECZNA KOMPATYBILNOŚĆ ---

# Uruchamiamy konfigurację przy imporcie modułu
setup_logging()

# EXPORT ZMIENNEJ GLOBALNEJ (dla kompatybilności ze starym kodem)
logger: logging.Logger = logging.getLogger("GLOBAL")