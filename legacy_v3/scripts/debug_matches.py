import sys
import os

# Configuración de rutas
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(current_dir, 'backend'))

from src.database import SessionLocal
from src.models import Match
from sqlalchemy import or_

def debug_matches():
    db = SessionLocal()
    try:
        print("🕵️ DIAGNÓSTICO DE PARTIDOS PENDIENTES")
        print("=====================================")
        
        # 1. Buscar partidos NS (No Iniciados)
        ns_matches = db.query(Match).filter(Match.status == "NS").all()
        print(f"📊 Total partidos con estado 'NS': {len(ns_matches)}")
        
        if len(ns_matches) == 0:
            print("⚠️ ALERTA: No hay partidos NS. ¿Se borraron o cambiaron a '1H'?")
            return

        print("\n🔍 Analizando los primeros 3 partidos NS:")
        for m in ns_matches[:3]:
            pred_val = m.ai_prediction
            print(f"   - ID {m.id}: {m.home_team} vs {m.away_team}")
            print(f"     Fecha: {m.date}")
            print(f"     Predicción (Raw): '{pred_val}' (Tipo: {type(pred_val)})")
            
            # Prueba de lógica
            es_none = (pred_val is None)
            print(f"     ¿Es None?: {es_none}")
            
        # 2. Simular la consulta del Backend
        # Probamos filtrando por None y también por cadena vacía por si acaso
        pending = db.query(Match).filter(
            Match.status == "NS",
            or_(Match.ai_prediction == None, Match.ai_prediction == "")
        ).all()
        
        print(f"\n✅ Partidos listos para analizar (Query Corregida): {len(pending)}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    debug_matches()