import logging
import sys
from pathlib import Path


def setup_logging():
    """Konfiguruje globalny logger z obsługą UTF-8"""
    # Tworzenie katalogu logs, jeśli nie istnieje
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    # Konfiguracja formatu loggera
    log_format = '%(asctime)s - %(levelname)s - %(name)s - %(message)s'

    # Konfiguracja głównego loggera
    logging.basicConfig(
        level=logging.INFO,
        format=log_format,
        handlers=[
            logging.FileHandler(log_dir / "bot_log.log", encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )

    # Rekonfiguracja kodowania dla stdout (terminala)
    sys.stdout.reconfigure(encoding='utf-8')  # Rekonfiguruj stdout dla Pythona 3.7+

    # Wycisz zbędne logowanie z bibliotek zewnętrznych
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('selenium').setLevel(logging.WARNING)
    logging.getLogger('webdriver_manager').setLevel(logging.WARNING)


def get_logger(name):
    """
    Zwraca skonfigurowany logger dla danego modułu

    Args:
        name: Nazwa modułu, zazwyczaj __name__

    Returns:
        Logger: Skonfigurowany obiekt logger
    """
    # Upewniamy się, że główna konfiguracja została wykonana
    if not logging.getLogger().handlers:
        setup_logging()

    # Zwróć logger dla danego modułu
    logger = logging.getLogger(name)
    return logger


# Wykonaj konfigurację podczas importu modułu
setup_logging()