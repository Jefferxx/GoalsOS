import requests
import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("API_FOOTBALL_KEY")
BASE_URL = "https://v3.football.api-sports.io"

def check_access():
    if not API_KEY:
        print("❌ ERROR: Falta API_FOOTBALL_KEY")
        return

    headers = {'x-apisports-key': API_KEY}
    print(f"🦅 GoalOS API Inspector v2")
    print("-" * 40)

    # 1. ESTADO
    try:
        status = requests.get(f"{BASE_URL}/status", headers=headers).json()
        requests_info = status.get("response", {}).get("requests", {})
        print(f"📊 Uso: {requests_info.get('current')}/{requests_info.get('limit_day')} | Plan: {status.get('response', {}).get('subscription', {}).get('plan')}")
    except:
        print("❌ Error conectando a /status")
        return

    # 2. CHECKLIST DE FUNCIONALIDADES (Usando un partido real de Premier League)
    # Usamos la Premier League (ID 39) Season 2023 para asegurar datos
    test_league = 39 
    test_season = 2023
    
    print("\n🔍 Verificando Acceso a Módulos:")
    
    modules = [
        ("Fixtures (Partidos)", f"/fixtures?league={test_league}&season={test_season}&last=1"),
        ("Standings (Tabla)", f"/standings?league={test_league}&season={test_season}"),
        ("Pre-match Odds (Cuotas)", f"/odds?league={test_league}&season={test_season}&bet=1"),
        ("Predictions (Predicciones)", f"/predictions?fixture=1035043"), # Un partido pasado real
        ("Lineups (Alineaciones)", f"/fixtures/lineups?fixture=1035043"),
        ("Injuries (Lesiones)", f"/injuries?fixture=1035043"),
    ]

    for name, endpoint in modules:
        try:
            res = requests.get(f"{BASE_URL}{endpoint}", headers=headers)
            data = res.json()
            
            if not data.get("errors") and res.status_code == 200:
                # A veces devuelve 200 pero response vacía si el plan no lo permite
                if isinstance(data.get("response"), list): 
                    print(f"✅ {name}: ACCESO CONCEDIDO")
                else:
                    print(f"⚠️ {name}: Respuesta vacía (Posible restricción)")
            else:
                print(f"❌ {name}: DENEGADO ({data.get('errors')})")
        except Exception as e:
            print(f"❌ {name}: Error de red")

    print("-" * 40)
    print("Nota: 'In-Play Odds' y 'Livescore' consumen muchas llamadas. GoalOS usará datos Pre-Match.")

if __name__ == "__main__":
    check_access()