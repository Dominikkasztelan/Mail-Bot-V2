import requests
import time

print("🔍 Testowanie połączenia z Google Gemini API...")
url = "https://generativelanguage.googleapis.com"

try:
    start = time.time()
    response = requests.get(url, timeout=5)
    ping = (time.time() - start) * 1000
    print(f"✅ Połączenie OK! Ping: {ping:.0f} ms")
    print(f"Status kod: {response.status_code} (To normalne dla GET na główny adres)")
except Exception as e:
    print(f"❌ BŁĄD SIECIOWY: {e}")