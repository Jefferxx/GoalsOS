import os
import json
import time
import threading
import collections
import datetime
import asyncio
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from groq import Groq
from sqlmodel import Session

from src.services.football.mapper import DataMapper
from src.services.football.team_form import get_team_market_rates
from src.services.math.poisson import PoissonEngine
from src.services.math.xg_resolver import resolve_match_lambdas

# Límites del plan free de Gemini 3.1 Flash Lite (confirmados por el usuario)
GEMINI_RPM_LIMIT = 15
GEMINI_RPD_LIMIT = 500


class _GeminiRateLimiter:
    """Limitador en proceso: ventana deslizante de 60s para RPM + contador diario para RPD.
    No reemplaza el rate limit real de Google, solo evita que GoalOS se autoinduzca
    un 429 disparando más de lo permitido y cayendo a Groq innecesariamente."""

    def __init__(self):
        self._lock = threading.Lock()
        self._minute_window = collections.deque()
        self._day = time.strftime("%Y-%m-%d")
        self._day_count = 0

    def allow(self) -> bool:
        with self._lock:
            now = time.time()
            today = time.strftime("%Y-%m-%d")
            if today != self._day:
                self._day = today
                self._day_count = 0

            while self._minute_window and now - self._minute_window[0] > 60:
                self._minute_window.popleft()

            if len(self._minute_window) >= GEMINI_RPM_LIMIT or self._day_count >= GEMINI_RPD_LIMIT:
                return False

            self._minute_window.append(now)
            self._day_count += 1
            return True


_gemini_limiter = _GeminiRateLimiter()


class FootballAI:
    def __init__(self):
        self.google_key = os.getenv("GOOGLE_API_KEY")
        self.groq_key = os.getenv("GROQ_API_KEY")
        self.model = None
        self.poisson_engine = PoissonEngine()

        if self.google_key:
            try:
                genai.configure(api_key=self.google_key)
                self.model = genai.GenerativeModel(
                    'models/gemini-3.1-flash-lite',
                    safety_settings={
                        HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                        HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                        HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                        HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
                    },
                    generation_config=genai.GenerationConfig(
                        response_mime_type="application/json",
                    ),
                )
                print("✅ AI Service: Gemini 3.1 Flash Lite configurado (JSON mode).")
            except Exception as e:
                print(f"⚠️ AI Service: Error configurando Gemini: {e}")

    async def _compute_candidate_picks(self, match, session: Session = None) -> list[dict]:
        """
        Capa estadística real (no inventada por el LLM): resuelve λ de goles
        (Understat → xG implícito → neutral) y λ propios de corners/tarjetas
        por equipo (histórico de GoalOS), y corre el PoissonEngine extendido.
        """
        lambda_home, lambda_away, _, _ = await resolve_match_lambdas(match)
        lambda_home_adj = lambda_home * 1.10  # ventaja de local, igual que /analysis/predict

        home_rates = {"corners_lambda": None, "cards_lambda": None, "first_half_ratio": 0.45}
        away_rates = {"corners_lambda": None, "cards_lambda": None, "first_half_ratio": 0.45}
        if session is not None and match.home_team_id and match.away_team_id:
            try:
                # Secuencial (no asyncio.gather): get_team_market_rates puede bloquear
                # con time.sleep en cache-miss, y comparten la misma Session de SQLAlchemy
                # (no es thread-safe para uso concurrente) — to_thread evita bloquear el
                # event loop sin arriesgar dos hilos tocando la sesión a la vez.
                home_rates = await asyncio.to_thread(get_team_market_rates, session, match.home_team_id)
                away_rates = await asyncio.to_thread(get_team_market_rates, session, match.away_team_id)
            except Exception as e:
                print(f"⚠️ No se pudieron derivar λ de corners/tarjetas: {e}")

        return self.poisson_engine.analyze_full(
            lambda_home=lambda_home_adj,
            lambda_away=lambda_away,
            corners_lambda_home=home_rates.get("corners_lambda"),
            corners_lambda_away=away_rates.get("corners_lambda"),
            cards_lambda_home=home_rates.get("cards_lambda"),
            cards_lambda_away=away_rates.get("cards_lambda"),
            first_half_ratio_home=home_rates.get("first_half_ratio", 0.45),
            first_half_ratio_away=away_rates.get("first_half_ratio", 0.45),
        )

    async def analyze_match(self, match_data, session: Session = None):
        """
        Motor de picks múltiples: el PoissonEngine calcula las probabilidades
        reales de cada mercado (ganador, goles totales/por equipo, BTTS,
        corners, tarjetas, 1ª mitad); la IA solo selecciona los más sólidos,
        les agrega riesgo/razón y los ordena — no inventa probabilidades.
        """
        home = getattr(match_data, 'home_team', None) or match_data.get('home_team')
        away = getattr(match_data, 'away_team', None) or match_data.get('away_team')
        league = getattr(match_data, 'league_name', None) or match_data.get('league_name')

        context = DataMapper.get_ai_context(match_data)

        try:
            candidate_picks = await self._compute_candidate_picks(match_data, session)
        except Exception as e:
            print(f"⚠️ Motor Poisson no disponible para este partido: {e}")
            candidate_picks = []

        if not candidate_picks:
            return {
                "summary": "Datos insuficientes para calcular picks estadísticos de este partido.",
                "generated_at": datetime.datetime.utcnow().isoformat(),
                "picks": [],
            }

        picks_table = "\n".join(
            f"- {p['market']} · {p['selection']}: {p['probability']:.0%}"
            for p in candidate_picks[:12]
        )

        prompt = f"""
        Actúa como un Analista Cuantitativo de Élite especializado en Gestión de Riesgo.
        Ya tienes las probabilidades REALES calculadas por un motor estadístico
        (distribución de Poisson sobre xG y datos históricos del equipo). NO inventes
        ni cambies ningún número de probabilidad — solo selecciona, explica y ordena.

        EVENTO: {home} vs {away} ({league})

        CONTEXTO TÁCTICO:
        1. FORMA/PREDICCIÓN: {context.get('form_analysis', 'Sin datos')}
        2. H2H: {context.get('h2h_trends', 'Sin datos')}
        3. LESIONES: {context.get('injury_report', 'Sin datos')}
        4. CUOTAS: {context.get('odds_summary', 'Sin datos')}

        PICKS CANDIDATOS (probabilidad ya calculada, no la modifiques):
        {picks_table}

        TU TAREA:
        1. Elige los 5-6 picks más sólidos de la lista (puedes combinar mercados distintos).
        2. Para cada uno, usa EXACTAMENTE el "market", "selection" y "probability" de la lista.
        3. Agrega "confidence" (0-100, tu confianza cualitativa) y "risk_level" (Low/Medium/High).
        4. Agrega una "reasoning" breve combinando el dato estadístico con el contexto táctico.
        5. Agrega un "summary" de 1-2 frases con la lectura general del partido.
        6. Responde SOLO con JSON puro, sin texto extra.

        FORMATO:
        {{
            "summary": "Lectura general del partido",
            "picks": [
                {{"market": "...", "selection": "...", "probability": 0.00, "confidence": 0, "risk_level": "Low/Medium/High", "reasoning": "..."}}
            ]
        }}
        """

        result = None
        if self.model:
            if _gemini_limiter.allow():
                try:
                    response = self.model.generate_content(prompt)
                    result = self._parse_json(response.text)
                except Exception as e:
                    error_str = str(e)
                    if "429" in error_str or "ResourceExhausted" in error_str or "quota" in error_str.lower():
                        print(f"⚠️ Gemini: cuota/rate-limit excedido (429): {e}")
                    else:
                        print(f"⚠️ Fallo Gemini: {e}")
            else:
                print("⚠️ Gemini: límite interno RPM/RPD alcanzado, usando fallback Groq.")

        if result is None and self.groq_key:
            try:
                print("🔄 Usando Fallback GROQ...")
                client = Groq(api_key=self.groq_key)
                completion = client.chat.completions.create(
                    model="llama-3.1-8b-instant",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.2,
                    max_tokens=1536,
                    response_format={"type": "json_object"},
                )
                result = self._parse_json(completion.choices[0].message.content)
            except Exception as e:
                print(f"❌ Fallo Groq: {e}")

        if result is None or not result.get("picks"):
            # Sin IA disponible (o respuesta no legible): degradamos a los picks
            # crudos del Poisson, sin razonamiento cualitativo, pero con números reales.
            result = {
                "summary": "IA no disponible: se muestran los picks estadísticos sin razonamiento cualitativo.",
                "picks": [
                    {**p, "confidence": round(p["probability"] * 100), "risk_level": "Medium", "reasoning": "Calculado por el motor Poisson."}
                    for p in candidate_picks[:6]
                ],
            }

        result["generated_at"] = datetime.datetime.utcnow().isoformat()
        result["picks"] = sorted(result.get("picks", []), key=lambda p: p.get("probability", 0), reverse=True)
        return result

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

                # Normalización: a veces la IA devuelve "probability"/"win_probability"
                # como strings "60%" en vez de números 0.60
                for pick in data.get("picks", []):
                    prob = pick.get("probability")
                    if isinstance(prob, str):
                        clean = prob.replace('%', '')
                        pick["probability"] = float(clean) / 100 if float(clean) > 1 else float(clean)

                return data
            else:
                raise ValueError("No se encontraron llaves JSON {} en la respuesta")

        except Exception as e:
            print(f"❌ Error parseando JSON de IA: {e}")
            print(f"📄 Texto recibido (DEBUG): {text}")  # Para ver qué nos mandó la IA realmente
            return None
