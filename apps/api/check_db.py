import sys
import os

# Aseguramos que Python encuentre los módulos de la app
sys.path.append(os.getcwd())

from src.db.session import SessionLocal
from src.models.match import Match
from sqlalchemy import text

def check_matches():
    session = SessionLocal()
    
    target_date = '2026-02-08' # La fecha que te falta
    print(f"\n🕵️‍♂️ --- DIAGNÓSTICO DE BASE DE DATOS: {target_date} ---\n")

    try:
        # Consulta cruda para ver partidos de esa fecha
        query = text(f"SELECT api_id, home_team, away_team, status, odds_data FROM matches WHERE date::text LIKE '{target_date}%'")
        results = session.exec(query).all()

        if not results:
            print("❌ NO HAY PARTIDOS para esta fecha en la base de datos.")
            print("   -> Causa probable: El Worker de sincronización falló o no ha terminado de correr.")
        else:
            print(f"✅ Se encontraron {len(results)} partidos:\n")
            for row in results:
                has_odds = "SÍ" if row.odds_data else "NO"
                print(f"   ⚽ {row.home_team} vs {row.away_team} | Estado: {row.status} | Cuotas: {has_odds}")
                
                if row.status in ['FT', 'AET', 'PEN']:
                    print("      ⚠️ OJO: Este partido está marcado como FINALIZADO (FT). El Dashboard lo oculta por defecto.")

    except Exception as e:
        print(f"🔥 Error leyendo DB: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    check_matches()