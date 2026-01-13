# src/identity_manager.py
import os
import random
from typing import Optional, Any
from faker import Faker
from src.config import GENERATOR_CONFIG
from src.models import UserIdentity


class IdentityManager:
    def __init__(self, db_path: str = "konta_interia.txt"):
        self.db_path = db_path
        self.fake = Faker(GENERATOR_CONFIG["LOCALE"])

    def check_duplicates(self, login: str, lock: Optional[Any] = None) -> bool:
        """
        Sprawdza czy dany login już istnieje w pliku bazy danych.
        Ignoruje domenę przy sprawdzaniu (sprawdza tylko prefix).
        """
        if not os.path.exists(self.db_path):
            return False
        try:
            if lock: lock.acquire()
            try:
                with open(self.db_path, "r", encoding="utf-8") as f:
                    for line in f:
                        # Sprawdzamy czy login występuje w linii (proste i skuteczne)
                        if f"{login}@" in line:
                            return True
            finally:
                if lock: lock.release()
        except OSError:
            pass
        return False

    def generate(self, lock: Optional[Any] = None) -> UserIdentity:
        """
        Generuje nową, unikalną tożsamość użytkownika.
        Zwraca obiekt zgodny ze strukturą UserIdentity.
        """
        first_name = self.fake.first_name_male()
        last_name = self.fake.last_name_male()
        year = str(random.randint(GENERATOR_CONFIG["YEAR_MIN"], GENERATOR_CONFIG["YEAR_MAX"]))
        day = str(random.randint(1, 28))
        months = ["Styczeń", "Luty", "Marzec", "Kwiecień", "Maj", "Czerwiec",
                  "Lipiec", "Sierpień", "Wrzesień", "Październik", "Listopad", "Grudzień"]

        def clean(s: str) -> str:
            """Usuwa polskie znaki i formatuje pod login."""
            return s.lower().replace('ł', 'l').replace('ś', 's').replace('ą', 'a').replace('ż', 'z').replace('ź',
                                                                                                             'z').replace(
                'ć', 'c').replace('ń', 'n').replace('ó', 'o').replace('ę', 'e')

        # Próba wygenerowania unikalnego loginu (do 100 prób)
        for _ in range(100):
            suffix = random.randint(100, 9999)
            login = f"{clean(first_name)}.{clean(last_name)}.{suffix}"

            if not self.check_duplicates(login, lock):
                return {
                    "first_name": first_name,
                    "last_name": last_name,
                    "birth_day": day,
                    "birth_month_name": random.choice(months),
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
            "birth_month_name": random.choice(months),
            "birth_year": year,
            "password": str(GENERATOR_CONFIG["PASSWORD_DEFAULT"]),
            "login": f"{clean(first_name)}.{clean(last_name)}.{fallback_suffix}",
            "domain": ""  # <--- FIX
        }