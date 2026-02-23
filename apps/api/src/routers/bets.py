from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from typing import List
from pydantic import BaseModel

from src.db.session import get_session
from src.models.bet import Bet
from src.models.match import Match
from src.models.user import User
from src.utils.notifications import send_telegram_alert

router = APIRouter(prefix="/bets", tags=["Bets"])

# --- ESQUEMAS ---
class BetCreate(BaseModel):
    match_api_id: str
    user_email: str
    selection: str
    odds: float
    stake: float
    strategy: str = "Manual"

# --- ENDPOINTS ---

@router.post("/", response_model=Bet)
def create_bet(bet_data: BetCreate, session: Session = Depends(get_session)):
    """
    Registra una apuesta con TRANSACCIONALIDAD ATÓMICA.
    Garantiza que el saldo solo se descuente si la apuesta se crea correctamente.
    """
    # 1. Buscar el Partido
    match = session.exec(select(Match).where(Match.api_id == bet_data.match_api_id)).first()
    if not match:
        raise HTTPException(status_code=404, detail="Partido no encontrado en el sistema")

    # 2. Buscar el Usuario
    user = session.exec(select(User).where(User.email == bet_data.user_email)).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    # VALIDACIÓN DE SEGURIDAD CRÍTICA: Cuotas mínimas
    if bet_data.odds < 1.01:
        raise HTTPException(
            status_code=400,
            detail="Error de Mercado: Las cuotas no están disponibles para este partido. Intenta sincronizar o espera unos minutos."
        )

    # 3. VERIFICACIÓN DE FONDOS
    if user.bankroll < bet_data.stake:
        raise HTTPException(
            status_code=400, 
            detail=f"Saldo insuficiente. Tienes ${user.bankroll}, intentas apostar ${bet_data.stake}"
        )

    # 4. EVITAR DUPLICADOS (Doble seguridad)
    existing_bet = session.exec(
        select(Bet)
        .where(Bet.user_id == user.id)
        .where(Bet.match_id == match.id)
    ).first()
    
    if existing_bet:
        raise HTTPException(status_code=400, detail="Ya has apostado en este partido.")

    # 5. Calcular Ganancia Potencial
    potential_payout = round(bet_data.stake * bet_data.odds, 2)

    # 6. Preparar la Apuesta
    # CORRECCIÓN CRÍTICA: Asignamos match_api_id explícitamente desde el objeto match
    new_bet = Bet(
        user_id=user.id,
        match_id=match.id,
        match_api_id=match.api_id, # <--- ¡LA LÍNEA MÁGICA QUE FALTABA!
        selection=bet_data.selection,
        odds=bet_data.odds,
        stake=bet_data.stake,
        potential_payout=potential_payout,
        strategy=bet_data.strategy,
        status="PENDING"
    )

    # 7. BLOQUE TRANSACCIONAL (Garantiza integridad financiera)
    try:
        user.bankroll -= bet_data.stake # Restamos el dinero
        session.add(user)    # Marcamos usuario para actualización
        session.add(new_bet) # Marcamos apuesta para inserción
        
        session.commit()     # Ejecutamos ambos cambios a la vez
        session.refresh(new_bet)
        
        # Alerta Telegram (Opcional)
        try:
            send_telegram_alert(
                f"💰 **Apuesta Confirmada**\n"
                f"Evento: {match.home_team} vs {match.away_team}\n"
                f"Pick: {bet_data.selection} (@{bet_data.odds})\n"
                f"Monto: ${bet_data.stake}\n"
                f"Nuevo Saldo: ${round(user.bankroll, 2)}"
            )
        except Exception as e:
            print(f"⚠️ Alerta Telegram no enviada: {e}")
        
    except Exception as e:
        session.rollback() # SI ALGO FALLA, SE REVIERTE EL DESCUENTO DEL DINERO
        print(f"🔥 Error crítico en transacción: {e}") # Log para debug
        raise HTTPException(
            status_code=500, 
            detail=f"Error crítico procesando la transacción. No se descontó dinero."
        )

    return new_bet

@router.get("/check/{match_api_id}/{user_email}")
def check_bet_status(match_api_id: str, user_email: str, session: Session = Depends(get_session)):
    """
    Endpoint para que el Frontend verifique el estado de una apuesta.
    """
    user = session.exec(select(User).where(User.email == user_email)).first()
    if not user:
        return {"has_bet": False}
        
    match = session.exec(select(Match).where(Match.api_id == match_api_id)).first()
    if not match:
        return {"has_bet": False}
        
    bet = session.exec(
        select(Bet)
        .where(Bet.user_id == user.id)
        .where(Bet.match_id == match.id)
    ).first()
    
    if bet:
        return {"has_bet": True, "selection": bet.selection, "stake": bet.stake, "status": bet.status}
        
    return {"has_bet": False}

@router.get("/", response_model=List[Bet])
def get_bets(session: Session = Depends(get_session)):
    """Lista todas las apuestas registradas."""
    bets = session.exec(select(Bet)).all()
    return bets

@router.get("/parley/generate")
def generate_parley(limit: int = 3, min_confidence: int = 75, session: Session = Depends(get_session)):
    """
    Generador de Parleys optimizado.
    Filtra los partidos con mayor confianza de análisis de IA.
    """
    statement = (
        select(Match)
        .where(Match.ai_analysis != None)
        .order_by(Match.date)
    )
    matches = session.exec(statement).all()
    
    safe_picks = []
    for m in matches:
        if not m.ai_analysis: 
            continue
            
        try:
            # Aseguramos que el análisis sea un diccionario
            if isinstance(m.ai_analysis, str):
                import json
                analysis = json.loads(m.ai_analysis)
            else:
                analysis = m.ai_analysis
            
            confidence = analysis.get("confidence", 0)
            
            if confidence >= min_confidence:
                # Extraemos la predicción principal del nuevo formato
                prediction = analysis.get("prediction", "N/A")
                reason = analysis.get("reasoning", "Análisis de alta probabilidad")
                
                # Intentamos sacar una cuota aproximada del JSON de odds si existe
                home_win_odd = 0.0
                try:
                    if m.odds_data and isinstance(m.odds_data, str):
                        odds_json = json.loads(m.odds_data)
                        # Lógica simple para extraer cuota (mejorar con TacticalRefinery si es necesario)
                        # Por ahora placeholder 0.0 si no se parsea fácil
                        pass 
                except: pass

                safe_picks.append({
                    "match": f"{m.home_team} vs {m.away_team}",
                    "selection": prediction,
                    "confidence": confidence,
                    "reason": reason,
                    "odds": 0.0 # Placeholder, el frontend lo muestra si es > 0
                })
        except Exception as e: 
            print(f"Error generando parley para match {m.id}: {e}")
            continue
            
    # Ordenar por confianza de mayor a menor
    safe_picks.sort(key=lambda x: x["confidence"], reverse=True)
    
    final_parley = safe_picks[:limit]
    return {
        "status": "success", 
        "parley_size": len(final_parley), 
        "picks": final_parley
    }