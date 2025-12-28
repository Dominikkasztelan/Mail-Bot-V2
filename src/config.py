"""
Plik konfiguracyjny projektu.
Przechowuje stałe, listy i ustawienia, aby oddzielić dane od logiki kodu.
"""

# --- USTAWIENIA FINGERPRINTINGU (ODCISKI PALCA) ---

# Lista User-Agentów (Chrome na Windows 10/11)
USER_AGENTS = [
    # Windows 10
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.6167.85 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.6261.94 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.6312.58 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",

    # Windows 11
    "Mozilla/5.0 (Windows NT 11.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 11.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.6167.160 Safari/537.36",
    "Mozilla/5.0 (Windows NT 11.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.6261.112 Safari/537.36",
    "Mozilla/5.0 (Windows NT 11.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 11.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.6367.91 Safari/537.36",
    "Mozilla/5.0 (Windows NT 11.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.6422.60 Safari/537.36",
]

# Rozdzielczości ekranu (Viewporty)
VIEWPORTS = [
    {"width": 1366, "height": 768, "scale": 1},
    {"width": 1920, "height": 1080, "scale": 1},
    {"width": 1536, "height": 864, "scale": 1.25},
    {"width": 1440, "height": 900, "scale": 1},
    {"width": 2560, "height": 1440, "scale": 1.5},
    {"width": 1280, "height": 720, "scale": 1},
]

# --- USTAWIENIA GENERATORA TOŻSAMOŚCI ---
GENERATOR_CONFIG = {
    "LOCALE": "pl_PL",
    "PASSWORD_DEFAULT": "SilneHaslo123!@#",
    "YEAR_MIN": 1974,
    "YEAR_MAX": 2006,
}



# --- KONFIGURACJA CZASÓW (PRĘDKOŚĆ BOTA) ---
# Zmieniając te liczby, sterujesz czy bot jest "Żółwiem" czy "Zającem"
DELAYS = {
    "PAGE_LOAD_MIN": 2.0,
    "PAGE_LOAD_MAX": 4.0,

    "HUMAN_TYPE_MIN": 0.15,  # Opóźnienie między klawiszami (sekundy)
    "HUMAN_TYPE_MAX": 0.35,

    "THINKING_MIN": 1.5,  # Czas "zastanawiania się"
    "THINKING_MAX": 3.5,

    "SECTION_PAUSE_MIN": 2.0,  # Przerwa między sekcjami formularza
    "SECTION_PAUSE_MAX": 4.0
}