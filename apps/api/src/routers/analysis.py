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
from src.services.math.xg_resolver import resolve_match_lambdas
from src.utils.security import get_current_user

logger = logging.getLogger("goalos.routers.analysis")

router = APIRouter(prefix="/analysis", tags=["Análisis Predictivo"])

# Instancia singleton (sin estado mutable, es thread-safe)
_poisson_engine = PoissonEngine()


# ─── HELPERS DE ODDS ───────────────────────────────────────────────────────────

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

    # ── 2-4. Resolver λ (Understat → xG implícito → xG neutral) ─────────────
    lambda_home, lambda_away, xg_source, neutral_used = await resolve_match_lambdas(match, season)

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
