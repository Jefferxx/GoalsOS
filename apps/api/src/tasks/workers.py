import datetime
import time
from typing import List
from celery import shared_task
from sqlmodel import select

from src.db.session import SessionLocal
from src.models.match import Match
from src.services.football.real_service import RealFootballService
from src.services.football.mapper import DataMapper
from src.services.football.result_service import ResultAuditor
from src.tasks.ingestion import PRIORITY_LEAGUES, ALLOWED_LEAGUES  # Fuente única de verdad

import pytz
ECUADOR_TZ = pytz.timezone('America/Guayaquil')

def get_ecuador_now():
    return datetime.datetime.now(ECUADOR_TZ)

@shared_task(name="src.tasks.workers.run_ingestion_worker")
def run_ingestion_worker(dates: List[str], audit_mode: bool = False):
    """
    Worker V4 con Lógica Silicon Valley:
    1. Tier System: Prioriza ligas top.
    2. Reserve Tank: Se detiene a las 85 llamadas.
    3. Audit Mode: Si es True, solo actualiza marcadores.
    """
    session = SessionLocal()
    football_service = RealFootballService()
    
    processed_count = 0
    MAX_API_CALLS_SESSION = 85


    try:
        print(f"🦅 Worker V4 iniciado. Fechas: {dates}. AuditMode: {audit_mode}")
        for date_str in dates:
            if processed_count >= MAX_API_CALLS_SESSION and not audit_mode: 
                print("🛑 Tanque de Reserva alcanzado (85 calls). Deteniendo ingesta masiva.")
                break

            print(f"📅 Solicitando Fixtures para: {date_str}")
            fixtures_json = football_service.get_fixtures_by_date(date_str)
            print("⏳ Enfriando (7s)...")
            time.sleep(7) 
            
            if not fixtures_json: continue

            fixtures_json.sort(key=lambda x: 0 if x["league"]["id"] in PRIORITY_LEAGUES else 1)

            for fixture_data in fixtures_json:
                if processed_count >= MAX_API_CALLS_SESSION and not audit_mode: break
                
                league_id = fixture_data["league"]["id"]
                if league_id not in ALLOWED_LEAGUES: continue 
                    
                api_id = str(fixture_data["fixture"]["id"])
                home_team = fixture_data['teams']['home']['name']
                current_status = fixture_data['fixture']['status']['short']
                home_score = fixture_data['goals']['home']
                away_score = fixture_data['goals']['away']
                
                existing_match = session.exec(select(Match).where(Match.api_id == api_id)).first()
                
                if audit_mode:
                    if existing_match:
                        if existing_match.status != current_status or existing_match.home_score != home_score or existing_match.away_score != away_score:
                            existing_match.status = current_status
                            existing_match.home_score = home_score
                            existing_match.away_score = away_score
                            session.add(existing_match)
                            session.commit()
                    continue 

                needs_full_update = False
                if not existing_match: needs_full_update = True
                elif not existing_match.odds_data and current_status not in ['FT', 'AET', 'PEN']: needs_full_update = True
                
                if needs_full_update:
                    odds_json = football_service.get_odds(api_id)
                    time.sleep(7)
                    injuries_json = football_service.get_injuries(api_id)
                    time.sleep(7)
                    prediction_json = football_service.get_predictions(api_id)
                    time.sleep(7)
                    
                    match_obj = DataMapper.fixture_to_match(fixture_data, odds_data=odds_json)
                    match_obj = DataMapper.update_tactical_data(match_obj, injuries=injuries_json, lineups=[], prediction=prediction_json)
                    
                    if existing_match:
                        existing_match.odds_data = match_obj.odds_data
                        existing_match.injuries = match_obj.injuries 
                        existing_match.api_prediction = match_obj.api_prediction
                        existing_match.status = match_obj.status
                        existing_match.home_score = match_obj.home_score
                        existing_match.away_score = match_obj.away_score
                        session.add(existing_match)
                    else:
                        session.add(match_obj)
                    
                    processed_count += 3 
                    session.commit()
                
                elif existing_match:
                    if existing_match.status != current_status or existing_match.home_score != home_score or existing_match.away_score != away_score:
                        existing_match.status = current_status
                        existing_match.home_score = home_score
                        existing_match.away_score = away_score
                        session.add(existing_match)
                        session.commit()
            
    except Exception as e:
        print(f"🔥 Error Worker: {e}")
        session.rollback()
    finally:
        session.close()

@shared_task(name="src.tasks.workers.scheduled_sync_job")
def scheduled_sync_job():
    """05:00 AM: Descarga Inteligente (Estrategia Francotirador)"""
    today_str = get_ecuador_now().strftime("%Y-%m-%d")
    run_ingestion_worker([today_str])

@shared_task(name="src.tasks.workers.scheduled_audit_job")
def scheduled_audit_job():
    """23:55 PM: Cierre de Caja (Auditoría Lazy)"""
    session = SessionLocal()
    try:
        today_str = get_ecuador_now().strftime("%Y-%m-%d")
        run_ingestion_worker([today_str], audit_mode=True) 
        auditor = ResultAuditor(session)
        auditor.audit_pending_bets()
    except Exception as e:
        print(f"🔥 Error en Auditoría Nocturna: {e}")
    finally:
        session.close()
