"""
GoalOS — Resolución de λ (xG) por partido
============================================
Fallback chain compartida por /analysis/predict/{id} y por el motor de
picks múltiples de la IA (ai.py):
  1. xG real de Understat (solo ligas soportadas)
  2. xG implícito desde api_prediction de API-Football (DB)
  3. xG neutral de liga (con aviso explícito)
"""

from __future__ import annotations

import logging
from typing import Optional

from src.models.match import Match
from src.services.scrapers.understat import UnderstatScraper

logger = logging.getLogger("goalos.services.xg_resolver")

_understat_scraper = UnderstatScraper()

# Solo las ligas que Understat tiene disponibles
LEAGUE_ID_TO_UNDERSTAT: dict[int, str] = {
    39:  "EPL",         # Premier League
    140: "La_liga",     # La Liga
    78:  "Bundesliga",  # Bundesliga
    135: "Serie_A",     # Serie A
    61:  "Ligue_1",     # Ligue 1
}

# xG neutral por liga cuando todos los fallbacks fallan
# Basado en promedios históricos europeos (Caley, 2014-2024)
NEUTRAL_XG: dict[str, tuple[float, float]] = {
    "EPL":        (1.53, 1.14),
    "La_liga":    (1.47, 1.08),
    "Bundesliga": (1.68, 1.22),
    "Serie_A":    (1.38, 1.05),
    "Ligue_1":    (1.45, 1.10),
    "DEFAULT":    (1.35, 1.10),
}


def extract_xg_from_api_prediction(match: Match) -> tuple[Optional[float], Optional[float]]:
    """
    Extrae xG implícito desde api_prediction de API-Football.

    API-Football /predictions devuelve porcentajes de victoria:
      { "predictions": { "percent": { "home": "55%", "draw": "25%", "away": "20%" } } }

    Convertimos esos porcentajes a lambdas usando una heurística calibrada
    (no es xG real, es una aproximación cuando no hay datos de Understat).
    """
    try:
        pred = match.api_prediction
        if not pred:
            return None, None

        response = pred if isinstance(pred, dict) else {}
        if "response" in response:
            response = response["response"][0] if response["response"] else {}

        percent = response.get("predictions", {}).get("percent", {})
        if not percent:
            return None, None

        def parse_pct(val) -> float:
            if isinstance(val, str):
                return float(val.replace("%", "")) / 100
            return float(val) / 100 if float(val) > 1 else float(val)

        p_home = parse_pct(percent.get("home", 0))
        p_away = parse_pct(percent.get("away", 0))

        if p_home <= 0 or p_away <= 0:
            return None, None

        total_lambda = 2.65  # promedio empírico de goles/partido en ligas top
        ratio = p_home / (p_home + p_away)
        lambda_home = total_lambda * ratio
        lambda_away = total_lambda * (1 - ratio)

        return round(lambda_home, 3), round(lambda_away, 3)

    except Exception as e:
        logger.warning(f"⚠️ [Fallback API] Error extrayendo xG implícito: {e}")
        return None, None


async def resolve_match_lambdas(match: Match, season: int = 2024) -> tuple[float, float, str, bool]:
    """
    Devuelve (lambda_home, lambda_away, xg_source, neutral_used) siguiendo el
    fallback Understat -> xG implícito de api_prediction -> xG neutral por liga.
    """
    lambda_home: Optional[float] = None
    lambda_away: Optional[float] = None
    xg_source = "unknown"

    understat_slug = LEAGUE_ID_TO_UNDERSTAT.get(match.league_id)

    if understat_slug:
        try:
            lambda_home, lambda_away = await _understat_scraper.get_match_lambdas(
                home_team=match.home_team,
                away_team=match.away_team,
                league_slug=understat_slug,
                season=season,
            )
            if lambda_home and lambda_away:
                xg_source = f"understat/{understat_slug}/{season}"
        except Exception as e:
            logger.warning(f"⚠️ [Understat] Fallo en scraping: {e}. Activando fallback.")

    if not lambda_home or not lambda_away:
        lambda_home, lambda_away = extract_xg_from_api_prediction(match)
        if lambda_home and lambda_away:
            xg_source = "api_football_prediction_derived"

    neutral_used = False
    if not lambda_home or not lambda_away:
        neutral_key = understat_slug or "DEFAULT"
        lambda_home, lambda_away = NEUTRAL_XG.get(neutral_key, NEUTRAL_XG["DEFAULT"])
        xg_source = f"neutral_average/{neutral_key}"
        neutral_used = True
        logger.warning(
            f"⚠️ [Predicción] Usando xG neutral ({neutral_key}) para "
            f"{match.home_team} vs {match.away_team}. Confianza reducida."
        )

    return lambda_home, lambda_away, xg_source, neutral_used
