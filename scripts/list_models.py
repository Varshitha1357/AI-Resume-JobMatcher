import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))

models = genai.list_models()
print("\nAvailable models that support generateContent:")
print("-" * 80)
for m in models:
    if 'generateContent' in m.supported_generation_methods:
        print(f"Name: {m.name}")
        print(f"Display: {m.display_name}")
        print(f"Description: {m.description}")
        print("-" * 80)
