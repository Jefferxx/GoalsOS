from fastapi import APIRouter, Depends, Request
from fastapi.concurrency import run_in_threadpool
from sqlmodel import Session

from src.db.session import get_session
from src.services.football.team_form import get_or_compute_team_form
from src.utils.security import get_current_user
from src.utils.rate_limit import limiter

router = APIRouter(prefix="/teams", tags=["Teams"])


@router.get("/{team_id}/recent-form")
@limiter.limit("20/minute")
async def get_team_recent_form(
    request: Request,
    team_id: int,
    last: int = 5,
    session: Session = Depends(get_session),
    current_user: dict = Depends(get_current_user),
):
    """
    Últimos N partidos finalizados de un equipo (de los que GoalOS ya tiene
    en su propia base de datos) con corners/tarjetas/goles por tiempo, y
    agregados %over1.5, %over2.5, %BTTS. Cachea 18h en Postgres para no
    gastar cuota de API-Football en consultas repetidas del mismo equipo.

    NOTA: solo puede mostrar partidos que GoalOS ya haya ingerido (ligas
    permitidas en ingestion.py). El plan free de API-Football no permite
    consultar el historial completo de un equipo por temporada/last.
    """
    def handler():
        result = get_or_compute_team_form(session, team_id, last)
        return {
            "team_id": team_id,
            "team_name": result["team_name"],
            "cached": result["cached"],
            "cached_at": result["cached_at"].isoformat(),
            "stats": result["stats"],
            "matches": result["matches_table"],
        }

    return await run_in_threadpool(handler)
