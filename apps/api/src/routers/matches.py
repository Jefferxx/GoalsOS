import json
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.concurrency import run_in_threadpool
from sqlmodel import Session, select
from pydantic import BaseModel

from src.db.session import get_session
from src.models.match import Match
from src.services.ai import FootballAI
from src.services.football.result_service import ResultAuditor
from src.tasks.workers import run_ingestion_worker
from src.utils.security import get_current_user  # 🔐 Guard de autenticación
from src.utils.rate_limit import limiter

router = APIRouter(prefix="", tags=["Matches y Auditoría"])
ai_service = FootballAI()

@router.get("/audit/run")
async def run_audit(
    session: Session = Depends(get_session),
    current_user: dict = Depends(get_current_user),  # 🔐 PROTEGIDO
):
    def perform_audit():
        auditor = ResultAuditor(session)
        return auditor.audit_pending_bets()
    return await run_in_threadpool(perform_audit)

@router.get("/matches")
async def get_matches(session: Session = Depends(get_session)):
    def fetch_matches():
        return session.exec(select(Match).order_by(Match.date.desc())).all()
    
    matches = await run_in_threadpool(fetch_matches)
    return {"status": "success", "count": len(matches), "data": matches}

@router.get("/matches/{match_id}")
async def get_match(match_id: str, session: Session = Depends(get_session)):
    def fetch_single():
        return session.exec(select(Match).where(Match.api_id == match_id)).first()
        
    match = await run_in_threadpool(fetch_single)
    if not match: 
        raise HTTPException(status_code=404, detail="Match not found")
    return match

@router.post("/matches/{match_id}/analyze")
@limiter.limit("10/minute")
async def analyze_match(
    request: Request,
    match_id: str,
    session: Session = Depends(get_session),
    current_user: dict = Depends(get_current_user),  # 🔐 PROTEGIDO
):
    def process_analysis():
        match = session.exec(select(Match).where(Match.api_id == match_id)).first()
        if not match: return None
        
        if match.ai_analysis:
            try:
                if isinstance(match.ai_analysis, str): json.loads(match.ai_analysis)
            except: pass 
            
        print(f"🤖 Analizando: {match.home_team} vs {match.away_team}")
        analysis_result = ai_service.analyze_match(match)
        match.ai_analysis = analysis_result 
        
        session.add(match)
        session.commit()
        session.refresh(match)
        return match

    match = await run_in_threadpool(process_analysis)
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")
    return match

@router.get("/test/ingest")
async def test_full_ingestion(
    current_user: dict = Depends(get_current_user),  # 🔐 PROTEGIDO
):
    import datetime
    import pytz
    
    now_ec = datetime.datetime.now(pytz.timezone('America/Guayaquil'))
    today_str = now_ec.strftime("%Y-%m-%d")
    
    # Delegamos a Celery!
    run_ingestion_worker.delay([today_str])
    
    return {"status": "Celery Task Iniciada (Solo Hoy)", "dates": [today_str]}
