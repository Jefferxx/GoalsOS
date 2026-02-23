import sys
import os

# Ajuste de path para que funcione dentro del contenedor Docker (/app)
sys.path.append("/app")

from sqlmodel import Session, select, create_engine
from src.models.match import Match
from src.services.football.real_service import RealFootballService

# --- CORRECCIÓN VITAL: Usamos 'db' en lugar de 'localhost' ---
DATABASE_URL = "postgresql://goalos_admin:goalos_secure_pass@db:5432/goalos_v4"
engine = create_engine(DATABASE_URL)

def inspect_system():
    print("\n🕵️‍♂️ --- INSPECTOR DE GOALOS (Docker Mode) ---")
    
    # 1. Verificar Consumo API Real
    print("\n📡 Estado de API-Sports:")
    try:
        service = RealFootballService()
        status = service._get("status")
        if status:
            req = status.get("requests", {})
            print(f"   ✅ Actual: {req.get('current')} / {req.get('limit_day')}")
            # Si el límite es igual al actual, avisar
            if req.get('current') == req.get('limit_day'):
                print("   🛑 ¡ALERTA! Has consumido el 100% de tu cuota diaria.")
        else:
            print("   ❌ No se pudo conectar a API-Sports")
    except Exception as e:
        print(f"   ⚠️ Error de conexión: {e}")

    # 2. Verificar Partidos en DB
    print("\n⚽ Partidos Sincronizados en DB (Últimos 20):")
    with Session(engine) as session:
        matches = session.exec(select(Match).order_by(Match.date.desc())).all()
        
        if not matches:
            print("   📭 La base de datos está vacía.")
        else:
            print(f"   Total encontrados: {len(matches)}")
            print("-" * 85)
            print(f"{'FECHA (UTC)':<20} | {'LIGA':<15} | {'EQUIPOS'}")
            print("-" * 85)
            for m in matches[:20]: 
                teams = f"{m.home_team} vs {m.away_team}"
                # Cortar nombres largos
                league = (m.league_name[:13] + '..') if len(m.league_name) > 13 else m.league_name
                print(f"{str(m.date)[:19]:<20} | {league:<15} | {teams}")
            print("-" * 85)

if __name__ == "__main__":
    inspect_system()