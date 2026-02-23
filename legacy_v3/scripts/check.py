import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    print("❌ Error: No se encontró la API KEY en el archivo .env")
else:
    genai.configure(api_key=api_key)
    print("🔍 Conectando a Google... Estos son tus modelos disponibles:")
    try:
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                print(f"   ✅ {m.name}")
    except Exception as e:
        print(f"❌ Error de conexión: {e}")