import sys
import os
import json

# --- CORRECCIÓN DE RUTA ---
# Le decimos a Python que busque módulos dentro de la carpeta 'backend'
current_dir = os.getcwd()
backend_path = os.path.join(current_dir, "backend")
sys.path.append(backend_path)
# --------------------------

try:
    from src.database import SessionLocal
    from src import models
    from src.services.stats_service import StatsService
except ImportError as e:
    print(f"❌ Error de Importación: {e}")
    print(f"Ruta intentada: {backend_path}")
    print("Asegúrate de que existe la carpeta 'backend/src'.")
    sys.exit(1)

def inspect_match_data():
    try:
        db = SessionLocal()
    except Exception as e:
        print(f"❌ Error conectando a la base de datos: {e}")
        return

    # 1. Buscamos un partido pendiente (NS = Not Started)
    try:
        match = db.query(models.Match).filter(models.Match.status == "NS").first()
    except Exception as e:
        print(f"❌ Error consultando la tabla de partidos: {e}")
        print("¿Has ejecutado las migraciones o sincronizado el mercado?")
        return
    
    if not match:
        print("❌ No hay partidos pendientes (NS) en la base de datos para analizar.")
        print("   Ejecuta 'Sincronizar Mercado' en el Dashboard primero.")
        return

    print(f"\n🦅 --- INSPECTOR DE DATOS GOAL OS ---")
    print(f"🏟️  Partido: {match.home_team} vs {match.away_team}")
    print(f"🆔  API ID: {match.api_id}")
    print("-" * 50)

    # 2. Invocamos al servicio de estadísticas
    stats_service = StatsService()
    
    print("\n📡 Conectando con API-Football para extraer datos raw...")
    context_data = stats_service.get_match_context(match.api_id)
    
    # 3. Revelamos la verdad
    raw_text = context_data.get("text", "VACÍO")

    print("\n📄 [LO QUE LEE LA IA] (Este es el 'stats_context'):")
    print("=" * 20 + " INICIO TEXTO " + "=" * 20)
    print(raw_text)
    print("=" * 20 + " FIN TEXTO " + "=" * 20)

    print("\n🔍 [ANÁLISIS DE CALIDAD DE DATOS]:")
    
    text_lower = raw_text.lower()
    
    # Chequeo de Córners
    if "corner" in text_lower or "esquina" in text_lower:
        print("✅ Datos de CÓRNERS detectados.")
    else:
        print("⚠️ ALERTA: No veo la palabra 'corner'. La IA no puede predecir córners.")

    # Chequeo de Tarjetas
    if "card" in text_lower or "tarjeta" in text_lower or "yellow" in text_lower:
        print("✅ Datos de TARJETAS detectados.")
    else:
        print("⚠️ ALERTA: No veo datos de tarjetas. La IA no puede predecir amonestaciones.")

    # Chequeo de Goles
    if "-" in raw_text and ("1" in raw_text or "0" in raw_text):
        print("✅ Datos de GOLES/MARCADORES detectados.")
    else:
        print("❌ CRÍTICO: No parece haber marcadores históricos.")

if __name__ == "__main__":
    inspect_match_data()