import sys
import os
import requests
import json

# Rutas
current_dir = os.getcwd()
sys.path.append(os.path.join(current_dir, 'backend'))

from dotenv import load_dotenv
load_dotenv()

API_KEY = os.getenv("API_FOOTBALL_KEY")
BASE_URL = "https://v3.football.api-sports.io"
HEADERS = {'x-rapidapi-host': "v3.football.api-sports.io", 'x-rapidapi-key': API_KEY}

def check_coverage(team_id):
    print(f"\n🕵️‍♂️ VERIFICANDO COBERTURA PARA ID: {team_id}")
    print("=========================================")
    
    # 1. ¿Quién es este equipo?
    url_info = f"{BASE_URL}/teams?id={team_id}"
    try:
        resp = requests.get(url_info, headers=HEADERS).json()
        team_data = resp.get('response', [])
        
        if not team_data:
            print("❌ ERROR: El ID no existe en la API.")
            return
            
        team = team_data[0]['team']
        print(f"✅ Equipo Confirmado: {team['name']} ({team['country']})")
        print(f"   Logo: {team['logo']}")
    except Exception as e:
        print(f"❌ Error conectando: {e}")
        return

    # 2. ¿Qué cobertura tengo para este equipo?
    # Este endpoint nos dice en qué ligas y temporadas la API tiene datos para este equipo
    print("\n📊 Buscando Ligas y Temporadas disponibles...")
    url_leagues = f"{BASE_URL}/leagues?team={team_id}"
    
    try:
        resp_leagues = requests.get(url_leagues, headers=HEADERS).json()
        leagues = resp_leagues.get('response', [])
        
        if not leagues:
            print("⚠️ ALERTA: No hay ligas disponibles para este equipo en tu plan.")
        else:
            print(f"✅ Encontrado en {len(leagues)} ligas. Mostrando las últimas:")
            for l in leagues[:5]: # Mostrar solo las primeras 5 para no saturar
                league_name = l['league']['name']
                seasons = [s['year'] for s in l['seasons'] if s['coverage']['fixtures']['events']]
                print(f"   - {league_name}: Temporadas con datos -> {seasons[-3:]} (Últimas 3)")
                
    except Exception as e:
        print(f"❌ Error consultando ligas: {e}")

if __name__ == "__main__":
    # Verificamos Porto y Rangers
    check_coverage(212) # Porto
    check_coverage(257) # Rangers