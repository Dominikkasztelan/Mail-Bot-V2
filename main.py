#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
main.py - POPRAWIONA WERSJA
Główny plik bota tworzenia kont Interia z uproszczoną logiką sukcesu
"""

import time
import random
import traceback
from pathlib import Path

# Importuj moduły z pakietu src
from src.browser_setup import create_stealth_browser
from src.user_actions import click_username_field, browse_naturally
from src.form_handlers import fill_registration_form
from src.captcha_handler import simplified_handle_captcha_and_submit, test_current_page_for_captcha_error
from src.gdpr_handler import handle_gdpr_screen, check_popups
from src.logger_config import get_logger
from src.data_saver import save_account

# Inicjalizacja loggera
logger = get_logger(__name__)


def check_if_left_registration_page(driver, timeout=5):
    """
    NOWA FUNKCJA: Sprawdza czy nastąpiło przekierowanie ze strony rejestracji
    To jest dodatkowy wskaźnik sukcesu (opcjonalny)

    Args:
        driver: WebDriver Selenium
        timeout: Maksymalny czas oczekiwania

    Returns:
        tuple: (success: bool, message: str)
    """
    try:
        time.sleep(timeout)  # Daj czas na ewentualne przekierowanie

        current_url = driver.current_url.lower()
        logger.info(f"📍 Aktualny URL po przesłaniu: {current_url}")

        # Sprawdź czy nadal jesteśmy na stronie rejestracji
        registration_indicators = [
            "register", "rejestracja", "signup", "sign-up",
            "create-account", "new-account", "konto-pocztowe"
        ]

        still_on_registration = any(indicator in current_url for indicator in registration_indicators)

        if not still_on_registration:
            # Sprawdź pozytywne wskaźniki przekierowania
            success_indicators = [
                "welcome", "witaj", "success", "sukces", "confirm", "potwierdz",
                "thank", "dziek", "login", "zaloguj", "mail", "inbox", "skrzynka"
            ]

            redirect_to_success = any(indicator in current_url for indicator in success_indicators)

            if redirect_to_success:
                return True, f"Przekierowanie na stronę sukcesu: {current_url}"
            else:
                return True, f"Opuszczono stronę rejestracji: {current_url}"
        else:
            return False, f"Nadal na stronie rejestracji: {current_url}"

    except Exception as e:
        logger.warning(f"⚠️ Błąd podczas sprawdzania przekierowania: {e}")
        return None, f"Błąd sprawdzania: {str(e)}"


def restart_browser(driver):
    """
    Restartuje przeglądarkę dla świeżego startu

    Args:
        driver: Obecna instancja WebDriver

    Returns:
        WebDriver: Nowa instancja przeglądarki
    """
    logger.info("🔄 Restartuję przeglądarkę...")

    if driver:
        try:
            driver.quit()
        except:
            pass

    # Dodaj opóźnienie przed utworzeniem nowej przeglądarki
    time.sleep(random.uniform(3, 7))

    return create_stealth_browser()


def single_registration_attempt(max_full_retries=3, auto_mode=False, enable_debugging=False):
    """
    POPRAWIONA funkcja - jedna próba rejestracji z uproszczoną logiką sukcesu

    Args:
        max_full_retries: Maksymalna liczba pełnych restartów procesu
        auto_mode: Czy działać w trybie automatycznym
        enable_debugging: Czy włączyć funkcje debugowania

    Returns:
        tuple: (account_data, registration_status)
    """
    driver = None
    account_data = None
    registration_status = "failed"

    for full_attempt in range(max_full_retries):
        logger.info(f"🔥 Pełna próba rejestracji {full_attempt + 1}/{max_full_retries}")

        try:
            # Restart przeglądarki dla każdej pełnej próby (oprócz pierwszej)
            if full_attempt > 0:
                driver = restart_browser(driver)
            else:
                driver = create_stealth_browser()

            if not driver:
                logger.error("❌ Nie udało się utworzyć przeglądarki")
                continue

            # Otwórz stronę rejestracji
            registration_url = "https://konto-pocztowe.interia.pl/"
            logger.info(f"🌐 Otwieram stronę rejestracji (próba {full_attempt + 1})...")
            driver.get(registration_url)
            time.sleep(random.uniform(3, 5))

            # Obsługa ekranu GDPR
            if not handle_gdpr_screen(driver):
                logger.warning("⚠️ Problem z obsługą GDPR, kontynuuję...")

            time.sleep(random.uniform(1, 3))
            check_popups(driver)

            # Naturalne przeglądanie
            browse_naturally(driver)
            check_popups(driver)

            # Kliknij w pole nazwy konta
            click_username_field(driver)
            time.sleep(random.uniform(1, 2))

            # Wypełnij formularz
            filled_successfully, account_data = fill_registration_form(driver, return_data=True)
            if not filled_successfully:
                logger.warning(f"⚠️ Nie udało się wypełnić formularza w próbie {full_attempt + 1}")
                if account_data:
                    save_account(account_data, status="failed_form")
                continue  # Przejdź do następnej pełnej próby

            # KLUCZOWY MOMENT: Obsługa CAPTCHA z nową logiką
            logger.info("🧩 Rozpoczynam obsługę CAPTCHA...")
            captcha_success = simplified_handle_captcha_and_submit(driver, max_attempts=2)

            if captcha_success:
                # ✅ SUKCES! - Brak komunikatu "Przepisz kod z obrazka"
                logger.info("🎉 SUKCES! Formularz przesłany bez błędu CAPTCHA")

                # Opcjonalnie: sprawdź czy nastąpiło przekierowanie (dodatkowy wskaźnik)
                redirect_success, redirect_message = check_if_left_registration_page(driver, timeout=5)
                if redirect_success:
                    logger.info(f"✅ Dodatkowe potwierdzenie sukcesu: {redirect_message}")
                elif redirect_success is False:
                    logger.info(f"ℹ️ Brak przekierowania: {redirect_message}")
                # redirect_success is None = błąd sprawdzania, ignorujemy

                registration_status = "created"
                save_account(account_data, status=registration_status)

                logger.info(f"🎉 Sukces! Utworzono konto: {account_data['username']}@interia.pl")
                logger.info(f"🔑 Hasło: {account_data['password']}")

                # Zapisz zrzut ekranu sukcesu
                try:
                    screenshots_dir = Path("screenshots")
                    screenshots_dir.mkdir(exist_ok=True)
                    timestamp = time.strftime("%Y%m%d_%H%M%S")
                    screenshot_path = screenshots_dir / f"success_{account_data['username']}_{timestamp}.png"
                    driver.save_screenshot(str(screenshot_path))
                    logger.info(f"📸 Zrzut ekranu sukcesu: {screenshot_path}")
                except Exception as e:
                    logger.warning(f"⚠️ Nie udało się zapisać zrzutu ekranu sukcesu: {e}")

                return account_data, registration_status

            else:
                # ❌ NIEPOWODZENIE - Pojawiał się komunikat "Przepisz kod z obrazka"
                logger.warning(f"❌ Niepowodzenie CAPTCHA w próbie {full_attempt + 1}")
                save_account(account_data, status="failed_captcha")

                # Debugowanie - jeśli włączone
                if enable_debugging:
                    logger.info("🧪 Uruchamiam debugowanie...")
                    try:
                        test_current_page_for_captcha_error(driver)
                        if not auto_mode:
                            input("🔍 Naciśnij Enter aby kontynuować...")
                    except Exception as debug_error:
                        logger.error(f"❌ Błąd debugowania: {debug_error}")

                continue  # Restart całego procesu

        except Exception as e:
            logger.error(f"❌ Błąd w próbie {full_attempt + 1}: {e}")
            logger.error(traceback.format_exc())

            if account_data:
                save_account(account_data, status="error")

            # Zapisz zrzut ekranu błędu
            if driver:
                try:
                    screenshots_dir = Path("screenshots")
                    screenshots_dir.mkdir(exist_ok=True)
                    timestamp = time.strftime("%Y%m%d_%H%M%S")
                    screenshot_path = screenshots_dir / f"error_attempt_{full_attempt + 1}_{timestamp}.png"
                    driver.save_screenshot(str(screenshot_path))
                    logger.info(f"📸 Zrzut ekranu błędu: {screenshot_path}")
                except Exception as screenshot_error:
                    logger.warning(f"⚠️ Nie udało się zapisać zrzutu ekranu błędu: {screenshot_error}")

            continue  # Próbuj ponownie

    # Wszystkie próby się nie powiodły
    logger.error(f"❌ Wszystkie {max_full_retries} prób rejestracji zakończone niepowodzeniem")

    # Zamknij przeglądarkę
    if driver:
        try:
            driver.quit()
        except:
            pass

    return account_data, registration_status


def create_multiple_accounts(num_accounts, max_retries_per_account=3, enable_debugging=False):
    """
    POPRAWIONA funkcja do tworzenia wielu kont z uproszczoną logiką

    Args:
        num_accounts: Liczba kont do utworzenia
        max_retries_per_account: Maksymalna liczba prób na konto
        enable_debugging: Czy włączyć funkcje debugowania
    """
    successful_accounts = 0
    failed_accounts = 0
    total_attempts = 0

    logger.info(f"🔥 Rozpoczynam tworzenie {num_accounts} kont...")

    for i in range(num_accounts):
        logger.info(f"🔥 Konto {i + 1}/{num_accounts}...")

        # Losowe opóźnienie między kontami (5-20 sekund)
        if i > 0:
            delay = random.uniform(5, 20)
            logger.info(f"⏱️ Opóźnienie {delay:.1f}s przed kolejnym kontem...")
            time.sleep(delay)

        # Próbuj utworzyć konto z restartami
        account_data, status = single_registration_attempt(
            max_full_retries=max_retries_per_account,
            auto_mode=True,
            enable_debugging=enable_debugging
        )

        total_attempts += 1

        if status == "created":
            successful_accounts += 1
            logger.info(f"✅ Konto {i + 1} utworzone pomyślnie!")
        else:
            failed_accounts += 1
            logger.error(f"❌ Konto {i + 1} - niepowodzenie")

        # Statystyki po każdym koncie
        success_rate = (successful_accounts / total_attempts) * 100
        logger.info(f"📊 Statystyki: {successful_accounts}/{total_attempts} kont ({success_rate:.1f}% sukcesu)")

    # Podsumowanie
    final_success_rate = (successful_accounts / total_attempts) * 100 if total_attempts > 0 else 0

    logger.info("=" * 60)
    logger.info("🏁 PODSUMOWANIE KOŃCOWE:")
    logger.info(f"   ✅ Utworzonych kont: {successful_accounts}")
    logger.info(f"   ❌ Nieudanych: {failed_accounts}")
    logger.info(f"   📈 Wskaźnik sukcesu: {final_success_rate:.1f}%")
    logger.info("=" * 60)

    # Czekaj na zamknięcie
    logger.info("⏱️ Czekam na ręczne zamknięcie...")
    while True:
        if input("Naciśnij 'q' aby zakończyć: ").lower() == 'q':
            break
        time.sleep(1)


def main(auto_mode=False, enable_debugging=False):
    """
    POPRAWIONA główna funkcja programu

    Args:
        auto_mode: Czy działać w trybie automatycznym
        enable_debugging: Czy włączyć funkcje debugowania
    """
    logger.info("🚀 Uruchamiam bot tworzenia kont Interia (POPRAWIONA WERSJA)...")
    logger.info("🔧 Nowa logika: Sukces = brak komunikatu 'Przepisz kod z obrazka'")

    account_data, status = single_registration_attempt(
        max_full_retries=3,
        auto_mode=auto_mode,
        enable_debugging=enable_debugging
    )

    if not auto_mode and status != "created":
        logger.info("⏱️ Czekam na ręczne zamknięcie...")
        while True:
            if input("Naciśnij 'q' aby zakończyć: ").lower() == 'q':
                break
            time.sleep(1)

    logger.info("✅ Program zakończony")
    return account_data, status


def test_mode():
    """
    NOWA FUNKCJA: Tryb testowy do sprawdzenia wykrywania błędów CAPTCHA
    """
    logger.info("🧪 TRYB TESTOWY - sprawdzanie wykrywania błędów CAPTCHA")

    # Instrukcja dla użytkownika
    print("\n" + "=" * 60)
    print("🧪 TRYB TESTOWY")
    print("=" * 60)
    print("Instrukcje:")
    print("1. Bot wypełni formularz normalnie")
    print("2. Gdy pojawi się CAPTCHA - WPROWADŹ CELOWO BŁĘDNY KOD")
    print("3. Bot sprawdzi czy wykrywa komunikat błędu")
    print("4. Następnie wprowadź poprawny kod")
    print("5. Bot sprawdzi czy wykrywa sukces")
    print("=" * 60)
    input("Naciśnij Enter aby rozpocząć test...")

    # Uruchom jedną próbę z debugowaniem
    account_data, status = single_registration_attempt(
        max_full_retries=1,
        auto_mode=False,
        enable_debugging=True
    )

    print(f"\n🏁 WYNIK TESTU: {status}")
    if status == "created":
        print("✅ Test zakończony sukcesem!")
    else:
        print("❌ Test nie zakończony sukcesem")

    input("Naciśnij Enter aby zakończyć...")


def advanced_mode():
    """
    NOWA FUNKCJA: Tryb zaawansowany z dodatkowymi opcjami
    """
    print("\n" + "=" * 60)
    print("⚙️ TRYB ZAAWANSOWANY")
    print("=" * 60)

    try:
        num_accounts = int(input("Liczba kont do utworzenia (domyślnie 1): ") or "1")
        max_retries = int(input("Maksymalne próby na konto (domyślnie 3): ") or "3")

        debug_choice = input("Włączyć debugowanie? (t/N): ").lower()
        enable_debugging = debug_choice in ['t', 'tak', 'true', 'y', 'yes']

        print(f"\n🔧 Konfiguracja:")
        print(f"   Liczba kont: {num_accounts}")
        print(f"   Maksymalne próby: {max_retries}")
        print(f"   Debugowanie: {'Tak' if enable_debugging else 'Nie'}")

        confirm = input("\nRozpocząć? (T/n): ").lower()
        if confirm not in ['n', 'nie', 'no']:
            if num_accounts == 1:
                main(auto_mode=True, enable_debugging=enable_debugging)
            else:
                create_multiple_accounts(num_accounts, max_retries, enable_debugging)
        else:
            print("Anulowano.")

    except ValueError:
        print("❌ Nieprawidłowa wartość liczbowa")
    except KeyboardInterrupt:
        print("\n🛑 Przerwano przez użytkownika")


def interactive_menu():
    """
    NOWA FUNKCJA: Interaktywne menu wyboru trybu
    """
    while True:
        print("\n" + "=" * 60)
        print("🤖 BOT TWORZENIA KONT INTERIA")
        print("=" * 60)
        print("Wybierz tryb działania:")
        print("1. 📈 Tryb standardowy (1 konto)")
        print("2. 🔢 Tryb wielokrotny (wiele kont)")
        print("3. 🧪 Tryb testowy (sprawdzenie wykrywania błędów)")
        print("4. ⚙️ Tryb zaawansowany (własne ustawienia)")
        print("5. ❌ Wyjście")
        print("=" * 60)

        try:
            choice = input("Wybierz opcję (1-5): ").strip()

            if choice == "1":
                main(auto_mode=False, enable_debugging=False)
                break
            elif choice == "2":
                try:
                    num = int(input("Ile kont utworzyć? ") or "3")
                    create_multiple_accounts(num, max_retries_per_account=3)
                except ValueError:
                    print("❌ Nieprawidłowa liczba")
                    continue
                break
            elif choice == "3":
                test_mode()
                break
            elif choice == "4":
                advanced_mode()
                break
            elif choice == "5":
                print("👋 Do widzenia!")
                break
            else:
                print("❌ Nieprawidłowy wybór. Spróbuj ponownie.")

        except KeyboardInterrupt:
            print("\n🛑 Przerwano przez użytkownika")
            break
        except Exception as e:
            print(f"❌ Błąd: {e}")


if __name__ == "__main__":
    try:
        # Sprawdź argumenty linii poleceń
        import sys

        if len(sys.argv) > 1:
            mode = sys.argv[1].lower()

            if mode == "test":
                test_mode()
            elif mode == "auto":
                num_accounts = int(sys.argv[2]) if len(sys.argv) > 2 else 3
                create_multiple_accounts(num_accounts, max_retries_per_account=3)
            elif mode == "single":
                main(auto_mode=False, enable_debugging=False)
            elif mode == "debug":
                main(auto_mode=False, enable_debugging=True)
            else:
                print(f"❌ Nieznany tryb: {mode}")
                print("Dostępne tryby: test, auto, single, debug")
        else:
            # Brak argumentów - pokaż interaktywne menu
            interactive_menu()

    except KeyboardInterrupt:
        print("\n🛑 Program przerwany przez użytkownika")
    except Exception as e:
        logger.error(f"❌ Krytyczny błąd programu: {e}")
        logger.error(traceback.format_exc())
        input("Naciśnij Enter aby zakończyć...")