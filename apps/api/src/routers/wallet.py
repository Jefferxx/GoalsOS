from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from pydantic import BaseModel

from src.db.session import get_session
from src.models.user import User
from src.models.bet import Bet
from src.models.match import Match # <--- IMPORTANTE: Necesario para el JOIN

router = APIRouter(prefix="/wallet", tags=["Wallet"])

# Esquema para actualizar saldo
class BankrollUpdate(BaseModel):
    user_email: str
    new_balance: float

@router.get("/{email}")
def get_balance(email: str, session: Session = Depends(get_session)):
    """Obtiene el saldo actual del usuario."""
    user = session.exec(select(User).where(User.email == email)).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return {"bankroll": user.bankroll}

# --- NUEVO ENDPOINT DE ESTADÍSTICAS REALES ---
@router.get("/stats/roi/{email}")
def get_roi_stats(email: str, session: Session = Depends(get_session)):
    """
    Calcula el ROI total, Profit/Loss y Strike Rate basado en historial real.
    """
    user = session.exec(select(User).where(User.email == email)).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    # Obtener SOLO apuestas finalizadas (WON o LOST)
    bets = session.exec(select(Bet).where(Bet.user_id == user.id).where(Bet.status.in_(["WON", "LOST"]))).all()

    # CORRECCIÓN: Usamos 'stake' en lugar de 'amount'
    total_invested = sum([b.stake for b in bets])
    total_returned = 0
    wins = 0
    losses = 0

    for bet in bets:
        if bet.status == "WON":
            # Ganancia total = monto apostado * cuota
            # CORRECCIÓN: Usamos 'stake'
            total_returned += (bet.stake * bet.odds)
            wins += 1
        elif bet.status == "LOST":
            losses += 1

    net_profit = total_returned - total_invested
    
    roi_percent = 0.0
    if total_invested > 0:
        roi_percent = (net_profit / total_invested) * 100

    strike_rate = 0.0
    if len(bets) > 0:
        strike_rate = (wins / len(bets)) * 100

    return {
        "total_invested": round(total_invested, 2),
        "total_returned": round(total_returned, 2),
        "net_profit": round(net_profit, 2),
        "roi_percent": round(roi_percent, 2),
        "total_bets": len(bets),
        "wins": wins,
        "losses": losses,
        "strike_rate": round(strike_rate, 1)
    }

# --- NUEVO: HISTORIAL COMPLETO (JOIN) ---
@router.get("/history/{email}")
def get_betting_history(email: str, session: Session = Depends(get_session)):
    """Devuelve el historial de apuestas con los datos del partido asociado."""
    user = session.exec(select(User).where(User.email == email)).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    # JOIN: Traeme la Apuesta Y el Partido correspondiente
    statement = select(Bet, Match).join(Match).where(Bet.user_id == user.id).order_by(Bet.created_at.desc())
    results = session.exec(statement).all()
    
    history_log = []
    for bet, match in results:
        # Calculamos ganancia neta para mostrar
        profit = 0
        if bet.status == "WON":
            profit = (bet.stake * bet.odds) - bet.stake
        elif bet.status == "LOST":
            profit = -bet.stake
            
        history_log.append({
            "bet_id": bet.id,
            "date": match.date,
            "league": match.league_name,
            "match": f"{match.home_team} vs {match.away_team}",
            "selection": bet.selection,
            "odds": bet.odds,
            "stake": bet.stake,
            "status": bet.status, # PENDING, WON, LOST
            "score": f"{match.home_score}-{match.away_score}" if match.home_score is not None else "?-?",
            "profit": round(profit, 2)
        })
        
    return history_log

@router.post("/sync")
def sync_balance(data: BankrollUpdate, session: Session = Depends(get_session)):
    """
    Sincronización Manual: Fuerza el saldo de GoalOS para que coincida con Betano.
    """
    user = session.exec(select(User).where(User.email == data.user_email)).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    # Actualizamos el saldo
    previous = user.bankroll
    user.bankroll = data.new_balance
    
    session.add(user)
    session.commit()
    session.refresh(user)
    
    return {
        "status": "Sincronizado", 
        "previous": previous, 
        "current": user.bankroll,
        "message": "Tu banca ahora coincide con la realidad."
    }