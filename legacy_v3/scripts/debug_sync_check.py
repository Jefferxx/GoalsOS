import sys
import os
from datetime import datetime, timedelta

# Configurar rutas para importar backend
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(current_dir, 'backend'))

from src.database import SessionLocal
from src.models import Match
from sqlalchemy import func

def check_sync_status():
    db = SessionLocal()
    print("🕵️ AUDITORÍA DE SINCRONIZACIÓN")
    print("=============================")
    
    today = datetime.now().date()
    tomorrow = today + timedelta(days=1)
    
    # 1. Ver qué fechas existen en la DB (desde hoy en adelante)
    matches = db.query(Match).filter(func.date(Match.date) >= today).order_by(Match.date).all()
    
    if not matches:
        print("❌ La base de datos está VACÍA para hoy en adelante.")
        return

    print(f"📊 Total partidos encontrados: {len(matches)}")
    print(f"📅 Fecha Hoy: {today}")
    
    # Contadores
    ns_count = 0
    finished_count = 0
    
    print("\n📋 LISTADO DETALLADO:")
    for m in matches:
        local_time = m.date.strftime("%Y-%m-%d %H:%M")
        status_icon = "🟢" if m.status == "NS" else "🔴"
        print(f"   {status_icon} [{m.status}] {local_time} | {m.home_team} vs {m.away_team}")
        
        if m.status == "NS":
            ns_count += 1
        else:
            finished_count += 1
            
    print("\n-----------------------------")
    print(f"✅ Pendientes (NS) - Aptos para analizar: {ns_count}")
    print(f"🔴 Finalizados/En Juego - No aparecen en Cyborg: {finished_count}")
    
    if ns_count == 0 and finished_count > 0:
        print("\n⚠️ DIAGNÓSTICO: Todos los partidos de hoy ya terminaron o empezaron.")
        print("   SOLUCIÓN: Necesitas sincronizar también los partidos de MAÑANA.")

if __name__ == "__main__":
    check_sync_status()