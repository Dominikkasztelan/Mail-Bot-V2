# scripts/test_net.py
"""
Network connectivity test for Google Gemini API.
"""
import time

from src.logger_config import get_logger

logger = get_logger("TestNet")

try:
    import requests
except ImportError:
    logger.error("❌ Module 'requests' not installed. Run: pip install requests")
    exit(1)


def test_gemini_connection() -> None:
    """Tests connection to Google Generative Language API endpoint."""
    logger.info("🔍 Testowanie połączenia z Google Gemini API...")
    url = "https://generativelanguage.googleapis.com"

    try:
        start = time.time()
        response = requests.get(url, timeout=5)
        ping = (time.time() - start) * 1000
        logger.info(f"✅ Połączenie OK! Ping: {ping:.0f} ms")
        logger.info(f"Status kod: {response.status_code} (To normalne dla GET na główny adres)")
    except requests.exceptions.Timeout:
        logger.error("❌ BŁĄD: Timeout połączenia (5s)")
    except requests.exceptions.ConnectionError as e:
        logger.error(f"❌ BŁĄD SIECIOWY: Brak połączenia z internetem - {e}")
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ BŁĄD SIECIOWY: {e}")


if __name__ == "__main__":
    test_gemini_connection()
