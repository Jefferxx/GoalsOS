import sys
import os
# Ajuste para Docker
sys.path.append("/app")

from sqlmodel import Session, select
from src.db.session import engine
from src.models.match import Match

def list_all_matches():
    print("\n📋 LISTADO COMPLETO DE PARTIDOS EN BASE DE DATOS")
    print("="*100)
    print(f"{'ID':<6} | {'API ID':<10} | {'FECHA':<20} | {'LIGA':<20} | {'PARTIDO'}")
    print("="*100)

    with Session(engine) as session:
        # Ordenamos por fecha para ver los futuros (fantasmas) al final o al inicio
        matches = session.exec(select(Match).order_by(Match.date.desc())).all()
        
        for m in matches:
            match_name = f"{m.home_team} vs {m.away_team}"
            # Cortamos nombres largos para que se vea bien en consola
            league = (m.league_name[:18] + '..') if m.league_name and len(m.league_name) > 18 else m.league_name
            date_str = str(m.date)[:16]
            
            print(f"{m.id:<6} | {m.api_id:<10} | {date_str:<20} | {league:<20} | {match_name}")

    print("="*100)
    print(f"Total de partidos encontrados: {len(matches)}\n")

if __name__ == "__main__":
    list_all_matches()