#!/usr/bin/env python3
"""
Comprehensive Gemini API diagnostics.
Tests multiple SDK versions and model names to find working configuration.
"""
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.config import API_KEYS


def test_google_generativeai():
    """Test with google-generativeai library."""
    print("\n" + "="*60)
    print("Testing google-generativeai SDK")
    print("="*60)

    try:
        import google.generativeai as genai  # noqa: PLC0415

        keys = API_KEYS.get("GEMINI", [])
        if not keys:
            print("❌ No API keys found")
            return False

        key = keys[0]
        print(f"🔑 Using key: {key[:10]}...{key[-5:]}")

        genai.configure(api_key=key)

        # Try to list models
        print("\n📋 Attempting to list available models...")
        try:
            models = list(genai.list_models())
            print(f"✅ Found {len(models)} models:")
            for m in models[:5]:  # Show first 5
                print(f"  - {m.name}")
                if hasattr(m, 'supported_generation_methods'):
                    print(f"    Methods: {m.supported_generation_methods}")
            return True
        except Exception as e:
            print(f"❌ Failed to list models: {e}")

        # Try common model names
        model_names = [
            "gemini-pro",
            "gemini-1.0-pro",
            "gemini-1.5-pro",
            "gemini-1.5-flash",
            "models/gemini-pro",
            "models/gemini-1.5-flash"
        ]

        print("\n🔍 Testing common model names...")
        for model_name in model_names:
            try:
                print(f"\nTrying: {model_name}")
                model = genai.GenerativeModel(model_name)
                response = model.generate_content("Say 'OK' if you work")
                print(f"  ✅ SUCCESS! Response: {response.text[:50]}")
                return True
            except Exception as e:
                error_msg = str(e)
                if "404" in error_msg:
                    print("  ❌ 404 Not Found")
                elif "403" in error_msg:
                    print("  ❌ 403 Forbidden (API key issue)")
                else:
                    print(f"  ❌ {error_msg[:100]}")

    except ImportError:
        print("❌ google-generativeai not installed")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

    return False

def test_google_genai():
    """Test with google.genai library."""
    print("\n" + "="*60)
    print("Testing google-genai SDK")
    print("="*60)

    try:
        from google import genai  # noqa: PLC0415, F401
        from google.genai import types  # noqa: PLC0415, F401

        keys = API_KEYS.get("GEMINI", [])
        if not keys:
            print("❌ No API keys found")
            return False

        key = keys[0]
        print(f"🔑 Using key: {key[:10]}...{key[-5:]}")

        client = genai.Client(api_key=key)

        # Try common model names
        model_names = [
            "gemini-2.0-flash-exp",
            "gemini-1.5-flash",
            "gemini-1.5-pro",
            "gemini-pro",
        ]

        print("\n🔍 Testing model names...")
        for model_name in model_names:
            try:
                print(f"\nTrying: {model_name}")
                response = client.models.generate_content(
                    model=model_name,
                    contents="Say 'OK'"
                )
                print(f"  ✅ SUCCESS! Response: {response.text[:50]}")
                return True
            except Exception as e:
                error_msg = str(e)
                if "404" in error_msg or "NOT_FOUND" in error_msg:
                    print("  ❌ 404 Not Found")
                elif "403" in error_msg or "PERMISSION" in error_msg:
                    print("  ❌ 403 Permission Denied")
                else:
                    print(f"  ❌ {error_msg[:100]}")

    except ImportError:
        print("❌ google-genai not installed")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

    return False

def check_api_key_validity():
    """Check if API keys look valid."""
    print("\n" + "="*60)
    print("API Key Validation")
    print("="*60)

    keys = API_KEYS.get("GEMINI", [])
    print(f"Found {len(keys)} API key(s)")

    for i, key in enumerate(keys, 1):
        print(f"\nKey {i}:")
        print(f"  Length: {len(key)} chars")
        print(f"  Prefix: {key[:10]}...")
        print(f"  Suffix: ...{key[-5:]}")
        print(f"  Starts with 'AIza': {'✅' if key.startswith('AIza') else '❌'}")

def main():
    print("🔍 Gemini API Diagnostics")
    print("="*60)

    check_api_key_validity()

    # Test both SDKs
    success1 = test_google_generativeai()
    success2 = test_google_genai()

    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    if success1 or success2:
        print("✅ At least one SDK configuration works!")
    else:
        print("❌ No working configuration found.")
        print("\nPossible issues:")
        print("  1. API keys may be invalid or expired")
        print("  2. API keys may not have Gemini API enabled")
        print("  3. Billing may not be set up")
        print("\nNext steps:")
        print("  1. Visit https://aistudio.google.com/app/apikey")
        print("  2. Check if keys are valid")
        print("  3. Ensure Gemini API is enabled in Google Cloud Console")

if __name__ == "__main__":
    main()
