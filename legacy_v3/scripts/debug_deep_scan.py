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

def deep_scan_team(team_id, team_name):
    print(f"\n🕵️‍♂️ ESCANEANDO PROFUNDAMENTE A: {team_name} (ID: {team_id})")
    print("==================================================")
    
    # Probamos años hacia atrás
    years_to_scan = [2026, 2025, 2024, 2023]
    
    found_data = False
    
    for year in years_to_scan:
        print(f"   ⏳ Probando Temporada {year}...", end=" ")
        
        # 1. Buscamos Partidos (Forma)
        url_fix = f"{BASE_URL}/fixtures?team={team_id}&last=5&status=FT&season={year}"
        resp_fix = requests.get(url_fix, headers=HEADERS).json().get('response', [])
        
        if resp_fix:
            print(f"✅ ¡EUREKA! {len(resp_fix)} partidos encontrados.")
            print(f"      Ejemplo: {resp_fix[0]['teams']['home']['name']} vs {resp_fix[0]['teams']['away']['name']} ({resp_fix[0]['goals']['home']}-{resp_fix[0]['goals']['away']})")
            print(f"      Fecha: {resp_fix[0]['fixture']['date'][:10]}")
            found_data = True
            break # Dejamos de buscar, ya encontramos lo más reciente
        else:
            print("❌ Vacío.")

    if not found_data:
        print("\n⚠️ ALERTA CRÍTICA: Este equipo no tiene datos en los últimos 4 años. ¿ID Incorrecto?")
    else:
        print(f"\n🚀 CONCLUSIÓN: Para {team_name}, debemos usar la temporada {year}.")

if __name__ == "__main__":
    # IDs sacados de tu log anterior
    deep_scan_team(212, "FC Porto")
    deep_scan_team(257, "Rangers")