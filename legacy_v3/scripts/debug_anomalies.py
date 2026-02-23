import sys
import os
import re
from sqlalchemy import text

# Configurar rutas
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(current_dir, 'backend'))

from src.database import SessionLocal
from src import models

def audit_debugger():
    db = SessionLocal()
    print("\n🕵️ --- DETECTIVE DE ANOMALÍAS ---")
    print(f"{'ID':<4} | {'PARTIDO':<30} | {'SCORE':<5} | {'SELECCIÓN REAL (DB)':<30} | {'LIMPIEZA REGEX'} | {'ESTADO'}")
    print("-" * 110)

    bets = db.query(models.Bet).join(models.Match).filter(
        models.Bet.status.in_(['WON', 'LOST', 'REJECTED'])
    ).all()

    for bet in bets:
        sel_raw = bet.selection.upper()
        # SIMULACIÓN DEL BUG (La regex que falló)
        sel_bugged = re.sub(r'[^\w\s:+-]', '', sel_raw).strip() 
        
        # SIMULACIÓN DE LA CORRECCIÓN (Con punto decimal)
        sel_fixed = re.sub(r'[^\w\s:+.-]', '', sel_raw).strip()

        score = f"{bet.match.home_score}-{bet.match.away_score}"
        
        # Solo mostramos los que mencionaste con error
        if "OVER" in sel_raw or "GANADOR" in sel_raw or "EMPATE" in sel_raw:
             print(f"{bet.id:<4} | {bet.match.home_team[:13]} vs {bet.match.away_team[:13]} | {score:<5} | {bet.selection[:30]:<30} | {sel_bugged[:15]}... | {bet.status}")

    print("-" * 110)
    print("👉 SI EN 'LIMPIEZA REGEX' VES NUMEROS SIN PUNTO (EJ: '25' EN VEZ DE '2.5'), ESE ES EL ERROR.")

if __name__ == "__main__":
    audit_debugger()