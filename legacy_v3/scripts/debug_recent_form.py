import sys
import os
import requests
import json
from datetime import datetime

# Configurar rutas para importar backend
current_dir = os.getcwd()
sys.path.append(os.path.join(current_dir, 'backend'))

from src.database import SessionLocal
from src.models import Match
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("API_FOOTBALL_KEY")
BASE_URL = "https://v3.football.api-sports.io"
HEADERS = {
    'x-rapidapi-host': "v3.football.api-sports.io",
    'x-rapidapi-key': API_KEY
}

def get_last_matches_time_machine(team_id, team_name, limit=5):
    """
    Estrategia Híbrida: Forma Individual + Máquina del Tiempo.
    Intenta 2026, si falla, baja a 2025.
    """
    print(f"\n🔎 Buscando Forma Reciente: {team_name} (ID: {team_id})...")
    
    # 1. Intentar Temporada 2026 (Futuro/Presente)
    url_2026 = f"{BASE_URL}/fixtures?team={team_id}&last={limit}&status=FT&season=2026"
    resp_2026 = requests.get(url_2026, headers=HEADERS).json().get('response', [])
    
    if resp_2026:
        print(f"   ✅ Encontrados en 2026 ({len(resp_2026)} partidos).")
        return format_matches(resp_2026)
        
    print("   ⚠️ 2026 vacío. ⏪ Activando Máquina del Tiempo (2025)...")
    
    # 2. Intentar Temporada 2025 (Pasado Inmediato)
    url_2025 = f"{BASE_URL}/fixtures?team={team_id}&last={limit}&status=FT&season=2025"
    resp_2025 = requests.get(url_2025, headers=HEADERS).json().get('response', [])
    
    if resp_2025:
        print(f"   ✅ ¡ÉXITO! Encontrados datos reales de 2025.")
        return format_matches(resp_2025)
    
    print("   ❌ Falló 2025 también. Este equipo es un fantasma.")
    return []

def format_matches(fixtures):
    games_found = []
    for f in fixtures:
        game = {
            "date": f['fixture']['date'].split('T')[0],
            "league": f['league']['name'],
            "home": f['teams']['home']['name'],
            "away": f['teams']['away']['name'],
            "score": f"{f['goals']['home']}-{f['goals']['away']}"
        }
        games_found.append(game)
        print(f"   - [{game['date']}] {game['home']} {game['score']} {game['away']} ({game['league']})")
    return games_found

def debug_strategy_v2():
    db = SessionLocal()
    try:
        # Buscamos un partido problemático (ej: Porto)
        search_query = "Porto" 
        print(f"🕵️ DIAGNÓSTICO DE ESTRATEGIA V2 (FORMA RECIENTE)")
        print(f"   Objetivo: {search_query}")
        
        match = db.query(Match).filter(Match.home_team.ilike(f"%{search_query}%")).first()
        
        if not match:
            print("❌ No encontré el partido en la BD.")
            return

        print(f"✅ Partido: {match.home_team} vs {match.away_team}")
        
        # PROBAR NUEVA ESTRATEGIA
        print("\n--- PRUEBA DE SOLUCIÓN: FORMA INDIVIDUAL + TIEMPO ---")
        
        # Local
        recent_home = get_last_matches_time_machine(match.home_team_id, match.home_team)
        
        # Visita
        recent_away = get_last_matches_time_machine(match.away_team_id, match.away_team)
        
        print("\n✨ ANÁLISIS FINAL:")
        if recent_home and recent_away:
            print("🎉 ¡TENEMOS DATOS! La estrategia funciona si forzamos el año 2025.")
            print("   La IA ahora podrá leer: 'Porto viene de ganar 3 partidos seguidos en 2025'.")
        else:
            print("❌ Sigue fallando. Algo pasa con la API o los IDs.")

    except Exception as e:
        print(f"❌ Error general: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    debug_strategy_v2()