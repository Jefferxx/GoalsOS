import google.generativeai as genai
import os
import json
import warnings
from groq import Groq 
from dotenv import load_dotenv

warnings.filterwarnings("ignore")
load_dotenv()

class AIPredictionService:
    def __init__(self):
        # 1. Configurar Gemini (Principal)
        self.gemini_key = os.getenv("GEMINI_API_KEY")
        if self.gemini_key:
            genai.configure(api_key=self.gemini_key)
            # Usamos response_mime_type para forzar JSON limpio desde la fuente
            self.gemini_model = genai.GenerativeModel(
                'gemini-2.0-flash',
                generation_config={"response_mime_type": "application/json"}
            )
        
        # 2. Configurar Groq (Respaldo)
        self.groq_key = os.getenv("GROQ_API_KEY")
        self.groq_client = None
        if self.groq_key:
            self.groq_client = Groq(api_key=self.groq_key)

    def analyze_match(self, home_team: str, away_team: str, date: str, league: str = "", stats_context: str = ""):
        """
        Orquestador: Intenta Gemini primero, si falla (429/Error), salta a Groq.
        """
        if not self.gemini_key and not self.groq_key:
            print("❌ Error: No hay API Keys configuradas (Gemini/Groq).")
            return None

        # --- PROMPT MAESTRO V4.0 (V2.7 + SAFETY PICKS) ---
        prompt = f"""
        ACTÚA COMO: Analista Deportivo Senior de ESPN/Opta (Especialista en Big Data y Valor +EV).
        
        PARTIDO: {home_team} vs {away_team} ({league})
        
        CONTEXTO TÁCTICO Y ESTADÍSTICO (STATS):
        {stats_context}

        --- TUS INSTRUCCIONES DE ANÁLISIS PROFUNDO ---
        1. 🚫 PROHIBIDO: Respuestas genéricas como "tienen tendencia a marcar".
        2. ✅ OBLIGATORIO: Usa los números del texto 'STATS' para justificar.
           - Cita promedios específicos: "Local marca 1.8 goles/partido", "Visita encajó en sus últimos 3 juegos".
           - Analiza la FORMA RECIENTE (Últimos 5 partidos) proporcionada.
        
        3. SELECCIÓN DEL MERCADO (Jerarquía de Seguridad):
           - Si hay goles > 2.5 en promedios y mala defensa -> OVER 2.5 GOLES.
           - Si uno es muy superior en forma y H2H -> GANADOR DIRECTO.
           - Si hay dudas o equilibrio -> DOBLE OPORTUNIDAD o OVER 1.5.
           - Si ambos anotan mucho y encajan -> AMBOS MARCAN (BTTS).

        4. SAFETY PICK (NUEVO REQUISITO):
           - Debes generar una segunda opción de MUY ALTA PROBABILIDAD (>85%) para combinar en parleys seguros.
           - Ejemplos: "Más de 0.5 Goles", "Handicap Asiático +2.0", "Local o Empate".

        FORMATO DE SALIDA (JSON PURO):
        {{
            "market": "Mercado Principal (Ej: Over 2.5 Goles, BTTS Si)",
            "selection": "Tu selección principal (Ej: Over, Si, Local)",
            "probability": (0-100),
            "confidence_score": (0-100),
            "estimated_ev": "POSITIVE",
            "safety_pick": "Tu selección segura (Ej: Over 1.5 Goles)",
            "key_stat": "Dato estadístico EXACTO extraído del texto (ej: 'Porto: 10 goles en últimos 5 juegos').",
            "reasoning": "Párrafo de 3 a 4 líneas. Conecta la forma reciente con los promedios. Explica POR QUÉ hay valor."
        }}
        """

        # --- INTENTO 1: GEMINI ---
        try:
            if self.gemini_model:
                response = self.gemini_model.generate_content(prompt)
                text_response = response.text.strip()
                
                # Limpieza de bloques de código (Markdown) por si acaso
                if "```json" in text_response:
                    text_response = text_response.split("```json")[1].split("```")[0]
                elif "```" in text_response:
                    text_response = text_response.replace("```", "")
                
                return json.loads(text_response)

        except Exception as e_gemini:
            print(f"⚠️ Gemini error ({str(e_gemini)[:50]}). Cambiando a GROQ...")
            
            # --- INTENTO 2: GROQ (Respaldo) ---
            if self.groq_client:
                try:
                    chat_completion = self.groq_client.chat.completions.create(
                        messages=[
                            {"role": "system", "content": "You are a sports betting analyst that outputs strictly JSON."}, 
                            {"role": "user", "content": prompt}
                        ],
                        model="llama-3.3-70b-versatile", 
                        temperature=0.3, # Baja temperatura para análisis preciso
                        response_format={"type": "json_object"}
                    )
                    return json.loads(chat_completion.choices[0].message.content)
                except Exception as e_groq:
                    print(f"❌ Groq también falló: {e_groq}")
            
            return None