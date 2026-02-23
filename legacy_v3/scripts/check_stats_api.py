import requests
import os
from dotenv import load_dotenv
import json

load_dotenv()

API_KEY = os.getenv("API_FOOTBALL_KEY")
BASE_URL = "https://v3.football.api-sports.io"

headers = {
    'x-rapidapi-host': "v3.football.api-sports.io",
    'x-rapidapi-key': API_KEY
}

def check_stats():
    # ID del partido Rangers vs Ludogorets (sacado de tu tabla)
    MATCH_ID = 1451276
    
    print(f"🕵️ Probando conexión de ESTADÍSTICAS para el partido ID {MATCH_ID}...")
    print(f"🔑 Usando Key: {API_KEY[:5]}******")

    # 1. Probar H2H (Cara a Cara)
    # Necesitamos los IDs de los equipos primero. 
    # Rangers (257) vs Ludogorets (566) - IDs aproximados, consultamos el partido primero
    
    url_match = f"{BASE_URL}/fixtures?id={MATCH_ID}"
    try:
        r = requests.get(url_match, headers=headers)
        data = r.json()
        
        if "errors" in data and data["errors"]:
            print(f"❌ Error API (General): {data['errors']}")
            return

        match_info = data['response'][0]
        home_id = match_info['teams']['home']['id']
        away_id = match_info['teams']['away']['id']
        home_name = match_info['teams']['home']['name']
        away_name = match_info['teams']['away']['name']
        
        print(f"✅ Partido encontrado: {home_name} (ID: {home_id}) vs {away_name} (ID: {away_id})")
        
        # 2. AHORA probamos el H2H (Lo que nutre a la IA)
        url_h2h = f"{BASE_URL}/fixtures/headtohead?h2h={home_id}-{away_id}"
        print(f"📡 Solicitando H2H: {url_h2h}")
        
        r_h2h = requests.get(url_h2h, headers=headers)
        h2h_data = r_h2h.json()
        
        items_h2h = len(h2h_data.get('response', []))
        print(f"📊 Datos H2H recibidos: {items_h2h} partidos previos.")
        
        if items_h2h == 0:
            print("⚠️ OJO: La API devolvió 0 historial. Esto explica por qué la IA no sabe nada.")
        else:
            print("✅ ¡Hay datos! El problema es que el código de Python no los está leyendo bien.")
            print(json.dumps(h2h_data['response'][0], indent=2))

    except Exception as e:
        print(f"❌ Error Crítico: {e}")

if __name__ == "__main__":
    check_stats()