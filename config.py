#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
config.py - Plik konfiguracyjny dla bota tworzenia kont Interia

Ten plik zawiera wszystkie ustawienia konfiguracyjne dla bota.
Możesz dostosować te wartości według swoich potrzeb.
"""


class BotConfig:
    """
    Główna klasa konfiguracyjna bota tworzenia kont

    Zawiera wszystkie parametry konfiguracyjne pogrupowane tematycznie:
    - Próby i timeouty
    - Opóźnienia
    - Ustawienia przeglądarki
    - Ścieżki katalogów
    - Ustawienia logowania
    - Statystyki i raportowanie
    - ChatGPT CAPTCHA solver
    - Bezpieczeństwo
    """

    # ===== KONFIGURACJA PRÓB I TIMEOUTÓW =====
    MAX_FULL_RETRIES_PER_ACCOUNT = 3  # Maksymalna liczba pełnych restartów na konto
    MAX_CAPTCHA_ATTEMPTS = 2  # Maksymalna liczba prób CAPTCHA w jednej sesji
    CHATGPT_TIMEOUT = 90  # Timeout dla ChatGPT solver'a (sekundy)

    # Timeouty dla różnych operacji (sekundy)
    FORM_SUBMISSION_TIMEOUT = 8  # Timeout sprawdzania wysłania formularza
    REGISTRATION_SUCCESS_TIMEOUT = 30  # Timeout sprawdzania sukcesu rejestracji
    GDPR_TIMEOUT = 20  # Timeout obsługi ekranu GDPR
    ELEMENT_WAIT_TIMEOUT = 10  # Standardowy timeout oczekiwania na elementy
    PAGE_LOAD_TIMEOUT = 30  # Timeout ładowania strony

    # ===== OPÓŹNIENIA MIĘDZY OPERACJAMI =====
    # Format: (minimum, maximum) w sekundach
    DELAY_BETWEEN_ACCOUNTS = (5, 20)  # Opóźnienie między próbami tworzenia kont
    DELAY_BETWEEN_RETRIES = (3, 7)  # Opóźnienie między pełnymi próbami tego samego konta
    DELAY_AFTER_FORM_FILL = (1, 2)  # Opóźnienie po wypełnieniu formularza
    DELAY_AFTER_CAPTCHA = (2, 4)  # Opóźnienie po wprowadzeniu CAPTCHA
    DELAY_NATURAL_TYPING = (0.05, 0.25)  # Opóźnienie między znakami podczas pisania

    # ===== USTAWIENIA PRZEGLĄDARKI =====
    BROWSER_HEADLESS = False  # Czy uruchomić w trybie headless (bez okna)
    BROWSER_WINDOW_SIZE = (1920, 1080)  # Rozmiar okna przeglądarki
    BROWSER_MAXIMIZE = True  # Czy maksymalizować okno przeglądarki
    BROWSER_INCOGNITO = True  # Czy używać trybu incognito

    # User Agents dla różnorodności
    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0"
    ]

    # ===== ŚCIEŻKI I KATALOGI =====
    SCREENSHOTS_DIR = "screenshots"  # Katalog na zrzuty ekranu
    CAPTCHA_DIR = "captcha_images"  # Katalog na obrazki CAPTCHA
    LOGS_DIR = "logs"  # Katalog na pliki logów
    SAVED_ACCOUNTS_DIR = "saved_accounts"  # Katalog na zapisane dane kont
    STATS_DIR = "statistics"  # Katalog na pliki statystyk

    # Nazwy plików
    MAIN_LOG_FILE = "bot_log.log"  # Główny plik logów
    STATS_FILE = "bot_stats.json"  # Plik ze statystykami sesji
    ERROR_LOG_FILE = "errors.log"  # Plik z błędami

    # ===== USTAWIENIA LOGOWANIA =====
    LOG_LEVEL = "INFO"  # Poziom logowania (DEBUG, INFO, WARNING, ERROR)
    LOG_TO_FILE = True  # Czy zapisywać logi do pliku
    LOG_TO_CONSOLE = True  # Czy wyświetlać logi w konsoli
    LOG_FORMAT = '%(asctime)s - %(levelname)s - %(name)s - %(message)s'
    LOG_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'
    LOG_ENCODING = 'utf-8'  # Kodowanie plików logów

    # ===== STATYSTYKI I RAPORTOWANIE =====
    SAVE_SUCCESS_SCREENSHOTS = True  # Czy zapisywać zrzuty ekranu sukcesu
    SAVE_ERROR_SCREENSHOTS = True  # Czy zapisywać zrzuty ekranu błędów
    SAVE_CAPTCHA_IMAGES = True  # Czy zachowywać obrazki CAPTCHA
    GENERATE_SUMMARY_REPORT = True  # Czy generować raport podsumowujący
    GENERATE_DETAILED_STATS = True  # Czy generować szczegółowe statystyki
    SAVE_STATS_REALTIME = True  # Czy zapisywać statystyki na bieżąco

    # ===== CHATGPT CAPTCHA SOLVER =====
    USE_CHATGPT_SOLVER = True  # Czy używać ChatGPT do rozwiązywania CAPTCHA
    CHATGPT_HEADLESS = True  # Czy uruchomić ChatGPT w trybie headless
    CHATGPT_MAX_RETRIES = 2  # Maksymalna liczba prób rozpoznania przez ChatGPT
    FALLBACK_TO_MANUAL = True  # Czy przełączyć na ręczne wprowadzenie po niepowodzeniu

    # Prompt dla ChatGPT
    CHATGPT_PROMPT = "Jaki tekst znajduje się na tym obrazie CAPTCHA? Odpowiedz tylko tekstem z obrazka w cudzysłowie, bez dodatkowych komentarzy."

    # ===== USTAWIENIA BEZPIECZEŃSTWA =====
    RANDOM_USER_AGENTS = True  # Czy używać losowych User-Agent'ów
    CLEAR_BROWSER_DATA = True  # Czy czyścić dane przeglądarki między próbami
    USE_PROXY = False  # Czy używać proxy (wymaga konfiguracji PROXY_LIST)
    ROTATE_PROXY = False  # Czy rotować proxy między kontami

    # Lista proxy (jeśli USE_PROXY = True)
    PROXY_LIST = [
        # Format: "ip:port" lub "user:pass@ip:port"
        # Przykład: "127.0.0.1:8080"
    ]

    # ===== USTAWIENIA FORMULARZA =====
    # Czy używać realistycznych danych
    USE_REALISTIC_NAMES = True  # Czy generować realistyczne imiona/nazwiska
    PASSWORD_LENGTH = 12  # Długość generowanego hasła
    PASSWORD_COMPLEXITY = True  # Czy używać złożonych haseł (znaki specjalne)

    # Zakres dat urodzenia
    BIRTH_YEAR_MIN = 1970  # Minimalny rok urodzenia
    BIRTH_YEAR_MAX = 2000  # Maksymalny rok urodzenia

    # ===== USTAWIENIA DEBUGOWANIA =====
    DEBUG_MODE = False  # Czy włączyć tryb debugowania
    VERBOSE_LOGGING = False  # Czy włączyć szczegółowe logowanie
    SAVE_PAGE_SOURCE = False  # Czy zapisywać kod źródłowy strony przy błędach
    PAUSE_ON_ERROR = False  # Czy zatrzymać wykonanie przy błędach

    # ===== URL I SELEKTORY =====
    REGISTRATION_URL = "https://konto-pocztowe.interia.pl/"
    EMAIL_DOMAIN = "@interia.pl"

    # ===== USTAWIENIA WYDAJNOŚCI =====
    MAX_CONCURRENT_BROWSERS = 1  # Maksymalna liczba równoczesnych przeglądarek
    MEMORY_LIMIT_MB = 2048  # Limit pamięci na przeglądarkę (MB)

    @classmethod
    def get_config_summary(cls):
        """
        Zwraca czytelne podsumowanie konfiguracji

        Returns:
            str: Sformatowane podsumowanie głównych ustawień
        """
        return f"""
╔══════════════════════════════════════════════════════════════╗
║                    KONFIGURACJA BOTA                         ║
╠══════════════════════════════════════════════════════════════╣
║ Maksymalne pełne próby na konto: {cls.MAX_FULL_RETRIES_PER_ACCOUNT:2d}                    ║
║ Maksymalne próby CAPTCHA:        {cls.MAX_CAPTCHA_ATTEMPTS:2d}                    ║
║ Timeout ChatGPT:                 {cls.CHATGPT_TIMEOUT:3d}s                  ║
║ Opóźnienie między kontami:       {cls.DELAY_BETWEEN_ACCOUNTS[0]:2d}-{cls.DELAY_BETWEEN_ACCOUNTS[1]:2d}s               ║
║ Tryb headless:                   {'Tak' if cls.BROWSER_HEADLESS else 'Nie':3s}                  ║
║ ChatGPT solver:                  {'Włączony' if cls.USE_CHATGPT_SOLVER else 'Wyłączony':9s}           ║
║ Zapisywanie statystyk:           {'Tak' if cls.GENERATE_SUMMARY_REPORT else 'Nie':3s}                  ║
║ Zapisywanie zrzutów ekranu:      {'Tak' if cls.SAVE_ERROR_SCREENSHOTS else 'Nie':3s}                  ║
╚══════════════════════════════════════════════════════════════╝
        """

    @classmethod
    def get_full_config(cls):
        """
        Zwraca pełną konfigurację jako słownik

        Returns:
            dict: Wszystkie ustawienia konfiguracyjne
        """
        config = {}
        for attr_name in dir(cls):
            if not attr_name.startswith('_') and not callable(getattr(cls, attr_name)):
                if attr_name not in ['get_config_summary', 'get_full_config', 'validate_config']:
                    config[attr_name] = getattr(cls, attr_name)
        return config

    @classmethod
    def validate_config(cls):
        """
        Sprawdza poprawność konfiguracji i wyświetla ostrzeżenia

        Returns:
            bool: True jeśli konfiguracja jest prawidłowa
        """
        warnings = []
        errors = []

        # Sprawdź wartości liczbowe
        if cls.MAX_FULL_RETRIES_PER_ACCOUNT < 1:
            errors.append("MAX_FULL_RETRIES_PER_ACCOUNT musi być >= 1")

        if cls.MAX_CAPTCHA_ATTEMPTS < 1:
            errors.append("MAX_CAPTCHA_ATTEMPTS musi być >= 1")

        if cls.CHATGPT_TIMEOUT < 30:
            warnings.append("CHATGPT_TIMEOUT < 30s może być za krótki")

        # Sprawdź opóźnienia
        if cls.DELAY_BETWEEN_ACCOUNTS[0] >= cls.DELAY_BETWEEN_ACCOUNTS[1]:
            errors.append("DELAY_BETWEEN_ACCOUNTS: minimum musi być mniejsze od maksimum")

        # Sprawdź ścieżki
        if not all([cls.SCREENSHOTS_DIR, cls.LOGS_DIR, cls.SAVED_ACCOUNTS_DIR]):
            errors.append("Wszystkie ścieżki katalogów muszą być określone")

        # Sprawdź proxy
        if cls.USE_PROXY and not cls.PROXY_LIST:
            warnings.append("USE_PROXY=True ale PROXY_LIST jest pusta")

        # Wyświetl ostrzeżenia i błędy
        if warnings:
            print("⚠️  OSTRZEŻENIA KONFIGURACJI:")
            for warning in warnings:
                print(f"   - {warning}")

        if errors:
            print("❌ BŁĘDY KONFIGURACJI:")
            for error in errors:
                print(f"   - {error}")
            return False

        if not warnings and not errors:
            print("✅ Konfiguracja jest prawidłowa")

        return True


# Jeśli plik jest uruchamiany bezpośrednio, wyświetl konfigurację
if __name__ == "__main__":
    print("Testowanie konfiguracji bota...")
    print(BotConfig.get_config_summary())

    print("\nWalidacja konfiguracji:")
    BotConfig.validate_config()

    print(f"\nLiczba parametrów konfiguracyjnych: {len(BotConfig.get_full_config())}")

    # Przykład dostępu do konfiguracji
    print(f"\nPrzykład użycia:")
    print(f"Maksymalne próby CAPTCHA: {BotConfig.MAX_CAPTCHA_ATTEMPTS}")
    print(f"Katalog logów: {BotConfig.LOGS_DIR}")
    print(f"User Agent: {BotConfig.USER_AGENTS[0][:50]}...")