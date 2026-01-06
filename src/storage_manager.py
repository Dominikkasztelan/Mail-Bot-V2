# src/storage_manager.py
import datetime
from typing import Optional, Any
from src.models import UserIdentity
from src.logger_config import logger

class StorageManager:
    def __init__(self, filepath: str = "konta_interia.txt"):
        self.filepath = filepath

    def save_account(self, identity: UserIdentity, lock: Optional[Any] = None) -> None:
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        line = f"{identity['login']}@interia.pl | {identity['password']} | {identity['first_name']} {identity['last_name']} | {timestamp}\n"

        try:
            if lock: lock.acquire()
            try:
                with open(self.filepath, "a", encoding="utf-8") as f:
                    f.write(line)
                logger.info(f"💾 [STORAGE] Zapisano konto: {identity['login']}")
            finally:
                if lock: lock.release()
        except OSError as e:
            logger.error(f"❌ [STORAGE ERROR] {e}")