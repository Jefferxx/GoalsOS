import os
from groq import Groq
from dotenv import load_dotenv

# Cargar variables de entorno para leer la API Key
load_dotenv()

def list_groq_models():
    api_key = os.getenv("GROQ_API_KEY")
    
    if not api_key:
        print("❌ ERROR: No encontré la variable GROQ_API_KEY en tu archivo .env")
        print("   -> Asegúrate de haberla guardado en el archivo .env")
        return

    try:
        print("📡 Conectando a Groq para pedir el catálogo de modelos...")
        client = Groq(api_key=api_key)
        
        # Hacemos la llamada a la API para listar modelos
        models = client.models.list()
        
        print("\n✅ LISTADO OFICIAL DE MODELOS ACTIVOS EN GROQ:")
        print("==============================================")
        
        available_models = []
        for model in models.data:
            print(f"🔹 ID: {model.id}")
            available_models.append(model.id)
            
        print("==============================================")
        
        # Recomendación automática
        print("\n🧐 ANÁLISIS DE MEJOR OPCIÓN:")
        
        priorities = [
            "llama-3.3-70b-versatile", # La joya actual (Más inteligente)
            "llama-3.1-70b-versatile", # La versión estable anterior
            "llama3-70b-8192",         # (El que falló, probablemente ya no salga)
            "mixtral-8x7b-32768"       # Alternativa rápida de Mistral
        ]
        
        found = False
        for p in priorities:
            if p in available_models:
                print(f"🌟 TE RECOMIENDO USAR: '{p}'")
                print("   -> Es el más potente y estable de tu lista actual.")
                found = True
                break
        
        if not found:
            print("⚠️ No encontré mis favoritos. Elige cualquiera de la lista de arriba que termine en '70b' o 'versatile'.")

    except Exception as e:
        print(f"\n❌ Error conectando con Groq: {e}")
        print("   -> Verifica que tu API Key sea correcta y empiece con 'gsk_'")

if __name__ == "__main__":
    list_groq_models()