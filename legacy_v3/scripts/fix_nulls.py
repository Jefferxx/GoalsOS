import sys
import os
from sqlalchemy import text

# Configurar rutas
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(current_dir, 'backend'))

from src.database import SessionLocal

def force_fix_nulls():
    db = SessionLocal()
    try:
        print("🔧 Iniciando reparación forzada de NULOS en partidos NS...")
        
        # 1. Forzar a NULL puro mediante SQL directo
        # Esto arregla cualquier "null" de texto, JSON vacío o cadena vacía
        query = text("UPDATE matches SET ai_prediction = NULL WHERE status = 'NS'")
        result = db.execute(query)
        db.commit()
        
        print(f"✅ Se actualizaron/limpiaron {result.rowcount} filas.")
        
        # 2. Verificar cuántos quedan listos ahora
        check_query = text("SELECT count(*) FROM matches WHERE status = 'NS' AND ai_prediction IS NULL")
        count = db.execute(check_query).scalar()
        
        print(f"📊 Partidos listos para análisis (Real SQL): {count}")
        
        if count > 0:
            print("🚀 AHORA SÍ: Reinicia el backend e intenta analizar.")
        else:
            print("⚠️ Aún marca 0. Algo raro pasa con el status 'NS'.")

    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    force_fix_nulls()