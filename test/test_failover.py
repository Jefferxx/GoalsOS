import sys
import os

# --- 🛠️ CORRECCIÓN DE RUTA ---
# Esto agrega la ruta exacta donde vive 'ai_service.py' para que Python lo encuentre
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(current_dir, 'backend', 'src', 'services'))
# -----------------------------

# Ahora sí funcionará el import
from ai_service import AIPredictionService

print("🧪 INICIANDO PRUEBA DE FAILOVER (GEMINI -> GROQ)...")
print("---------------------------------------------------")

# Inicializamos el servicio
ai = AIPredictionService()

# Datos de prueba
print("🤖 Analizando partido de prueba...")
resultado = ai.analyze_match(
    home_team="Team A",
    away_team="Team B",
    date="2025-01-01",
    stats_context="Team A gana siempre. Team B pierde siempre."
)

print("\n📦 RESPUESTA RECIBIDA:")
print(resultado)