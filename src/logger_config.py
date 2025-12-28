import logging
import sys
import os


def setup_logger(name: str = "BotLogger") -> logging.Logger:
    """
    Konfiguruje logger, który wypisuje komunikaty na konsolę (kolorowe)
    oraz zapisuje je do pliku (bot_activity.log).
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)  # Rejestrujemy wszystko od poziomu DEBUG w górę

    # Zapobiegamy dublowaniu logów przy wielokrotnym imporcie
    if logger.handlers:
        return logger

    # Format logów: [DATA GODZINA] [POZIOM] Treść
    formatter = logging.Formatter(
        fmt="[%(asctime)s] [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # 1. Handler Konsoli (to co widzisz na ekranie)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)  # Na ekranie tylko ważne info (bez śmieci debugowych)
    console_handler.setFormatter(formatter)

    # 2. Handler Pliku (zapis do pliku)
    # Tworzymy folder logs jeśli nie istnieje
    if not os.path.exists("logs"):
        os.makedirs("logs")

    file_handler = logging.FileHandler("logs/bot_activity.log", encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)  # W pliku zapisujemy absolutnie wszystko
    file_handler.setFormatter(formatter)

    # Dodajemy handlery do loggera
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger


# Tworzymy globalną instancję loggera do importowania w innych plikach
logger = setup_logger()