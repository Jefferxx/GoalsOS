import sys
import os
from sqlalchemy import text

# Configurar rutas
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(current_dir, 'backend'))

from src.database import SessionLocal

def reset_all_outcomes():
    db = SessionLocal()
    try:
        print("🚑 INICIANDO RE-AUDITORÍA TOTAL...")
        print("   (Esto pondrá en PENDING todas las apuestas para volver a verificarlas)")
        
        # 1. Resetear apuestas liquidadas (WON/LOST) a PENDING
        # También reseteamos el profit a 0 para recalcularlo limpio
        query = text("""
            UPDATE bets 
            SET status = 'PENDING', result_profit = 0 
            WHERE status IN ('WON', 'LOST')
        """)
        result = db.execute(query)
        
        # 2. (Opcional) Corregir el saldo del Banco
        # Esto es complejo porque deberíamos revertir las transacciones.
        # Por ahora, confiaremos en que el 'settle-bets' sumará de nuevo las ganancias.
        # Si ves el saldo inflado, usa el botón RESET en el Dashboard y pon tu saldo real manualmente.
        
        db.commit()
        
        print(f"✅ {result.rowcount} tickets reseteados a PENDING.")
        print("👉 Paso final: Ve al Dashboard > Cartera > Click en '🕵️ Liquidar Resultados'.")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    reset_all_outcomes()