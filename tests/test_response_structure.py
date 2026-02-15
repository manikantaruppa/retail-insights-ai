"""
Understand the actual response structure
"""
from google import genai
from google.genai import types
from dotenv import load_dotenv
import os
import json

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=API_KEY)

print("=" * 70)
print("  Response Structure Analysis")
print("=" * 70)

model_name = "models/gemini-2.5-flash"
prompt = "What is 2+2? Answer with just the number."

print(f"\nModel: {model_name}")
print(f"Prompt: {prompt}")
print("\n" + "=" * 70)

response = client.models.generate_content(
    model=model_name,
    contents=prompt,
    config=types.GenerateContentConfig(temperature=0, max_output_tokens=50)
)

print("\n📦 Response Object:")
print(f"Type: {type(response)}")
print(f"\nAttributes: {dir(response)}")

print("\n" + "=" * 70)
print("Trying Different Access Methods:")
print("=" * 70)

# Method 1: .text
print(f"\n1. response.text = {response.text}")
print(f"   Type: {type(response.text)}")

# Method 2: Check candidates
if hasattr(response, 'candidates'):
    print(f"\n2. response.candidates:")
    for i, candidate in enumerate(response.candidates):
        print(f"   Candidate {i}: {candidate}")
        if hasattr(candidate, 'content'):
            print(f"   Content: {candidate.content}")
            if hasattr(candidate.content, 'parts'):
                print(f"   Parts: {candidate.content.parts}")
                for j, part in enumerate(candidate.content.parts):
                    print(f"     Part {j}: {part}")
                    if hasattr(part, 'text'):
                        print(f"     ✅ FOUND TEXT: '{part.text}'")

# Method 3: Check usage
if hasattr(response, 'usage_metadata'):
    print(f"\n3. response.usage_metadata:")
    print(f"   {response.usage_metadata}")

# Method 4: Try __dict__
if hasattr(response, '__dict__'):
    print(f"\n4. response.__dict__:")
    print(json.dumps(str(response.__dict__), indent=2)[:500])

print("\n" + "=" * 70)
print("Correct Way to Extract Text:")
print("=" * 70)

def extract_text(response):
    """Extract text from Gemini response"""
    # Try method 1: Direct text attribute
    if hasattr(response, 'text') and response.text:
        return response.text

    # Try method 2: Through candidates
    if hasattr(response, 'candidates') and response.candidates:
        for candidate in response.candidates:
            if hasattr(candidate, 'content') and hasattr(candidate.content, 'parts'):
                for part in candidate.content.parts:
                    if hasattr(part, 'text') and part.text:
                        return part.text

    return None

text = extract_text(response)
print(f"\n✅ Extracted text: '{text}'")
print(f"   Type: {type(text)}")
print(f"   Length: {len(text) if text else 0}")

print("\n" + "=" * 70)
