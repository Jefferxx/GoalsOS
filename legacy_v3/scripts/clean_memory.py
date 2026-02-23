import sys
import os

# --- CORRECCIÓN DE RUTA ---
# Agregamos la carpeta 'backend' al sistema para que encuentre 'src'
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(current_dir, 'backend'))
# ---------------------------

from src.database import SessionLocal
from src.models import Match

def clean_ai_memory():
    db = SessionLocal()
    try:
        print("🧹 Iniciando limpieza de predicciones antiguas...")
        
        # Buscamos partidos que tengan predicción pero sigan pendientes (NS)
        # Esto borra las predicciones 'ciegas' que se hicieron sin API Key
        matches = db.query(Match).filter(
            Match.ai_prediction != None,
            Match.status == "NS"
        ).all()
        
        count = 0
        for match in matches:
            match.ai_prediction = None
            count += 1
            
        db.commit()
        print(f"✅ ÉXITO: Se han borrado {count} predicciones 'ciegas'.")
        print("🧠 Ahora reinicia el Backend y dale a 'Analizar' de nuevo.")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    clean_ai_memory()