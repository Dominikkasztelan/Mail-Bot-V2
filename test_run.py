import random
import datetime
import os
import time
# ZMIANA: Dodano typy do obsługi Locka (Any, Optional)
from typing import Any, Optional
from playwright.sync_api import sync_playwright, ViewportSize
from faker import Faker

from src.registration_page import RegistrationPage
from src.config import USER_AGENTS, VIEWPORTS, GENERATOR_CONFIG
from src.models import UserIdentity
from src.logger_config import logger
# ZMIANA: Usunięto nieużywany import ElementNotFoundError
from src.exceptions import CaptchaSolveError, RegistrationFailedError


# ZMIANA: Typowanie 'lock: Optional[Any]' naprawia błąd IDE
def check_local_duplicates(login: str, lock: Optional[Any] = None) -> bool:
    """
    Sprawdza, czy dany login nie istnieje już w pliku wynikowym.
    Używa Locka do bezpiecznego odczytu, jeśli jest podany.
    """
    filename = "konta_interia.txt"
    if not os.path.exists(filename):
        return False

    try:
        # Jeśli mamy blokadę, używamy jej. Jeśli nie (test run), czytamy normalnie.
        if lock:
            lock.acquire()

        try:
            with open(filename, "r", encoding="utf-8") as f:
                for line in f:
                    if f"{login}@interia.pl" in line:
                        return True
        finally:
            if lock:
                lock.release()

    # ZMIANA: Konkretny wyjątek zamiast ogólnego Exception
    except OSError as e:
        logger.error(f"⚠️ Błąd odczytu bazy kont: {e}")

    return False


# ZMIANA: Typowanie 'lock: Optional[Any]'
def generate_identity(lock: Optional[Any] = None) -> UserIdentity:
    fake = Faker(GENERATOR_CONFIG["LOCALE"])

    first_name = fake.first_name_male()
    last_name = fake.last_name_male()
    year = str(random.randint(GENERATOR_CONFIG["YEAR_MIN"], GENERATOR_CONFIG["YEAR_MAX"]))
    day = str(random.randint(1, 28))
    months = ["Styczeń", "Luty", "Marzec", "Kwiecień", "Maj", "Czerwiec",
              "Lipiec", "Sierpień", "Wrzesień", "Październik", "Listopad", "Grudzień"]

    def clean(s: str) -> str:
        return s.lower().replace('ł', 'l').replace('ś', 's').replace('ą', 'a').replace('ż', 'z').replace('ź',
                                                                                                         'z').replace(
            'ć', 'c').replace('ń', 'n').replace('ó', 'o').replace('ę', 'e')

    for _ in range(100):
        random_suffix = random.randint(100, 9999)
        login_candidate = f"{clean(first_name)}.{clean(last_name)}.{random_suffix}"

        if not check_local_duplicates(login_candidate, lock):
            return {
                "first_name": first_name,
                "last_name": last_name,
                "birth_day": day,
                "birth_month_name": random.choice(months),
                "birth_year": year,
                "password": str(GENERATOR_CONFIG["PASSWORD_DEFAULT"]),
                "login": login_candidate
            }

    logger.warning("⚠️ Nie udało się wylosować unikalnego loginu lokalnie po 100 próbach.")
    return {
        "first_name": first_name,
        "last_name": last_name,
        "birth_day": day,
        "birth_month_name": random.choice(months),
        "birth_year": year,
        "password": str(GENERATOR_CONFIG["PASSWORD_DEFAULT"]),
        "login": f"{clean(first_name)}.{clean(last_name)}.{random.randint(10000, 99999)}"
    }


# ZMIANA: Typowanie 'lock: Optional[Any]'
def save_credentials(identity: UserIdentity, lock: Optional[Any] = None) -> None:
    filename = "konta_interia.txt"
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"{identity['login']}@interia.pl | {identity['password']} | {identity['first_name']} {identity['last_name']} | {timestamp}\n"

    try:
        # CRITICAL: Sekcja krytyczna. Tylko jeden proces na raz może pisać do pliku.
        if lock:
            lock.acquire()

        try:
            with open(filename, "a", encoding="utf-8") as f:
                f.write(line)
            logger.info(f"💾 [ZAPIS] Zapisano: {identity['login']}")
        finally:
            if lock:
                lock.release()

    # ZMIANA: Konkretny wyjątek OSError (błędy zapisu/pliku) zamiast Exception
    except OSError as e:
        logger.error(f"❌ [BŁĄD ZAPISU] {e}")


# ZMIANA: Typowanie 'file_lock: Any' (Lock jest tutaj wymagany, więc nie Optional)
def run_worker(instance_id: int, file_lock: Any) -> None:
    """
    Funkcja workera - to ona jest uruchamiana w osobnym procesie.
    """
    # Opóźnienie startu, żeby nie odpaliły się idealnie w tej samej milisekundzie (API rate limit)
    time.sleep(instance_id * 2.5)

    prefix = f"[Worker-{instance_id}]"
    logger.info(f"{prefix} 🚀 Startuje proces przeglądarki...")

    selected_ua = random.choice(USER_AGENTS)
    vp = random.choice(VIEWPORTS)

    # Przekazujemy Locka do generatora
    identity = generate_identity(file_lock)

    logger.info(f"{prefix} 🎭 Tożsamość: {identity['first_name']} (Login: {identity['login']})")

    with sync_playwright() as p:
        browser = p.chromium.launch(
            channel="chrome",
            headless=False,  # Zmień na True, jeśli nie chcesz widzieć okien
            args=["--disable-blink-features=AutomationControlled"],
            ignore_default_args=["--enable-automation"]
        )

        current_viewport: ViewportSize = {"width": vp["width"], "height": vp["height"]}

        context = browser.new_context(
            user_agent=selected_ua,
            viewport=current_viewport,
            device_scale_factor=vp["scale"],
            locale="pl-PL",
            timezone_id="Europe/Warsaw"
        )
        context.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

        page = context.new_page()
        bot = RegistrationPage(page)

        try:
            bot.load()
            bot.fill_form(identity)
            bot.accept_terms()
            bot.submit()

            if bot.verify_success():
                logger.info(f"{prefix} ✅ SUKCES!")
                # Zapisujemy bezpiecznie z użyciem blokady
                save_credentials(identity, file_lock)

                wait_time = random.uniform(4.0, 11.0)
                logger.info(f"{prefix} 👀 Czekam {wait_time:.1f}s...")
                page.wait_for_timeout(wait_time * 1000)
            else:
                logger.error(f"{prefix} ❌ Niepowodzenie weryfikacji.")
                page.screenshot(path=f"logs/error_worker_{instance_id}.png")

        except CaptchaSolveError:
            logger.critical(f"{prefix} 🤖 Captcha Error.")
        except RegistrationFailedError as e:
            logger.error(f"{prefix} ⛔ {e}")
        except Exception as e:
            # Tutaj Exception jest celowe (Global Safety Net) - łapie wszystko, co nieprzewidziane.
            logger.critical(f"{prefix} 💥 Krytyczny błąd procesu: {e}")
            try:
                page.screenshot(path=f"logs/crash_worker_{instance_id}.png")
            except Exception:
                pass
        finally:
            logger.info(f"{prefix} ⏸️ Koniec pracy.")


if __name__ == "__main__":
    # To pozwala uruchomić test_run.py pojedynczo jak dawniej (dla testów)
    print("⚠️ Uruchamiasz tryb pojedynczy. Użyj 'launcher.py' do wielu okien.")
    # Atrapa locka dla trybu pojedynczego
    from multiprocessing import Lock as MpLock

    dummy_lock = MpLock()
    run_worker(1, dummy_lock)