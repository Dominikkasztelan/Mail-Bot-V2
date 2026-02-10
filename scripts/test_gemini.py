import os
import sys

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from google import genai

from src.config import API_KEYS


def test_gemini():
    print("Testing Gemini API...")
    keys = API_KEYS.get("GEMINI", [])
    if not keys:
        print("❌ No API keys found.")
        return

    key = keys[0]
    print(f"🔑 Using key: {key[:5]}...{key[-5:]}")

    client = genai.Client(api_key=key)

    try:
        # List models
        print("Listing models...")
        # Note: The new SDK syntax for listing models might differ, trying standard approach
        # or just trying a different model name 'gemini-pro' as fallback in next step.
        # But let's try to print error details more clearly.

        # client.models.list() is not always direct in new SDK?
        # Let's try to just Try 'gemini-1.5-pro' instead.

        response = client.models.generate_content(
            model="gemini-2.0-flash-exp", # Try the experimental one often available
            contents="Hello",
        )
        print(f"✅ Response: {response.text}")
    except Exception as e:
        print(f"❌ Error with gemini-2.0-flash-exp: {e}")

        try:
             # Try old reliable
             response = client.models.generate_content(
                model="gemini-1.0-pro",
                contents="Hello",
             )
             print(f"✅ Response 1.0 diff: {response.text}")
        except Exception as e2:
             print(f"❌ Error with gemini-1.0-pro: {e2}")

if __name__ == "__main__":
    test_gemini()
