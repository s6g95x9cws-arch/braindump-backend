import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
print(f"API Key found: {api_key[:5]}...{api_key[-5:] if api_key else 'None'}")

try:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')
    print("Sending request to Gemini...")
    response = model.generate_content("Hello, can you hear me?")
    print("Response received!")
    print(response.text)
except Exception as e:
    print(f"Error: {e}")
