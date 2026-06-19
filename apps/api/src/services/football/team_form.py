"""
GoalOS — Forma reciente por equipo (servicio)
================================================
Construye el histórico de un equipo desde los partidos que GoalOS ya
ingirió en su propia base de datos (no desde /fixtures?team=, que el plan
free de API-Football restringe por temporada), con caché de 18h en
Postgres. Usado tanto por el router HTTP (/teams/{id}/recent-form) como
por el motor de picks múltiples (ai.py) para derivar λ de corners/tarjetas
y el ratio de goles en 1ª mitad de cada equipo.
"""

from datetime import datetime, timedelta

from sqlmodel import Session, select, or_

from src.models.match import Match
from src.models.team_form_cache import TeamFormCache
from src.services.football.real_service import RealFootballService
from src.services.math.poisson import DEFAULT_FIRST_HALF_RATIO

football_service = RealFootballService()
CACHE_TTL_HOURS = 18


def _extract_stat(team_stats: dict, stat_type: str) -> int:
    for s in team_stats.get("statistics", []):
        if s.get("type") == stat_type:
            return s.get("value") or 0
    return 0


def _compute_form(session: Session, team_id: int, last: int) -> dict:
    """
    Por cada partido encontrado se hacen 2 llamadas reales: detalle
    (marcador por tiempo) + estadísticas (corners/tarjetas).
    """
    import time

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

        if match.statistics:
            stats_resp = match.statistics
            detail = None
        else:
            detail = football_service.get_fixture_by_id(match.api_id)
            time.sleep(1)
            stats_resp = football_service.get_fixture_statistics(match.api_id)
            time.sleep(1)

        halftime = ((detail or {}).get("score") or {}).get("halftime") or {} if detail else {}
        ht_home = halftime.get("home") or 0
        ht_away = halftime.get("away") or 0
        goals_1st = ht_home if is_home else ht_away
        goals_2nd = team_goals - goals_1st

        corners = cards = 0
        for team_stats in (stats_resp or []):
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


def get_or_compute_team_form(session: Session, team_id: int, last: int = 5) -> dict:
    """
    {team_name, stats, matches_table, cached, cached_at} — usa caché de 18h en
    Postgres para no gastar cuota de API-Football en consultas repetidas.
    """
    cached = session.exec(select(TeamFormCache).where(TeamFormCache.team_id == team_id)).first()
    if cached and (datetime.utcnow() - cached.fetched_at) < timedelta(hours=CACHE_TTL_HOURS):
        return {
            "team_name": cached.team_name,
            "stats": cached.stats,
            "matches_table": cached.matches_table,
            "cached": True,
            "cached_at": cached.fetched_at,
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

    return {**result, "cached": False, "cached_at": datetime.utcnow()}


def get_team_market_rates(session: Session, team_id: int) -> dict:
    """
    λ propios del equipo (corners/tarjetas, promedio por partido) y el ratio de
    sus propios goles que cae en la 1ª mitad — derivados del histórico ya
    cacheado de "Forma Reciente". Si no hay muestra, devuelve None en los λ
    (el motor Poisson simplemente no genera esos mercados) y el ratio de
    respaldo de la literatura para 1ª mitad.
    """
    form = get_or_compute_team_form(session, team_id, last=5)
    stats = form.get("stats") or {}
    matches = form.get("matches_table") or []

    sample = stats.get("sample_size", 0)
    if sample == 0:
        return {"corners_lambda": None, "cards_lambda": None, "first_half_ratio": DEFAULT_FIRST_HALF_RATIO}

    total_1st = sum(m.get("goals_1st", 0) for m in matches)
    total_2nd = sum(m.get("goals_2nd", 0) for m in matches)
    total_goals = total_1st + total_2nd
    first_half_ratio = (total_1st / total_goals) if total_goals > 0 else DEFAULT_FIRST_HALF_RATIO

    return {
        "corners_lambda": stats.get("avg_corners"),
        "cards_lambda": stats.get("avg_cards"),
        "first_half_ratio": first_half_ratio,
    }
