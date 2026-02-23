import sys
import os
import requests
import json

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

def debug_botafogo():
    db = SessionLocal()
    try:
        print("🕵️ BUSCANDO 'BOTAFOGO' EN LA BASE DE DATOS...")
        # Buscamos por nombre aproximado
        match = db.query(Match).filter(Match.home_team.ilike("%Botafogo%")).first()
        
        if not match:
            print("❌ No encontré el partido de Botafogo en la BD local.")
            return

        print(f"✅ Partido encontrado: {match.home_team} vs {match.away_team}")
        print(f"   ID Partido (DB): {match.id}")
        print(f"   API ID: {match.api_id}")
        print("   --- IDs GUARDADOS PARA OPTIMIZACIÓN ---")
        print(f"   Home ID: {match.home_team_id}")
        print(f"   Away ID: {match.away_team_id}")
        print(f"   League ID: {match.league_id}")
        print(f"   Season: {match.season_year}")
        
        if not match.home_team_id or not match.away_team_id:
            print("⚠️ ALERTA: Los IDs de los equipos son NULOS. La optimización falló al guardar.")
            return

        print("\n📡 PROBANDO PETICIÓN H2H A LA API (REAL)...")
        url = f"{BASE_URL}/fixtures/headtohead?h2h={match.home_team_id}-{match.away_team_id}&last=10"
        print(f"   URL: {url}")
        
        response = requests.get(url, headers=HEADERS)
        data = response.json()
        
        results = data.get('response', [])
        print(f"📊 Resultados devueltos por la API: {len(results)}")
        
        if len(results) > 0:
            print("✅ La API SÍ tiene datos. Aquí el primero:")
            print(json.dumps(results[0]['score'], indent=2))
            print("\n🤔 CONCLUSIÓN: Si aquí ves datos, el problema está en cómo 'stats_service.py' procesa la respuesta.")
        else:
            print("❌ La API devolvió una lista vacía [].")
            print("   Posible causa: Los IDs son correctos pero no tienen historial registrado en la API, o los IDs están mal.")

    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    debug_botafogo()