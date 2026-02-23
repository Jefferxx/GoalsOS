import sys
import os
from sqlalchemy import text
import re

# Configuración de rutas para importar backend
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(current_dir, 'backend'))

from src.database import SessionLocal
from src import models

def debug_specific_bet():
    db = SessionLocal()
    try:
        print("\n🔍 --- INICIANDO DEBUG DE AUDITORÍA (CASO SION) ---")
        
        # 1. Buscar el ticket problemático (Servette vs Sion)
        # Usamos ILIKE para asegurar que lo encuentre mayúscula/minúscula
        match_query = db.query(models.Match).filter(
            models.Match.away_team.ilike("%Sion%")
        ).first()
        
        if not match_query:
            print("❌ ERROR: No encontré el partido de 'Sion' en la base de datos.")
            return

        bet = db.query(models.Bet).filter(models.Bet.match_id == match_query.id).first()
        
        if not bet:
            print("❌ ERROR: Encontré el partido, pero no hay apuesta asociada.")
            return

        # 2. Imprimir DATOS CRUDOS (Raw Data)
        print(f"\n📊 DATOS EN BASE DE DATOS:")
        print(f"   - Partido: {match_query.home_team} vs {match_query.away_team}")
        print(f"   - Marcador: {match_query.home_score} - {match_query.away_score}")
        print(f"   - Selección (Raw): '{bet.selection}'")
        print(f"   - Selección (Repr): {repr(bet.selection)}") # Esto muestra caracteres ocultos
        print(f"   - Estado Actual: {bet.status}")

        # 3. Simulación de la Lógica del Auditor
        print(f"\n🧠 SIMULANDO LÓGICA DEL AUDITOR:")
        
        sel = bet.selection.upper().strip()
        print(f"   1. Normalizado (.upper): '{sel}'")
        
        # Limpieza agresiva (lo que vamos a implementar)
        sel_clean = re.sub(r'[^\w\s:+-]', '', sel)
        print(f"   2. Limpieza Agresiva (Sin emojis): '{sel_clean}'")

        home_score = match_query.home_score
        away_score = match_query.away_score
        both_scored = (home_score > 0 and away_score > 0)
        
        print(f"   3. ¿Marcaron Ambos? (Score: {home_score}-{away_score}) -> {both_scored}")

        # Prueba de Lógica BTTS
        if "AMBOS" in sel or "BTTS" in sel or "MARCAN" in sel:
            print("   4. Detectado mercado: AMBOS MARCAN")
            
            has_no = "NO" in sel or "NUNCA" in sel
            print(f"   5. ¿Contiene la palabra 'NO'? -> {has_no}")
            
            if has_no:
                outcome = "WON" if not both_scored else "LOST"
                print(f"   6. Lógica Negativa Aplicada: Si both_scored es True -> LOST. Resultado -> {outcome}")
            else:
                outcome = "WON" if both_scored else "LOST"
                print(f"   6. Lógica Positiva Aplicada: Resultado -> {outcome}")
        else:
            print("   4. ⚠️ NO SE DETECTÓ COMO MERCADO 'AMBOS MARCAN'")

        print("\n------------------------------------------------")

    except Exception as e:
        print(f"❌ Error crítico en debug: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    debug_specific_bet()