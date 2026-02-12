import asyncio

import httpx
from loguru import logger

# Configuration
API_URL = "http://localhost:8000/auth/login"
TEST_EMAIL = "twoj_email@example.com"
TEST_PASSWORD = "twoje_haslo"

async def run_demo() -> None:
    logger.info(f"🚀 Wysyłam żądanie logowania do {API_URL}...")

    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            response = await client.post(API_URL, json={
                "strategy": "email",
                "email": TEST_EMAIL,
                "password": TEST_PASSWORD
            })

            if response.status_code == 200:
                data = response.json()
                logger.success(f"✅ SUKCES! Zalogowano jako: {data['email']}")
                logger.info(f"🍪 Otrzymane ciasteczka: {str(data['cookies'])[:100]}...")
            else:
                logger.error(f"❌ Błąd serwera: {response.text}")

        except httpx.ConnectError:
            logger.error(
                "❌ Nie można połączyć z serwerem. "
                "Upewnij się, że uruchomiłeś 'python -m src.main' w innym oknie!"
            )

if __name__ == "__main__":
    print("--- DEMO LOGOWANIA LEONARDO.AI ---")
    print("1. Upewnij się, że w drugim terminalu działa: python -m src.main")
    print("2. Edytuj ten plik i wpisz prawdziwe dane logowania (linie 7-8).")
    print("----------------------------------")
    asyncio.run(run_demo())
