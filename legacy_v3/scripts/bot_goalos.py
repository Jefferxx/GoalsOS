import time
import schedule
import requests
from datetime import datetime

# URL de tu API Local
API_URL = "http://127.0.0.1:8000"

def job():
    print(f"\n🤖 [GoalOS BOT] Iniciando rutina: {datetime.now()}")
    
    try:
        # PASO 1: Sincronizar Partidos y Cuotas
        print("   1. Sincronizando partidos y cuotas...")
        res = requests.get(f"{API_URL}/sync-matches")
        print(f"      Resultado: {res.json()}")
        time.sleep(5) 

        # PASO 2: Analizar Partidos (Batch)
        # Hacemos 3 pasadas por si hay muchos partidos (limit=5 cada vez)
        print("   2. Analizando con IA (3 lotes)...")
        for i in range(3):
            res = requests.get(f"{API_URL}/analyze-batch?limit=5")
            data = res.json()
            if data.get("status") == "info":
                print("      No hay más partidos pendientes.")
                break
            print(f"      Lote {i+1}: {data.get('processed')} analizados.")
            time.sleep(5)

        # PASO 3: Ejecutar Apuestas
        print("   3. Colocando Apuestas Automáticas...")
        res = requests.post(f"{API_URL}/auto-bet")
        print(f"      Resultado: {res.json()}")

        print("✅ [GoalOS BOT] Rutina finalizada con éxito.\n")

    except Exception as e:
        print(f"❌ [GoalOS BOT] Error de conexión: {e}")
        print("   ¿Está corriendo el servidor (uvicorn)?")

# Ejecuta el trabajo inmediatamente al iniciar el script
print("🚀 Arrancando Bot... Ejecutando primera ronda ahora mismo.")
job()

# Y programa la ejecución diaria a las 8 AM
schedule.every().day.at("08:00").do(job)

print("🕐 Esperando siguiente ejecución a las 08:00 AM...")
while True:
    schedule.run_pending()
    time.sleep(60)