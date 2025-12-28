import random
import string

# Importuj logger z odpowiedniego modułu
from src.logger_config import get_logger

logger = get_logger(__name__)


def generate_random_data():
    """Generuje losowe dane do formularza"""
    first_name = "Test" + ''.join(random.choice(string.ascii_lowercase) for i in range(5))
    last_name = "User" + ''.join(random.choice(string.ascii_lowercase) for i in range(5))
    username = first_name.lower() + ''.join(random.choice(string.digits) for i in range(3))

    # Ograniczamy dni do 28, aby formularz akceptował każdą kombinację dnia i miesiąca
    # Wszystkie miesiące mają co najmniej 28 dni, więc ta wartość jest bezpieczna
    day = str(random.randint(1, 28))
    month = random.randint(1, 12)
    year = str(random.randint(1970, 2000))

    # Tworzymy silne hasło zawierające małe i duże litery, cyfry oraz znaki specjalne
    password = ''.join(random.choice(string.ascii_letters + string.digits + "!@#$%^&*") for i in range(12))

    # Przygotuj dane w formie słownika
    data = {
        "first_name": first_name,
        "last_name": last_name,
        "username": username,
        "day": day,
        "month": month,
        "year": year,
        "password": password
    }

    # Logowanie (bez hasła, ze względów bezpieczeństwa)
    safe_data = data.copy()
    safe_data["password"] = "*****"  # Maskowanie hasła w logach
    logger.debug(f"Wygenerowano dane: {safe_data}")

    return data