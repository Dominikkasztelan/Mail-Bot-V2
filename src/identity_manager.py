# src/identity_manager.py
import os
import random
from typing import Any

from faker import Faker

from src.config import GENERATOR_CONFIG, POLISH_MONTHS, RETRY_LIMITS
from src.models import UserIdentity
from src.utils import clean_polish_chars


class IdentityManager:
    def __init__(self, db_path: str = "konta_interia.txt"):
        self.db_path = db_path
        self.fake = Faker(GENERATOR_CONFIG["LOCALE"])

    def check_duplicates(self, login: str, lock: Any | None = None) -> bool:
        """
        Sprawdza czy dany login już istnieje w pliku bazy danych.
        Ignoruje domenę przy sprawdzaniu (sprawdza tylko prefix).
        """
        if not os.path.exists(self.db_path):
            return False
        try:
            if lock: lock.acquire()
            try:
                with open(self.db_path, encoding="utf-8") as f:
                    for line in f:
                        # Sprawdzamy czy login występuje w linii (proste i skuteczne)
                        if f"{login}@" in line:
                            return True
            finally:
                if lock: lock.release()
        except OSError:
            pass
        return False

    def generate(self, lock: Any | None = None) -> UserIdentity:
        """
        Generuje nową, unikalną tożsamość użytkownika.
        Zwraca obiekt zgodny ze strukturą UserIdentity.
        """
        first_name = self.fake.first_name_male()
        last_name = self.fake.last_name_male()
        year = str(random.randint(GENERATOR_CONFIG["YEAR_MIN"], GENERATOR_CONFIG["YEAR_MAX"]))
        day = str(random.randint(1, 28))

        # Próba wygenerowania unikalnego loginu (do limitu z configu)
        for _ in range(RETRY_LIMITS["IDENTITY_GENERATION"]):
            suffix = random.randint(100, 9999)
            login = f"{clean_polish_chars(first_name)}.{clean_polish_chars(last_name)}.{suffix}"

            if not self.check_duplicates(login, lock):
                return {
                    "first_name": first_name,
                    "last_name": last_name,
                    "birth_day": day,
                    "birth_month_name": random.choice(POLISH_MONTHS),
                    "birth_year": year,
                    "password": str(GENERATOR_CONFIG["PASSWORD_DEFAULT"]),
                    "login": login,
                    "domain": ""  # <--- FIX: Inicjalizacja pustą domeną (będzie wypełniona w RegistrationPage)
                }

        # Fallback (bardzo rzadki przypadek, gdyby 100 losowań zawiodło)
        fallback_suffix = random.randint(10000, 99999)
        return {
            "first_name": first_name,
            "last_name": last_name,
            "birth_day": day,
            "birth_month_name": random.choice(POLISH_MONTHS),
            "birth_year": year,
            "password": str(GENERATOR_CONFIG["PASSWORD_DEFAULT"]),
            "login": f"{clean_polish_chars(first_name)}.{clean_polish_chars(last_name)}.{fallback_suffix}",
            "domain": ""  # <--- FIX
        }
