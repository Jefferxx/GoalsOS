import requests
import os
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

API_KEY = os.getenv("API_FOOTBALL_KEY")
BASE_URL = "https://v3.football.api-sports.io"


CHECK_DATE = "2026-01-28" 

headers = {
    'x-rapidapi-host': "v3.football.api-sports.io",
    'x-rapidapi-key': API_KEY
}

print(f"🕵️ ESCANEANDO API-FOOTBALL PARA LA FECHA: {CHECK_DATE}")
print("==================================================")

try:
    url = f"{BASE_URL}/fixtures?date={CHECK_DATE}&timezone=America/Guayaquil"
    r = requests.get(url, headers=headers)
    data = r.json()
    
    if "response" in data:
        matches = data["response"]
        print(f"✅ La API encontró {len(matches)} partidos en TOTAL (Mundial).")
        
        # Filtramos para mostrarte solo los importantes
        relevant_matches = []
        target_leagues = [2,    # UEFA Champions League
    3,    # UEFA Europa League
    39,   # Premier League (Inglaterra)
    45,   # FA Cup (Inglaterra)      <--- ¡CRUCIAL HOY!
    140,  # La Liga (España)         <--- ¡FALTABA!
    143,  # Copa del Rey (España)
    135,  # Serie A (Italia)
    137,  # Coppa Italia
    78,   # Bundesliga (Alemania)
    61,   # Ligue 1 (Francia)
    88,   # Eredivisie (Holanda)
    94,   # Liga Portugal (Porto)    <--- ¡FALTABA!
    203,  # Süper Lig (Turquía)
    71,   # Brasileirão Serie A
    72,   # Brasileirão Serie B
    242,  # LigaPro Ecuador (Serie A)
    848,  # Copa Sudamericana
    207,  # Swiss Super League (Suiza)
    144,  # Jupiler Pro League (Bélgica)
    103,  # Eliteserien (Noruega)
    218,  # Bundesliga (Austria)
    253,  # MLS (USA)
    89] # Premier, FA Cup, LaLiga, Serie A, Portugal
        
        print("\n👇 PARTIDOS DETECTADOS EN TUS LIGAS (Si está vacío, la API no tiene data):")
        for m in matches:
            lid = m['league']['id']
            lname = m['league']['name']
            home = m['teams']['home']['name']
            away = m['teams']['away']['name']
            
            if lid in target_leagues:
                print(f"   ⚽ [{lname}] {home} vs {away}")
                relevant_matches.append(m)
                
        if not relevant_matches:
            print("   ⚠️ No encontré partidos de Premier, LaLiga, Serie A o Portugal en esta fecha.")
            print("   Posiblemente sea un día sin partidos o la fecha 2025 no coincide con tu calendario 2026.")
            
    else:
        print("❌ Error en respuesta API:", data)

except Exception as e:
    print(f"❌ Error de conexión: {e}")