import os
import google.generativeai as genai

# NO usamos load_dotenv. Confiamos en las variables inyectadas por Docker Compose.
api_key = os.getenv("GOOGLE_API_KEY")

print("🔍 Diagnóstico de Variables de Entorno:")
if not api_key:
    print("❌ CRÍTICO: La variable GOOGLE_API_KEY no existe en el entorno del contenedor.")
    print("   Asegúrate de que está en docker-compose.yml y que reconstruiste el contenedor.")
    exit()
else:
    # Mostramos solo los primeros y últimos caracteres por seguridad
    masked_key = f"{api_key[:6]}...{api_key[-4:]}"
    print(f"✅ API Key detectada: {masked_key}")

# Configurar Gemini
try:
    genai.configure(api_key=api_key)
    print("\n📡 Conectando con Google AI...")
    
    models = genai.list_models()
    
    print("\n📋 MODELOS DISPONIBLES PARA TU CUENTA:")
    print("=" * 60)
    print(f"{'NOMBRE (ID)':<40} | {'MÉTODOS'}")
    print("=" * 60)
    
    count = 0
    for m in models:
        # Filtramos solo los que sirven para generar texto
        if 'generateContent' in m.supported_generation_methods:
            print(f"{m.name:<40} | generateContent")
            count += 1
            
    print("=" * 60)
    print(f"Total modelos generativos encontrados: {count}")

except Exception as e:
    print(f"\n🔥 ERROR DE CONEXIÓN CON GOOGLE: {str(e)}")
    print("   Posible causa: Clave inválida, cuota excedida o bloqueo regional.")