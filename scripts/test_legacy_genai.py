import os
import sys

# Add project root
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import google.generativeai as genai

from src.config import API_KEYS


def test_legacy_lib():
    print("Testing google-generativeai lib...")
    keys = API_KEYS.get("GEMINI", [])
    if not keys:
        print("No keys")
        return

    key = keys[0]
    genai.configure(api_key=key)

    try:
        print("Available models:")
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                print(f" - {m.name}")

        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content("Hello")
        print(f"✅ Success! Response: {response.text}")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_legacy_lib()
