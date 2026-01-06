# src/storage_manager.py
import datetime
from typing import Optional, Any
from src.models import UserIdentity
from src.logger_config import logger


class StorageManager:
    def __init__(self, filepath: str = "konta_interia.txt"):
        self.filepath = filepath

    def save_account(self, identity: UserIdentity, lock: Optional[Any] = None) -> None:
        """
        Zapisuje utworzone konto do pliku tekstowego (format: email | hasło | dane | data).
        Obsługuje dynamiczne domeny (interia.pl, interia.eu, poczta.fm).
        """
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # POBIERANIE DOMENY: Jeśli 'domain' nie istnieje w identity, użyj domyślnej 'interia.pl'
        # To kluczowa poprawka, aby obsługiwać rotację domen z RegistrationPage.
        domain = identity.get("domain", "interia.pl")  # type: ignore (Dla TypedDict bez klucza domain)

        full_email = f"{identity['login']}@{domain}"

        # Format linii wyjściowej
        line = f"{full_email} | {identity['password']} | {identity['first_name']} {identity['last_name']} | {timestamp}\n"

        try:
            # Sekcja krytyczna zapisu do pliku
            if lock:
                lock.acquire()
            try:
                with open(self.filepath, "a", encoding="utf-8") as f:
                    f.write(line)
                logger.info(f"💾 [STORAGE] Zapisano konto: {full_email}")
            finally:
                if lock:
                    lock.release()
        except OSError as e:
            logger.error(f"❌ [STORAGE ERROR] Nie udało się zapisać konta {full_email}: {e}")