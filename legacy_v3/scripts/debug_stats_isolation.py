import requests
import os
import json
from dotenv import load_dotenv

# Cargar entorno
load_dotenv()

API_KEY = os.getenv("API_FOOTBALL_KEY")
BASE_URL = "https://v3.football.api-sports.io"
HEADERS = {
    'x-rapidapi-host': "v3.football.api-sports.io",
    'x-rapidapi-key': API_KEY
}

def test_team_fixtures(team_id, team_name):
    print(f"\n🕵️‍♂️ DIAGNÓSTICO PROFUNDO PARA: {team_name} (ID: {team_id})")
    print("==================================================")

    # 1. PRUEBA DE TEMPORADAS (Verificar dónde hay datos)
    print("🔹 Paso 1: Verificar en qué temporadas existen partidos...")
    for year in [2026, 2025, 2024]:
        url = f"{BASE_URL}/fixtures?team={team_id}&last=5&season={year}"
        r = requests.get(url, headers=HEADERS)
        data = r.json().get("response", [])
        print(f"   - Temp {year}: {len(data)} partidos encontrados.")

    # 2. PRUEBA SIN TEMPORADA (Histórico Global - El "Último Recurso")
    print("\n🔹 Paso 2: Probar llamada SIN temporada (Fallback Global)...")
    url_global = f"{BASE_URL}/fixtures?team={team_id}&last=5&status=FT"
    r_global = requests.get(url_global, headers=HEADERS)
    data_global = r_global.json().get("response", [])
    
    if data_global:
        print(f"   ✅ ¡EUREKA! Encontrados {len(data_global)} partidos en el global.")
        first = data_global[0]
        print(f"   🔎 Ejemplo: {first['teams']['home']['name']} vs {first['teams']['away']['name']} ({first['fixture']['date']})")
    else:
        print("   ❌ FALLÓ TAMBIÉN EL GLOBAL. La API devuelve lista vacía.")
        print("   🔍 Respuesta cruda:", r_global.text[:200])

    # 3. PRUEBA EXTREMA (Sin filtros de estado)
    if not data_global:
        print("\n🔹 Paso 3: Prueba EXTREMA (Quitando filtro 'status=FT')...")
        url_extreme = f"{BASE_URL}/fixtures?team={team_id}&last=5"
        r_extreme = requests.get(url_extreme, headers=HEADERS)
        data_extreme = r_extreme.json().get("response", [])
        print(f"   - Resultados sin filtro FT: {len(data_extreme)}")

if __name__ == "__main__":
    if not API_KEY:
        print("❌ Error: No API Key en .env")
    else:
        # Probamos con los equipos que te dieron problemas
        test_team_fixtures(212, "FC Porto")   # Porto
        test_team_fixtures(257, "Rangers")    # Rangers