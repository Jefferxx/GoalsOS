import sys
import os
import json
from dotenv import load_dotenv

# --- Configuración de Rutas para importar módulos del backend ---
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(current_dir, 'backend'))

from src.services.stats_service import StatsService
from src.services.ai_service import AIPredictionService

# Cargar claves
load_dotenv()

def test_cyborg_flow():
    print("🦾 INICIANDO PRUEBA DE FLUJO CYBORG (Híbrido)")
    print("==============================================")

    # 1. Configuración del escenario de prueba
    # Usaremos el partido Mirassol (7848) vs Vasco (133) que vimos en tus logs
    match_id_test = 1492117
    home_id = 7848
    away_id = 133
    
    # Este es el texto que tú escribirías manualmente en el Dashboard
    manual_input_simulado = """
    ANÁLISIS DE REDSCORES:
    - Mirassol: Ha ganado 3 de sus últimos 5 partidos en casa. Su delantero principal vuelve de lesión.
    - Vasco: Viene de perder 2 seguidos como visitante. Tienen problemas defensivos graves.
    - Clima: Se espera lluvia fuerte, cancha pesada.
    """

    print(f"📝 1. Input Manual Simulado:\n{manual_input_simulado}")
    print("\n📡 2. Llamando a StatsService (Modo H2H + Manual)...")

    # 2. Ejecutar la lógica del StatsService
    stats_service = StatsService()
    
    try:
        # Llamamos a la función con el nuevo parámetro manual_input
        context = stats_service.get_match_context(
            match_id=match_id_test,
            home_id=home_id,
            away_id=away_id,
            league_id=71,   # Brasileirao
            season=2025,
            manual_input=manual_input_simulado  # <--- ¡AQUÍ ESTÁ LA CLAVE!
        )
        
        # 3. Verificar el "Mega-Prompt" generado
        generated_text = context.get("text", "")
        generated_json = context.get("json", {})
        
        print("\n✅ 3. Contexto Generado Exitosamente:")
        print("--------------------------------------------------")
        print(generated_text)
        print("--------------------------------------------------")
        
        # Validaciones automáticas
        has_manual = "ANÁLISIS DE REDSCORES" in generated_text
        has_h2h = "ANÁLISIS DE ENFRENTAMIENTOS DIRECTOS" in generated_text
        
        if has_manual and has_h2h:
            print("\n✅ PRUEBA DE INTEGRACIÓN: PASADA")
            print("   -> El sistema fusionó correctamente el H2H de la API con tu texto manual.")
        else:
            print("\n❌ PRUEBA FALLIDA: Falta alguna parte en el texto final.")

        # 4. Verificar estructura JSON para el Dashboard
        print("\n📊 4. Verificando JSON para Dashboard:")
        print(f"   - H2H Items: {len(generated_json.get('h2h', []))}")
        print(f"   - Home Last 5 (Debe estar vacío): {len(generated_json.get('home_last_5', []))}")
        
        # 5. (Opcional) Prueba de fuego con la IA real
        print("\n🧠 5. ¿Quieres enviar esto a la IA Real (Gemini/Groq)?")
        user_conf = input("   Escribe 'SI' para gastar 1 llamada de IA y ver la predicción: ")
        
        if user_conf.lower() == "si":
            print("\n   🚀 Enviando a la IA...")
            brain = AIPredictionService()
            prediction = brain.analyze_match(
                home_team="Mirassol",
                away_team="Vasco da Gama",
                date="2026-01-30",
                league="Brasileirao",
                stats_context=generated_text
            )
            print("\n   🤖 RESPUESTA DE LA IA:")
            print(json.dumps(prediction, indent=2, ensure_ascii=False))
        else:
            print("   Ok, prueba finalizada sin coste de IA.")

    except Exception as e:
        print(f"\n❌ ERROR CRÍTICO EN EL CÓDIGO: {e}")

if __name__ == "__main__":
    test_cyborg_flow()