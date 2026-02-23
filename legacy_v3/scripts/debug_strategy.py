import requests
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Cargar entorno
load_dotenv()

API_KEY = os.getenv("API_FOOTBALL_KEY")
BASE_URL = "https://v3.football.api-sports.io"
HEADERS = {
    'x-rapidapi-host': "v3.football.api-sports.io",
    'x-rapidapi-key': API_KEY
}

# EQUIPOS PARA LA PRUEBA DE FUEGO
# Usaremos equipos que fallaron ayer para ver si los desbloqueamos
TEST_CASES = [
    {"id": 7848, "name": "Mirassol (Brasil)", "season": 2025},  # Falló por "Plan Error"
    {"id": 66, "name": "Aston Villa (Inglaterra)", "season": 2025} # Falló por "Plan Error"
]

def try_fetch(name, url_suffix):
    print(f"   👉 Probando método: {name}...")
    try:
        url = f"{BASE_URL}/{url_suffix}"
        r = requests.get(url, headers=HEADERS)
        data = r.json()
        
        if "errors" in data and data["errors"]:
            print(f"      ❌ BLOQUEADO: {data['errors']}")
            return False, []
        
        count = data.get("results", 0)
        print(f"      ✅ ÉXITO: {count} partidos encontrados.")
        return True, data.get("response", [])
    except Exception as e:
        print(f"      ❌ ERROR CÓDIGO: {e}")
        return False, []

def run_diagnostics():
    print("🕵️ INICIANDO DIAGNÓSTICO DE ESTRATEGIAS API")
    print("============================================")

    for team in TEST_CASES:
        t_id = team['id']
        t_name = team['name']
        t_season = team['season']
        
        print(f"\n⚽ Analizando: {t_name} (ID: {t_id})")
        
        # --- ESTRATEGIA 1: POR TEMPORADA (La que falló ayer) ---
        # fixtures?team=ID&season=2025&status=FT
        try_fetch("Filtro por Season (2025)", f"fixtures?team={t_id}&season={t_season}&status=FT")

        # --- ESTRATEGIA 2: POR FECHA (Últimos 6 meses) ---
        # Esta es nuestra nueva apuesta. Pedimos desde hace 180 días hasta hoy.
        today = datetime.now().strftime("%Y-%m-%d")
        six_months_ago = (datetime.now() - timedelta(days=180)).strftime("%Y-%m-%d")
        
        # fixtures?team=ID&from=...&to=...
        success, games = try_fetch(
            "Filtro por Fecha (6 Meses)", 
            f"fixtures?team={t_id}&from={six_months_ago}&to={today}&status=FT"
        )
        
        if success and games:
            print("      🔍 Muestra (último partido):")
            last = games[-1] # El último de la lista
            print(f"         {last['fixture']['date'][:10]}: {last['teams']['home']['name']} vs {last['teams']['away']['name']} ({last['goals']['home']}-{last['goals']['away']})")

        # --- ESTRATEGIA 3: H2H (Verificación) ---
        # Verificamos si H2H sigue vivo
        # Usamos un rival aleatorio o conocido para probar (ej. Aston Villa vs Man City - ID 50)
        rival_id = 50 if t_id == 66 else 127 # Man City o Palmeiras
        try_fetch("Endpoint H2H", f"fixtures/headtohead?h2h={t_id}-{rival_id}")

if __name__ == "__main__":
    if not API_KEY:
        print("❌ Error: No API Key en .env")
    else:
        run_diagnostics()