# src/config.py
import os
import platform
from dotenv import load_dotenv

load_dotenv()

# Wykrywanie systemu (Windows vs Linux/VPS)
IS_WINDOWS = platform.system() == "Windows"
IS_LINUX = platform.system() == "Linux"

# ==========================================
# KONFIGURACJA PRZEGLĄDARKI (Single Source of Truth)
# ==========================================

# Bazowe flagi (bezpieczne dla obu systemów)
BROWSER_ARGS = [
    "--disable-blink-features=AutomationControlled",
    "--no-sandbox",
    "--disable-infobars",
    "--disable-dev-shm-usage",
    "--disable-extensions",
    "--no-first-run",
    "--no-service-autorun",
    "--password-store=basic",
    "--window-size=1920,1080"  # Ważne dla headless!
]

# Specyficzne flagi dla Linuxa (VPS)
if IS_LINUX:
    BROWSER_ARGS.extend([
        "--disable-gpu",            # Na VPS zazwyczaj nie ma GPU
        "--use-gl=swiftshader",     # Renderowanie programowe
        "--single-process",         # Zwiększa stabilność na słabych VPS
    ])

# Specyficzne flagi dla Windowsa
if IS_WINDOWS:
    # Na Windowsie GPU zazwyczaj pomaga w 'humanizacji', więc go nie wyłączamy
    pass

# Czy używać systemowego Google Chrome?
# True = Używa zainstalowanego Chrome (brak niebieskiej ramki)
USE_SYSTEM_CHROME = True


# ==========================================
# FINGERPRINTING
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
# LOGOWANIE
# ==========================================
LOGGING_CONFIG = {
    "LOG_DIR": "logs",
    "LOG_FILENAME": "bot_log.log",
    "MAX_BYTES": 5 * 1024 * 1024,
    "BACKUP_COUNT": 3,
    "ENCODING": "utf-8",
    "LEVEL": "INFO"
}