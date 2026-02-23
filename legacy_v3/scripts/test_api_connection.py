import os
import requests
from dotenv import load_dotenv

# Cargar variables
load_dotenv()

API_KEY = os.getenv("API_FOOTBALL_KEY")
URL = "https://v3.football.api-sports.io/status"

print("🩺 DIAGNÓSTICO DE CONEXIÓN API FOOTBALL")
print("=======================================")
print(f"🔑 Clave detectada: {API_KEY}")

if not API_KEY:
    print("❌ ERROR CRÍTICO: No se encontró API_FOOTBALL_KEY en el archivo .env")
    exit()

headers = {
    'x-rapidapi-host': "v3.football.api-sports.io",
    'x-rapidapi-key': API_KEY
}

try:
    print("📡 Conectando a los servidores de API-Football...")
    response = requests.get(URL, headers=headers)
    data = response.json()

    print(f"📥 Código de Respuesta: {response.status_code}")
    
    if "errors" in data and data["errors"]:
        print(f"❌ LA API DEVOLVIÓ ERRORES: {data['errors']}")
    elif "response" in data:
        account_info = data["response"]["account"]
        print("✅ CONEXIÓN EXITOSA")
        print(f"👤 Usuario: {account_info['firstname']} {account_info['lastname']}")
        print(f"📧 Email: {account_info['email']}")
        print(f"📊 Plan: {account_info['plan']}")
        
        requests_curr = data['response']['requests']['current']
        requests_limit = data['response']['requests']['limit_day']
        print(f"📉 Uso de Solicitudes Hoy: {requests_curr} / {requests_limit}")
        
        if requests_curr >= requests_limit:
            print("⚠️ ALERTA: ¡Has alcanzado el límite diario de tu plan!")
    else:
        print("⚠️ Respuesta inesperada:", data)

except Exception as e:
    print(f"❌ Error de conexión: {e}")