import random
import datetime
from playwright.sync_api import sync_playwright
from faker import Faker

from src.registration_page import RegistrationPage
from src.config import USER_AGENTS, VIEWPORTS, GENERATOR_CONFIG
from src.models import UserIdentity
from src.logger_config import logger
from src.exceptions import ElementNotFoundError, CaptchaSolveError, RegistrationFailedError


def generate_identity() -> UserIdentity:
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

    login = f"{clean(first_name)}.{clean(last_name)}.{random.randint(100, 9999)}"

    return {
        "first_name": first_name,
        "last_name": last_name,
        "birth_day": day,
        "birth_month_name": random.choice(months),
        "birth_year": year,
        "password": str(GENERATOR_CONFIG["PASSWORD_DEFAULT"]),
        "login": login
    }


def save_credentials(identity: UserIdentity) -> None:
    filename = "konta_interia.txt"
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"{identity['login']}@interia.pl | {identity['password']} | {identity['first_name']} {identity['last_name']} | {timestamp}\n"
    try:
        with open(filename, "a", encoding="utf-8") as f:
            f.write(line)
        logger.info(f"💾 [ZAPIS] Zapisano: {identity['login']}")
    except Exception as e:
        logger.error(f"❌ [BŁĄD ZAPISU] {e}")


def run() -> None:
    selected_ua = random.choice(USER_AGENTS)
    vp = random.choice(VIEWPORTS)
    identity = generate_identity()

    logger.info(f"🎭 START - Nowa Tożsamość: {identity['first_name']} {identity['last_name']}")

    with sync_playwright() as p:
        browser = p.chromium.launch(
            channel="chrome",
            headless=False,
            args=["--disable-blink-features=AutomationControlled", "--start-maximized"],
            ignore_default_args=["--enable-automation"]
        )

        context = browser.new_context(
            user_agent=selected_ua,
            viewport={"width": vp["width"], "height": vp["height"]},
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

            # --- NOWA SEKCJA WERYFIKACJI I OPÓŹNIENIA ---
            if bot.verify_success():
                logger.info("✅ KONTO UTWORZONE I ZWERYFIKOWANE!")
                save_credentials(identity)

                # Oczekiwanie 4-11 sekund przed zamknięciem
                wait_time = random.uniform(4.0, 11.0)
                logger.info(f"👀 Oglądam skrzynkę przez {wait_time:.1f} sekund...")
                page.wait_for_timeout(wait_time * 1000)
            else:
                logger.error("❌ Formularz wysłany, ale nie wykryto wejścia do skrzynki.")
                page.screenshot(path="logs/error_final.png")

        # --- SEKCJA OBSŁUGI BŁĘDÓW ---
        except CaptchaSolveError:
            logger.critical("🤖 CRITICAL: Polegliśmy na Captchy. Zalecana zmiana IP!")
        except ElementNotFoundError as e:
            logger.error(f"🔍 BŁĄD STRONY: {e}. Interia mogła zmienić kod HTML.")
        except Exception as e:
            logger.critical(f"💥 BŁĄD NIEZNANY: {e}. Sprawdź logi.")
            page.screenshot(path="logs/error_exception.png")
        finally:
            logger.info("⏸️ Zamykanie sesji...")
            # Tutaj kontekst 'with' automatycznie zamknie przeglądarkę


if __name__ == "__main__":
    run()