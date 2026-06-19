"""
GoalOS — Auto-análisis pre-partido
====================================
Cada ~10 minutos, busca partidos a 20-40 minutos del kickoff. En cuanto
las alineaciones se confirman (get_lineups ya no devuelve vacío), corre
el mismo motor de picks múltiples que el endpoint manual (Poisson
extendido + IA rankeando) y notifica por Telegram — sin que el usuario
tenga que pedirlo.
"""

import os
import asyncio
import datetime

import redis
from celery import shared_task
from sqlmodel import select

from src.db.session import SessionLocal
from src.models.match import Match
from src.services.ai import FootballAI
from src.services.football.real_service import RealFootballService
from src.utils.notifications import send_telegram_alert

QUOTA_CACHE_KEY = "goalos:api_football:quota_remaining"
QUOTA_CACHE_TTL_SECONDS = 300  # 5 min: evita gastar una request de /status en cada tick de 10min
QUOTA_SAFETY_MARGIN = 15

_redis_client = redis.Redis.from_url(os.getenv("REDIS_URL", "redis://redis:6379/1"))


def _get_cached_quota_remaining(football_service: RealFootballService) -> int:
    cached = _redis_client.get(QUOTA_CACHE_KEY)
    if cached is not None:
        return int(cached)

    status = football_service._get("status")
    requests_info = (status or {}).get("requests", {})
    remaining = requests_info.get("limit_day", 100) - requests_info.get("current", 0)
    _redis_client.set(QUOTA_CACHE_KEY, remaining, ex=QUOTA_CACHE_TTL_SECONDS)
    return remaining


@shared_task(name="src.tasks.pregame.scan_upcoming_kickoffs")
def scan_upcoming_kickoffs():
    """
    Ventana de 20-40min antes del kickoff: si las alineaciones ya están
    confirmadas, genera los picks y avisa por Telegram. Si todavía no hay
    alineaciones, no hace nada y se reintenta en el próximo tick (cada
    ~10min) hasta que se confirmen o el partido salga de la ventana.
    """
    session = SessionLocal()
    football_service = RealFootballService()
    ai_service = FootballAI()

    try:
        now = datetime.datetime.utcnow()
        window_start = now + datetime.timedelta(minutes=20)
        window_end = now + datetime.timedelta(minutes=40)

        candidates = session.exec(
            select(Match)
            .where(Match.date >= window_start)
            .where(Match.date <= window_end)
            .where(Match.auto_analyzed == False)
            .where(Match.status == "NS")
        ).all()

        if not candidates:
            return "Sin partidos en ventana de 20-40min."

        remaining = _get_cached_quota_remaining(football_service)
        if remaining < QUOTA_SAFETY_MARGIN:
            print(f"🛑 Auto-análisis pre-partido abortado: cuota insuficiente ({remaining}).")
            return f"Abortado: solo {remaining} requests restantes hoy"

        processed = []
        for match in candidates:
            lineups = football_service.get_lineups(match.api_id)
            if not lineups:
                continue  # alineaciones aún no confirmadas, se reintenta en el próximo tick

            match.lineups = lineups
            session.add(match)
            session.commit()

            print(f"🤖 [Auto-análisis] Alineaciones confirmadas: {match.home_team} vs {match.away_team}")
            analysis_result = asyncio.run(ai_service.analyze_match(match, session))

            match.ai_analysis = analysis_result
            match.auto_analyzed = True
            session.add(match)
            session.commit()

            top_picks = analysis_result.get("picks", [])[:3]
            picks_text = "\n".join(
                f"• {p['market']}: {p['selection']} ({p['probability']:.0%})" for p in top_picks
            ) or "Sin picks sólidos para este partido."

            send_telegram_alert(
                f"Alineaciones confirmadas: {match.home_team} vs {match.away_team}\n"
                f"Picks principales:\n{picks_text}"
            )
            processed.append(match.api_id)

        return f"Procesados: {processed}" if processed else "Sin alineaciones confirmadas todavía."

    except Exception as e:
        print(f"🔥 Error en scan_upcoming_kickoffs: {e}")
        session.rollback()
        return f"Error: {e}"
    finally:
        session.close()
