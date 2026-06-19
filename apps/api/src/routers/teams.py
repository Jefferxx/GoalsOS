import time
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, Request
from fastapi.concurrency import run_in_threadpool
from sqlmodel import Session, select, or_

from src.db.session import get_session
from src.models.match import Match
from src.models.team_form_cache import TeamFormCache
from src.services.football.real_service import RealFootballService
from src.utils.security import get_current_user
from src.utils.rate_limit import limiter

router = APIRouter(prefix="/teams", tags=["Teams"])

football_service = RealFootballService()
CACHE_TTL_HOURS = 18


def _extract_stat(team_stats: dict, stat_type: str) -> int:
    for s in team_stats.get("statistics", []):
        if s.get("type") == stat_type:
            return s.get("value") or 0
    return 0


def _compute_form(session: Session, team_id: int, last: int) -> dict:
    """
    Construye el histórico desde los partidos que GoalOS ya ingirió en su
    propia base de datos (no desde /fixtures?team=, que el plan free de
    API-Football restringe por temporada). Por cada partido encontrado se
    hacen 2 llamadas reales: detalle (marcador por tiempo) + estadísticas
    (corners/tarjetas).
    """
    own_matches = session.exec(
        select(Match)
        .where(or_(Match.home_team_id == team_id, Match.away_team_id == team_id))
        .where(Match.status == "FT")
        .order_by(Match.date.desc())
        .limit(last)
    ).all()

    matches_table = []
    team_name = None
    over_15 = over_25 = btts = 0
    total_cards = total_corners = 0
    sample = 0

    for match in own_matches:
        is_home = match.home_team_id == team_id
        team_name = match.home_team if is_home else match.away_team
        opponent = match.away_team if is_home else match.home_team

        goals_home = match.home_score or 0
        goals_away = match.away_score or 0
        total_goals = goals_home + goals_away
        team_goals = goals_home if is_home else goals_away
        opp_goals = goals_away if is_home else goals_home
        result = "W" if team_goals > opp_goals else ("D" if team_goals == opp_goals else "L")

        # Detalle del fixture (para el marcador de 1er tiempo) + estadísticas
        detail = football_service.get_fixture_by_id(match.api_id)
        time.sleep(1)
        stats_resp = football_service.get_fixture_statistics(match.api_id)
        time.sleep(1)

        halftime = ((detail or {}).get("score") or {}).get("halftime") or {}
        ht_home = halftime.get("home") or 0
        ht_away = halftime.get("away") or 0
        goals_1st = ht_home if is_home else ht_away
        goals_2nd = team_goals - goals_1st

        corners = cards = 0
        for team_stats in stats_resp:
            if (team_stats.get("team") or {}).get("id") == team_id:
                corners = _extract_stat(team_stats, "Corner Kicks")
                cards = _extract_stat(team_stats, "Yellow Cards") + _extract_stat(team_stats, "Red Cards")

        if total_goals > 1.5: over_15 += 1
        if total_goals > 2.5: over_25 += 1
        if goals_home > 0 and goals_away > 0: btts += 1
        total_cards += cards
        total_corners += corners
        sample += 1

        matches_table.append({
            "date": match.date.isoformat(),
            "opponent": opponent,
            "result": f"{result} {team_goals}-{opp_goals}",
            "corners": corners,
            "cards": cards,
            "goals_1st": goals_1st,
            "goals_2nd": goals_2nd,
        })

    stats = {
        "over_1_5_pct": round(100 * over_15 / sample) if sample else 0,
        "over_2_5_pct": round(100 * over_25 / sample) if sample else 0,
        "btts_pct": round(100 * btts / sample) if sample else 0,
        "avg_cards": round(total_cards / sample, 1) if sample else 0,
        "avg_corners": round(total_corners / sample, 1) if sample else 0,
        "sample_size": sample,
    }

    return {"team_name": team_name, "stats": stats, "matches_table": matches_table}


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
        cached = session.exec(select(TeamFormCache).where(TeamFormCache.team_id == team_id)).first()
        if cached and (datetime.utcnow() - cached.fetched_at) < timedelta(hours=CACHE_TTL_HOURS):
            return {
                "team_id": team_id,
                "team_name": cached.team_name,
                "cached": True,
                "cached_at": cached.fetched_at.isoformat(),
                "stats": cached.stats,
                "matches": cached.matches_table,
            }

        result = _compute_form(session, team_id, last)

        if cached:
            cached.team_name = result["team_name"]
            cached.last_n = last
            cached.stats = result["stats"]
            cached.matches_table = result["matches_table"]
            cached.fetched_at = datetime.utcnow()
            session.add(cached)
        else:
            session.add(TeamFormCache(
                team_id=team_id,
                team_name=result["team_name"],
                last_n=last,
                stats=result["stats"],
                matches_table=result["matches_table"],
            ))
        session.commit()

        return {
            "team_id": team_id,
            "team_name": result["team_name"],
            "cached": False,
            "cached_at": datetime.utcnow().isoformat(),
            "stats": result["stats"],
            "matches": result["matches_table"],
        }

    return await run_in_threadpool(handler)
