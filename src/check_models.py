import os
from google import genai
from dotenv import load_dotenv

# Ładujemy klucz z .env
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    print("❌ BŁĄD: Nie znaleziono klucza w pliku .env!")
    exit()

print(f"🔑 Używam klucza: {api_key[:5]}...*****")

try:
    client = genai.Client(api_key=api_key)
    print("\n🔍 Łączę się z Google API...")

    # Pobieramy listę modeli
    models = client.models.list()

    print("\n✅ LISTA DOSTĘPNYCH MODELI:")
    print("=" * 50)

    count = 0
    for m in models:
        # Wypisujemy po prostu nazwę (name) - to pole musi istnieć
        print(f"👉 {m.name}")
        count += 1

    if count == 0:
        print("⚠️ Lista modeli jest pusta. Sprawdź czy klucz API ma uprawnienia.")

except Exception as e:
    print(f"\n❌ BŁĄD: {e}")
    # Dla debugowania wypiszmy, co dokładnie zwraca biblioteka, jeśli coś pójdzie nie tak
    try:
        print(f"Szczegóły obiektu: {dir(models)}")
    except:
        pass