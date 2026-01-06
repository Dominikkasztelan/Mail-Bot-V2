import os
import platform
from dotenv import load_dotenv

# 1. Ładowanie zmiennych z pliku .env
load_dotenv()

# Wykrywanie systemu (Windows vs Linux/VPS)
IS_WINDOWS = platform.system() == "Windows"
IS_LINUX = platform.system() == "Linux"

# ==========================================
# KONFIGURACJA PRZEGLĄDARKI (Single Source of Truth)
# ==========================================

# Bazowe flagi (bezpieczne dla obu systemów)
BROWSER_ARGS = [
    "--disable-blink-features=AutomationControlled", # Ukrywa informację o automatyzacji
    "--no-sandbox",                                  # Wymagane na Dockerze/VPS
    "--disable-infobars",
    "--disable-dev-shm-usage",
    "--disable-extensions",
    "--no-first-run",
    "--no-service-autorun",
    "--password-store=basic",
    "--window-size=1920,1080"  # Kluczowe dla trybu Headless, żeby nie był 800x600
]

# Specyficzne flagi dla Linuxa (VPS / Docker)
if IS_LINUX:
    BROWSER_ARGS.extend([
        "--disable-gpu",            # Na serwerach zazwyczaj brak GPU
        "--use-gl=swiftshader",     # Renderowanie programowe
        "--single-process",         # Zwiększa stabilność na słabych maszynach
    ])

# Specyficzne flagi dla Windowsa
if IS_WINDOWS:
    # Na Windowsie GPU pomaga w 'humanizacji' (WebGL wygląda naturalnie), więc go nie wyłączamy.
    pass

# Czy używać systemowego Google Chrome?
# True = Używa zainstalowanego Chrome (brak niebieskiej ramki, większe zaufanie)
USE_SYSTEM_CHROME = True


# ==========================================
# FINGERPRINTING (UDWANIE UŻYTKOWNIKA)
# ==========================================
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.6167.85 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.6261.94 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.6312.58 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.6367.60 Safari/537.36",
    "Mozilla/5.0 (Windows NT 11.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
]

VIEWPORTS = [
    {"width": 1920, "height": 1080},
    {"width": 1366, "height": 768},
    {"width": 1536, "height": 864},
    {"width": 1440, "height": 900},
    {"width": 2560, "height": 1440},
]

# ==========================================
# GENERATOR DANYCH
# ==========================================
GENERATOR_CONFIG = {
    "LOCALE": "pl_PL",
    "PASSWORD_DEFAULT": "SilneHaslo123!@#",
    "YEAR_MIN": 1974,
    "YEAR_MAX": 2005,
}

# ==========================================
# SEKRETY I API (Rotacja kluczy)
# ==========================================
# Pobieramy ciąg znaków z .env, np. "klucz1, klucz2, klucz3"
raw_gemini_keys = os.getenv("GEMINI_API_KEY", "")

# Parsujemy do listy:
# 1. Dzielimy po przecinku.
# 2. Usuwamy spacje (strip) - to naprawia błąd "klucz1, klucz2".
# 3. Ignorujemy puste wpisy.
gemini_keys_list = [k.strip() for k in raw_gemini_keys.split(",") if k.strip()]

API_KEYS = {
    "GEMINI": gemini_keys_list
}

# ==========================================
# PROXY (WARSTWA SIECIOWA)
# ==========================================
PROXIES = []  # format: "http://user:pass@ip:port"

# ==========================================
# OPÓŹNIENIA (HUMANIZATION)
# ==========================================
DELAYS = {
    "PAGE_LOAD_MIN": 2.0, "PAGE_LOAD_MAX": 4.0,
    "HUMAN_TYPE_MIN": 0.15, "HUMAN_TYPE_MAX": 0.35, # Szybkość pisania (sekundy na znak)
    "THINKING_MIN": 1.5, "THINKING_MAX": 3.5,       # Czas "zastanawiania się"
    "SECTION_PAUSE_MIN": 2.0, "SECTION_PAUSE_MAX": 4.0 # Przerwy między sekcjami formularza
}

# ==========================================
# LOGOWANIE
# ==========================================
LOGGING_CONFIG = {
    "LOG_DIR": "logs",
    "LOG_FILENAME": "bot_log.log",
    "MAX_BYTES": 5 * 1024 * 1024,  # 5 MB
    "BACKUP_COUNT": 3,
    "ENCODING": "utf-8",
    "LEVEL": "DEBUG"
}

# ==========================================
# CONFIG LAUNCHERA
# ==========================================
LAUNCHER_CONFIG = {
    "CONCURRENT_BROWSERS": 3,        # Ilość równoległych Workerów
    "STARTUP_DELAY_MULTIPLIER": 2.5  # Opóźnienie startu kolejnych okien
}