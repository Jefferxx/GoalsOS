import sys
import os

# --- CORRECCIÓN DE RUTA (Magia para que funcione desde la raíz) ---
# Agregamos la carpeta 'backend' al sistema para poder importar 'src'
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(current_dir, 'backend'))
# ------------------------------------------------------------------

from src.database import SessionLocal
from sqlalchemy import text

def delete_yesterday_matches():
    db = SessionLocal()
    try:
        print("🧹 Eliminando partidos viejos (del 21 de Enero) que estorban...")
        
        # Borramos todo lo anterior al día 22 (Hoy)
        # Esto eliminará esos partidos de Champions League de ayer que bloquean el sistema
        query = text("DELETE FROM matches WHERE date < '2026-01-22 00:00:00'")
        result = db.execute(query)
        db.commit()
        
        print(f"✅ ÉXITO: Se eliminaron {result.rowcount} partidos viejos.")
        print("🚀 Ahora el sistema solo verá los partidos de HOY (Europa League).")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    delete_yesterday_matches()