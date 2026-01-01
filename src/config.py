import os
from dotenv import load_dotenv

# 1. Ładowanie zmiennych z pliku .env
load_dotenv()

# --- USTAWIENIA FINGERPRINTINGU ---
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.6167.85 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.6261.94 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.6312.58 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.6367.60 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",

    # Windows 11
    "Mozilla/5.0 (Windows NT 11.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 11.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.6167.160 Safari/537.36",
    "Mozilla/5.0 (Windows NT 11.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.6261.112 Safari/537.36",
    "Mozilla/5.0 (Windows NT 11.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 11.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.6367.91 Safari/537.36",
    "Mozilla/5.0 (Windows NT 11.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 11.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.6422.60 Safari/537.36",
    "Mozilla/5.0 (Windows NT 11.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
]

VIEWPORTS = [
    {"width": 1366, "height": 768, "scale": 1},
    {"width": 1920, "height": 1080, "scale": 1},
    {"width": 1536, "height": 864, "scale": 1.25},
    {"width": 1440, "height": 900, "scale": 1},
    {"width": 2560, "height": 1440, "scale": 1.5},
    {"width": 1280, "height": 720, "scale": 1},
]

# --- GENERATOR ---
GENERATOR_CONFIG = {
    "LOCALE": "pl_PL",
    "PASSWORD_DEFAULT": "SilneHaslo123!@#",
    "YEAR_MIN": 1974,
    "YEAR_MAX": 2006,
}

# --- SEKRETY (BEZPIECZNE) ---

API_KEYS = {
    "GEMINI": os.getenv("GEMINI_API_KEY")
}

# --- PROXY ---
PROXIES = []  # Możesz tu dodać listę proxy, jeśli masz

# --- OPÓŹNIENIA ---
DELAYS = {
    "PAGE_LOAD_MIN": 2.0, "PAGE_LOAD_MAX": 4.0,
    "HUMAN_TYPE_MIN": 0.15, "HUMAN_TYPE_MAX": 0.35,
    "THINKING_MIN": 1.5, "THINKING_MAX": 3.5,
    "SECTION_PAUSE_MIN": 2.0, "SECTION_PAUSE_MAX": 4.0
}

# --- KONFIGURACJA LOGOWANIA (NOWE) ---
LOGGING_CONFIG = {
    "LOG_DIR": "logs",
    "LOG_FILENAME": "bot_log.log",
    "MAX_BYTES": 5 * 1024 * 1024,  # 5 MB na plik
    "BACKUP_COUNT": 3,             # Ilość plików w rotacji
    "ENCODING": "utf-8",
    "LEVEL": "INFO"                # Poziom logowania (DEBUG, INFO, WARNING, ERROR)
}


# --- KONFIGURACJA LAUNCHERA ---
LAUNCHER_CONFIG = {
    "CONCURRENT_BROWSERS": 3,  # Ilość uruchamianych przeglądarek
    "STARTUP_DELAY_MULTIPLIER": 2.5  # Opóźnienie startu kolejnych okien (sekundy)
}