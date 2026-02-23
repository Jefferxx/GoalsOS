import os
import json
import re
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from groq import Groq
from src.services.football.mapper import DataMapper

class FootballAI:
    def __init__(self):
        self.google_key = os.getenv("GOOGLE_API_KEY")
        self.groq_key = os.getenv("GROQ_API_KEY")
        self.model = None

        if self.google_key:
            try:
                genai.configure(api_key=self.google_key)
                self.model = genai.GenerativeModel(
                    'models/gemini-flash-latest',
                    safety_settings={
                        HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                        HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                        HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                        HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
                    }
                )
                print("✅ AI Service: Gemini Flash Latest configurado.")
            except Exception as e:
                print(f"⚠️ AI Service: Error configurando Gemini: {e}")

    def analyze_match(self, match_data):
        home = getattr(match_data, 'home_team', None) or match_data.get('home_team')
        away = getattr(match_data, 'away_team', None) or match_data.get('away_team')
        league = getattr(match_data, 'league_name', None) or match_data.get('league_name')
        
        context = DataMapper.get_ai_context(match_data)
        
        prompt = f"""
        Actúa como un Matemático Deportivo de Élite especializado en Gestión de Riesgo (Kelly Criterion).
        OBJETIVO: Analizar este partido para encontrar valor matemático real.
        
        EVENTO: {home} vs {away} ({league})
        
        DATOS TÁCTICOS:
        1. FORMA/PREDICCIÓN: {context.get('form_analysis', 'Sin datos')}
        2. H2H: {context.get('h2h_trends', 'Sin datos')}
        3. LESIONES: {context.get('injury_report', 'Sin datos')}
        4. CUOTAS: {context.get('odds_summary', 'Sin datos')}
        
        TU TAREA:
        1. Calcula probabilidad REAL (0.0 a 1.0).
        2. Genera un JSON PURO, SIN COMENTARIOS NI TEXTO EXTRA.
        3. El campo "selection_code" debe ser "1" si gana {home}, "X" si es Empate, o "2" si gana {away}.

        FORMATO:
        {{
            "prediction": "Nombre Equipo o Empate",
            "selection_code": "1/X/2",
            "win_probability": 0.00,
            "confidence": 0,
            "reasoning": "Breve razón",
            "risk_level": "Low/Medium/High"
        }}
        """

        if self.model:
            try:
                response = self.model.generate_content(prompt)
                return self._parse_json(response.text)
            except Exception as e:
                print(f"⚠️ Fallo Gemini: {e}")

        if self.groq_key:
            try:
                print("🔄 Usando Fallback GROQ...")
                client = Groq(api_key=self.groq_key)
                completion = client.chat.completions.create(
                    model="llama-3.1-8b-instant",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.2
                )
                return self._parse_json(completion.choices[0].message.content)
            except Exception as e:
                print(f"❌ Fallo Groq: {e}")

        return {"prediction": "Error", "win_probability": 0, "confidence": 0, "reasoning": "IA offline"}

    def _parse_json(self, text):
        try:
            # 1. Limpieza agresiva de Markdown (```json ... ```)
            text = text.replace("```json", "").replace("```", "").strip()
            
            # 2. Búsqueda del primer '{' y el último '}' para aislar el objeto JSON
            start = text.find("{")
            end = text.rfind("}") + 1
            
            if start != -1 and end != 0:
                text = text[start:end]
                data = json.loads(text)
                
                # 3. Normalización de datos numéricos
                # A veces la IA devuelve strings "60%" en vez de números 0.60
                if 'win_probability' in data:
                    if isinstance(data['win_probability'], str):
                        clean_prob = data['win_probability'].replace('%', '')
                        # Si es mayor a 1 (ej. 60), dividir por 100. Si es 0.60, dejar igual.
                        data['win_probability'] = float(clean_prob) / 100 if float(clean_prob) > 1 else float(clean_prob)
                
                return data
            else:
                raise ValueError("No se encontraron llaves JSON {} en la respuesta")
                
        except Exception as e:
            print(f"❌ Error parseando JSON de IA: {e}")
            print(f"📄 Texto recibido (DEBUG): {text}") # Para ver qué nos mandó la IA realmente
            return {
                "prediction": "Error Formato",
                "selection_code": "X", # Default seguro (Empate) para no romper el frontend
                "win_probability": 0,
                "confidence": 0,
                "reasoning": "La IA generó una respuesta no legible. Intenta analizar de nuevo.",
                "risk_level": "High"
            }