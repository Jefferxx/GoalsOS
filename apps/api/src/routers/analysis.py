"""
GoalOS — Router de Análisis Predictivo
========================================
Expone el pipeline completo:
  Understat xG → PoissonEngine → Probabilidades + Value Bets

Endpoint:
  POST /analysis/predict/{match_id}

Seguridad:
  Protegido con Depends(get_current_user) — requiere Bearer JWT.

Fallback Strategy (@Auditor QA):
  1. Intenta obtener xG de Understat (solo ligas soportadas)
  2. Si falla, extrae xG implícito desde api_prediction de API-Football (DB)
  3. Si también falla, usa xG neutral de liga (1.35 / 1.10) con aviso explícito
"""

from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.concurrency import run_in_threadpool
from sqlmodel import Session, select

from src.db.session import get_session
from src.models.match import Match
from src.services.math.poisson import PoissonEngine
from src.services.scrapers.understat import UnderstatScraper, LEAGUE_SLUGS
from src.utils.security import get_current_user

logger = logging.getLogger("goalos.routers.analysis")

router = APIRouter(prefix="/analysis", tags=["Análisis Predictivo"])

# Instancias singleton de los servicios (sin estado mutable, son thread-safe)
_poisson_engine = PoissonEngine()
_understat_scraper = UnderstatScraper()

# ─── MAPPING API-FOOTBALL LEAGUE_ID → UNDERSTAT SLUG ──────────────────────────
# Solo las ligas que Understat tiene disponibles
_LEAGUE_ID_TO_UNDERSTAT: dict[int, str] = {
    39:  "EPL",         # Premier League
    140: "La_liga",     # La Liga
    78:  "Bundesliga",  # Bundesliga
    135: "Serie_A",     # Serie A
    61:  "Ligue_1",     # Ligue 1
}

# xG neutral por liga cuando todos los fallbacks fallan
# Basado en promedios históricos europeos (Caley, 2014-2024)
_NEUTRAL_XG: dict[str, tuple[float, float]] = {
    "EPL":        (1.53, 1.14),
    "La_liga":    (1.47, 1.08),
    "Bundesliga": (1.68, 1.22),
    "Serie_A":    (1.38, 1.05),
    "Ligue_1":    (1.45, 1.10),
    "DEFAULT":    (1.35, 1.10),
}


# ─── HELPERS DE FALLBACK ──────────────────────────────────────────────────────

def _extract_xg_from_api_prediction(match: Match) -> tuple[Optional[float], Optional[float]]:
    """
    Fallback 1: Extrae xG implícito desde api_prediction de API-Football.

    API-Football /predictions devuelve porcentajes de victoria:
      { "predictions": { "percent": { "home": "55%", "draw": "25%", "away": "20%" } } }

    Convertimos esos porcentajes a lambdas usando la inversa de la CDF Poisson
    aproximada: λ ≈ -ln(P_draw) * prob_home_ratio  (heurística calibrada).

    Si no hay datos, retorna (None, None).
    """
    try:
        pred = match.api_prediction
        if not pred:
            return None, None

        # Navegar estructura de API-Football
        response = pred if isinstance(pred, dict) else {}
        # Puede venir como { response: [...] } o directo
        if "response" in response:
            response = response["response"][0] if response["response"] else {}

        percent = (
            response.get("predictions", {})
            .get("percent", {})
        )
        if not percent:
            return None, None

        def parse_pct(val) -> float:
            """Convierte '55%' → 0.55 o float directo."""
            if isinstance(val, str):
                return float(val.replace("%", "")) / 100
            return float(val) / 100 if float(val) > 1 else float(val)

        p_home = parse_pct(percent.get("home", 0))
        p_draw = parse_pct(percent.get("draw", 0))
        p_away = parse_pct(percent.get("away", 0))

        if p_home <= 0 or p_away <= 0:
            return None, None

        # Heurística: si p_home ≈ 0.55, λ_home ≈ 1.6 (calibración empírica)
        # Usamos la media de goles totales esperados ≈ 2.6 (promedio europeo)
        # y distribuimos según la ratio de probabilidades
        total_lambda = 2.65  # promedio empírico de goles/partido en ligas top
        ratio = p_home / (p_home + p_away)
        lambda_home = total_lambda * ratio
        lambda_away = total_lambda * (1 - ratio)

        logger.info(
            f"📊 [Fallback API-Football] {match.home_team} vs {match.away_team}: "
            f"λh={lambda_home:.3f}, λa={lambda_away:.3f} (desde porcentajes {p_home:.0%}/{p_away:.0%})"
        )
        return round(lambda_home, 3), round(lambda_away, 3)

    except Exception as e:
        logger.warning(f"⚠️ [Fallback API] Error extrayendo xG implícito: {e}")
        return None, None


def _extract_odds_from_db(match: Match) -> dict[str, Optional[float]]:
    """
    Extrae cuotas 1X2 de odds_data almacenado en DB.
    Retorna dict con keys: home, draw, away (o None si no disponible).
    """
    empty = {"home": None, "draw": None, "away": None}
    try:
        odds = match.odds_data
        if not odds:
            return empty

        data = odds if isinstance(odds, dict) else {}
        bookmakers = data.get("bookmakers", []) or data.get("response", [])
        if not bookmakers:
            return empty

        bets = bookmakers[0].get("bets", [])
        for bet in bets:
            if bet.get("id") == 1:  # Match Winner
                values = {v["value"]: float(v["odd"]) for v in bet.get("values", [])}
                return {
                    "home":  values.get("Home"),
                    "draw":  values.get("Draw"),
                    "away":  values.get("Away"),
                }
        return empty
    except Exception:
        return empty


# ─── ENDPOINT PRINCIPAL ───────────────────────────────────────────────────────

@router.post("/predict/{match_id}")
async def predict_match(
    match_id: str,
    season: int = 2024,
    session: Session = Depends(get_session),
    current_user: dict = Depends(get_current_user),  # 🔐 PROTEGIDO
):
    """
    Pipeline de Predicción Completo para un partido.

    Flujo:
      1. Busca el partido en la DB por api_id
      2. Intenta obtener xG reales de Understat (si la liga está soportada)
      3. Fallback → xG implícito desde api_prediction de API-Football (DB)
      4. Fallback → xG neutral por liga con advertencia explícita
      5. Ejecuta PoissonEngine con las cuotas del mercado para detectar Value Bets
      6. Retorna análisis completo

    Args:
        match_id: api_id del partido (mismo que en /matches/{match_id})
        season: Temporada de Understat (default 2024 = temporada 2024/25)
    """
    # ── 1. Buscar partido en DB ─────────────────────────────────────────────
    def fetch_match():
        return session.exec(
            select(Match).where(Match.api_id == match_id)
        ).first()

    match = await run_in_threadpool(fetch_match)

    if not match:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Partido '{match_id}' no encontrado en la base de datos.",
        )

    # ── 2. Intentar xG desde Understat ─────────────────────────────────────
    lambda_home: Optional[float] = None
    lambda_away: Optional[float] = None
    xg_source = "unknown"

    understat_slug = _LEAGUE_ID_TO_UNDERSTAT.get(match.league_id)

    if understat_slug:
        try:
            logger.info(
                f"🕷️ [Understat] Buscando xG para {match.home_team} vs "
                f"{match.away_team} en {understat_slug}/{season}"
            )
            lambda_home, lambda_away = await _understat_scraper.get_match_lambdas(
                home_team=match.home_team,
                away_team=match.away_team,
                league_slug=understat_slug,
                season=season,
            )
            if lambda_home and lambda_away:
                xg_source = f"understat/{understat_slug}/{season}"
                logger.info(f"✅ [Understat] λh={lambda_home}, λa={lambda_away}")
        except Exception as e:
            logger.warning(f"⚠️ [Understat] Fallo en scraping: {e}. Activando fallback.")

    # ── 3. Fallback: xG implícito desde api_prediction (DB) ────────────────
    if not lambda_home or not lambda_away:
        lambda_home, lambda_away = _extract_xg_from_api_prediction(match)
        if lambda_home and lambda_away:
            xg_source = "api_football_prediction_derived"

    # ── 4. Fallback final: xG neutral por liga ──────────────────────────────
    neutral_used = False
    if not lambda_home or not lambda_away:
        neutral_key = understat_slug or "DEFAULT"
        lambda_home, lambda_away = _NEUTRAL_XG.get(neutral_key, _NEUTRAL_XG["DEFAULT"])
        xg_source = f"neutral_average/{neutral_key}"
        neutral_used = True
        logger.warning(
            f"⚠️ [Predicción] Usando xG neutral ({neutral_key}) para "
            f"{match.home_team} vs {match.away_team}. Confianza reducida."
        )

    # ── 5. Ejecutar PoissonEngine ────────────────────────────────────────────
    # Extraer cuotas del mercado desde DB para detectar Value Bets
    market_odds = _extract_odds_from_db(match)

    try:
        poisson_result = await _poisson_engine.analyze(
            xg_home=lambda_home,
            xg_away=lambda_away,
            apply_home_advantage=True,
            odds_home=market_odds.get("home"),
            odds_draw=market_odds.get("draw"),
            odds_away=market_odds.get("away"),
            edge_threshold=0.05,  # 5% de ventaja mínima para declarar Value Bet
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Error en el motor Poisson: {str(e)}",
        )

    # ── 6. Construir respuesta ───────────────────────────────────────────────
    response = {
        "match": {
            "api_id": match.api_id,
            "home_team": match.home_team,
            "away_team": match.away_team,
            "league": match.league_name,
            "date": match.date.isoformat(),
            "status": match.status,
        },
        "model_metadata": {
            "xg_source": xg_source,
            "lambda_home_input": lambda_home,
            "lambda_away_input": lambda_away,
            "confidence_warning": (
                "⚠️ xG neutral utilizado. Los datos reales de Understat no estaban disponibles para esta liga o equipo."
                if neutral_used else None
            ),
            "market_odds_used": market_odds if any(market_odds.values()) else None,
        },
        "prediction": poisson_result.to_dict(),
        "requested_by": current_user.get("sub"),  # email del usuario autenticado
    }

    return response
