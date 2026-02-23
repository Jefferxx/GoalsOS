import requests
import os
import json
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("API_FOOTBALL_KEY")
BASE_URL = "https://v3.football.api-sports.io"
HEADERS = {
    'x-rapidapi-host': "v3.football.api-sports.io",
    'x-rapidapi-key': API_KEY
}

def get_team_id(team_name):
    print(f"🔎 Buscando ID para: {team_name}...")
    try:
        url = f"{BASE_URL}/teams"
        params = {"search": team_name}
        r = requests.get(url, headers=HEADERS, params=params)
        data = r.json()
        
        if data.get("response"):
            # Tomamos el primero que coincida con Turquía si es posible, o el primero de la lista
            for item in data["response"]:
                t = item['team']
                print(f"   -> Encontrado: {t['name']} (ID: {t['id']}) - País: {t['country']}")
                if t['country'] == "Turkey":
                    return t['id']
            # Si no es turco, devolvemos el primero
            return data["response"][0]['team']['id']
        else:
            print("   ❌ No encontrado.")
            return None
    except Exception as e:
        print(f"   ❌ Error API: {e}")
        return None

def check_h2h():
    print("🕵️ DEBUGGER FORENSE: Alanyaspor vs Eyüpspor")
    print("============================================")

    # 1. Obtener IDs (Para asegurarnos de que no estamos usando IDs incorrectos)
    id_alanyaspor = get_team_id("Alanyaspor")
    id_eyupspor = get_team_id("Eyüpspor") # Ojo con la diéresis, la API a veces prefiere "Eyupspor"

    if not id_eyupspor:
        print("⚠️ Intentando buscar 'Eyupspor' sin diéresis...")
        id_eyupspor = get_team_id("Eyupspor")

    if not id_alanyaspor or not id_eyupspor:
        print("❌ No se pudieron obtener los IDs. Abortando.")
        return

    print(f"\n✅ IDs Confirmados: {id_alanyaspor} vs {id_eyupspor}")

    # 2. Consultar H2H Directo
    endpoint = f"fixtures/headtohead?h2h={id_alanyaspor}-{id_eyupspor}"
    print(f"\n📡 Consultando API: {endpoint}")
    
    url = f"{BASE_URL}/{endpoint}"
    r = requests.get(url, headers=HEADERS)
    data = r.json()

    # 3. Análisis de la Respuesta
    raw_response = data.get("response", [])
    print(f"📊 Partidos encontrados en la API: {len(raw_response)}")

    if len(raw_response) > 0:
        print("\n📜 LISTADO DE PARTIDOS (Raw Data):")
        for m in raw_response:
            date = m['fixture']['date']
            home = m['teams']['home']['name']
            away = m['teams']['away']['name']
            score = f"{m['goals']['home']}-{m['goals']['away']}"
            print(f"   - [{date}] {home} vs {away} ({score})")
            
        print("\n🤔 CONCLUSIÓN:")
        print("   Si ves partidos aquí arriba, entonces el error está en 'stats_service.py' (filtrado/fechas).")
        print("   Si NO ves partidos, entonces la API Oficial de Football NO tiene estos registros (RedScores usa otra fuente).")
    else:
        print("\n❌ LA API RESPONDIÓ UNA LISTA VACÍA [].")
        print("   Esto confirma que API-Football NO tiene registros de estos equipos jugando entre sí.")
        print("   Posible causa: Eyüpspor es un equipo nuevo en Super Lig y la API no tiene sus partidos de 2da división o amistosos.")

if __name__ == "__main__":
    check_h2h()