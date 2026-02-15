"""
Test Gemini models to find which ones work with your API key
"""
import sys
from google import genai
from google.genai import types
from dotenv import load_dotenv
import os

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    print("❌ GEMINI_API_KEY not found in .env")
    sys.exit(1)

print("=" * 70)
print("  Gemini Model Availability Test")
print("=" * 70)
print(f"\nAPI Key: {API_KEY[:8]}...{API_KEY[-4:]}")
print("\nTesting models...\n")

# Models to test
models_to_test = [
    # Experimental models (high free tier quota)
    "models/gemini-2.0-flash-exp",
    "models/gemini-exp-1206",
    "models/gemini-2.0-flash-thinking-exp-1219",

    # Latest stable
    "models/gemini-flash-latest",

    # 2.5 generation
    "models/gemini-2.5-flash",
    "models/gemini-2.5-pro",

    # 2.0 generation
    "models/gemini-2.0-flash",

    # Legacy
    "models/gemini-pro",
]

client = genai.Client(api_key=API_KEY)
working_models = []
failed_models = []

for model_name in models_to_test:
    try:
        print(f"Testing {model_name}...", end=" ")

        response = client.models.generate_content(
            model=model_name,
            contents="Say 'OK' if you can read this.",
            config=types.GenerateContentConfig(
                temperature=0.1,
                max_output_tokens=10
            )
        )

        text = (response.text or "").strip()

        if text:
            print(f"✅ WORKS - Response: {text[:50]}")
            working_models.append(model_name)
        else:
            print(f"⚠️  Empty response")
            failed_models.append((model_name, "Empty response"))

    except Exception as e:
        error_msg = str(e)[:80]
        print(f"❌ FAILED - {error_msg}")
        failed_models.append((model_name, error_msg))

print("\n" + "=" * 70)
print("  Results")
print("=" * 70)

print(f"\n✅ Working Models ({len(working_models)}):")
for model in working_models:
    print(f"   - {model}")

print(f"\n❌ Failed Models ({len(failed_models)}):")
for model, error in failed_models:
    print(f"   - {model}")
    print(f"     Error: {error[:60]}")

if working_models:
    print(f"\n🎯 Recommended Model: {working_models[0]}")
    print(f"   (This will be used as default with fallback to others)")
else:
    print("\n⚠️  No models working! Check your API key or quota.")

print("\n" + "=" * 70)
