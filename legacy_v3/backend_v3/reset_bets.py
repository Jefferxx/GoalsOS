from src.database import get_db
from sqlalchemy import text

def total_wipeout():
    db = next(get_db())
    print("☢️ INICIANDO BORRADO TOTAL (APUESTAS + ANÁLISIS VIEJOS)...")
    
    try:
        # 1. Borrar todas las apuestas (Tickets)
        db.execute(text("DELETE FROM bets"))
        print("✅ Tabla 'bets' vaciada.")

        # 2. Borrar las predicciones de la IA en la tabla matches (Memoria)
        # Esto pone el campo ai_prediction en NULL, obligando a re-analizar.
        db.execute(text("UPDATE matches SET ai_prediction = NULL"))
        print("✅ Columna 'ai_prediction' reseteada a NULL en todos los partidos.")
        
        db.commit()
        print("🎉 ¡SISTEMA COMPLETAMENTE LIMPIO! Listo para análisis real.")
    except Exception as e:
        print(f"❌ Error crítico: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    total_wipeout()