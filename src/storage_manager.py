# src/storage_manager.py
import datetime
import os
from typing import Any

from src.logger_config import logger
from src.models import UserIdentity


class StorageManager:
    def __init__(self, filepath: str = "saved_accounts/konta.txt"):
        self.filepath = filepath

    def save_account(self, identity: UserIdentity, lock: Any | None = None) -> None:
        """
        Zapisuje utworzone konto do pliku tekstowego (format: email | hasło | dane | data).
        Obsługuje dynamiczne domeny (interia.pl, interia.eu, poczta.fm) przekazane z RegistrationPage.
        """
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # 1. POBIERANIE DOMENY
        # Teraz pobieramy domenę jawnie z obiektu identity.
        # Dzięki poprawce w registration_page.py, pole to powinno być zawsze wypełnione po sukcesie.
        domain = identity.get("domain")

        # Zabezpieczenie (Fallback) na wypadek niespójności danych
        if not domain:
            logger.warning(f"⚠️ [STORAGE] Brak domeny w identity dla loginu '{identity.get('login')}'. Używam domyślnej 'interia.pl'.")
            domain = "interia.pl"

        # 2. KONSTRUKCJA ADRESU EMAIL
        full_email = f"{identity['login']}@{domain}"

        # Format linii wyjściowej: EMAIL | HASŁO | IMIĘ NAZWISKO | DATA
        line = f"{full_email} | {identity['password']} | {identity['first_name']} {identity['last_name']} | {timestamp}\n"

        try:
            # Sekcja krytyczna zapisu do pliku (obsługa Locka z Multiprocessing)
            if lock:
                lock.acquire()
            try:
                # Otwieramy w trybie 'append' (dopisywanie) z kodowaniem UTF-8
                with open(self.filepath, "a", encoding="utf-8") as f:
                    f.write(line)
                    # flush() wymusza zapis bufora na dysk (ważne przy crashu)
                    f.flush()
                    os.fsync(f.fileno())

                logger.info(f"💾 [STORAGE] Zapisano konto: {full_email}")
            finally:
                if lock:
                    lock.release()

        except OSError as e:
            logger.error(f"❌ [STORAGE ERROR] Nie udało się zapisać konta {full_email}: {e}")
