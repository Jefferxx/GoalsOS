import sys
import os
sys.path.append("/app")
from src.services.football.real_service import RealFootballService

def test_api_connection():
    print("📡 Iniciando diagnóstico de conexión API-Football...")
    service = RealFootballService()
    
    # 1. Probar Status (Cuota)
    print("\n1️⃣ Verificando Cuota y Estado...")
    status = service._get("status")
    print(f"   Respuesta: {status}")
    
    # 2. Probar un partido real conocido (Final del Mundial o algo reciente fijo)
    # ID 710561 es la final del mundial 2022 (siempre existe)
    test_id = "710561" 
    print(f"\n2️⃣ Buscando partido de prueba (ID Real: {test_id})...")
    fixture = service._get("fixtures", {"id": test_id})
    
    if fixture:
        match = fixture[0]
        print(f"   ✅ ÉXITO: {match['teams']['home']['name']} vs {match['teams']['away']['name']}")
        print(f"   Estado: {match['fixture']['status']['long']}")
    else:
        print("   ❌ FALLO: No se encontraron datos. Revisa tu Key.")

if __name__ == "__main__":
    test_api_connection()