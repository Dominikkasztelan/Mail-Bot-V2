import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import google.generativeai as genai

from src.config import API_KEYS

key = API_KEYS["GEMINI"][0]
genai.configure(api_key=key)

models_to_test = [
    "gemini-pro",
    "gemini-1.5-pro",
    "gemini-1.5-flash",
    "gemini-1.5-flash-latest",
    "models/gemini-pro",
    "models/gemini-1.5-flash"
]

print("Testing models:")
for model_name in models_to_test:
    try:
        model = genai.GenerativeModel(model_name)
        response = model.generate_content("Say OK")
        print(f"✅ {model_name}: {response.text[:20]}")
        break  # Stop at first success
    except Exception as e:
        print(f"❌ {model_name}: {str(e)[:50]}")
