"""
Módulo principal de la API GoalOS v2.7 (Consolidación)
Integración: Agente Estadístico + Gemini/Groq + Modo Manual + Gestión de Riesgo + Parleys Clasificados.
"""
from fastapi import FastAPI, Depends, HTTPException, Body, Query
from pydantic import BaseModel 
from sqlalchemy.orm import Session
from sqlalchemy import text, func 
from datetime import datetime, date 
from src.database import get_db, engine
from src import models
from src.services.football_api import FootballAPIService
from src.services.ai_service import AIPredictionService 
from src.services.stats_service import StatsService 
import time
import json 
import re 

# --- CONFIGURACIÓN INICIAL ---
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="GoalOS API", description="Sistema de Inversión Deportiva v2.7", version="2.7.0")

# --- MODELOS DE DATOS ---
class ManualAnalysisRequest(BaseModel):
    raw_text: str

class UpdateOddsRequest(BaseModel):
    bet_id: int
    real_odds: float

class AnalyzeSingleMatchRequest(BaseModel):
    match_id: int
    manual_text: str = ""

# --- MODELO PARA GESTIÓN DE FONDOS (RF-14) ---
class ManageFundsRequest(BaseModel):
    type: str = "SET_REAL_BALANCE" # Por defecto siempre será este
    amount: float
    description: str = "Sincronización Manual"

# --- ENDPOINTS GENERALES ---
@app.get("/")
def read_root():
    return {"sistema": "GoalOS", "estado": "Operativo 🟢", "version": "2.7.0 (Consolidación)"}

@app.get("/health")
def health_check(db: Session = Depends(get_db)):
    try:
        _result = db.execute(text("SELECT 1"))
        return {"status": "ok", "database": "Conectada 🚀"}
    except Exception as e:
        return {"status": "error", "database": str(e)}

# --- ENDPOINT DE CONSUMO API (RF-Consumo) ---
@app.get("/api-usage")
def check_api_usage():
    service = FootballAPIService()
    return service.get_usage_stats()

# --- ENDPOINTS DE PARTIDOS E IA ---
@app.get("/sync-matches")
def sync_todays_matches(db: Session = Depends(get_db)):
    service = FootballAPIService()
    result = service.fetch_and_save_matches(db)
    if "error" in result:
        return {"status": "failed", "detail": result["error"]}
    return result

@app.post("/analyze-single")
def analyze_single_match_cyborg(request: AnalyzeSingleMatchRequest, db: Session = Depends(get_db)):
    match = db.query(models.Match).filter(models.Match.id == request.match_id).first()
    if not match: raise HTTPException(status_code=404, detail="Partido no encontrado")
    
    print(f"\n🦾 [Cyborg] Iniciando análisis para: {match.home_team} vs {match.away_team}")
    stats_agent = StatsService()
    brain = AIPredictionService()
    
    if not (match.home_team_id and match.away_team_id):
        return {"status": "error", "message": "Faltan IDs técnicos."}

    full_stats = stats_agent.get_match_context(
        match.api_id, match.home_team_id, match.away_team_id, 
        match.league_id, match.season_year, manual_input=request.manual_text
    )
    
    match.stats_data = full_stats.get("json", None)
    
    analysis = brain.analyze_match(
        home_team=match.home_team, away_team=match.away_team, date=str(match.date),
        league=match.league_name or "Unknown", stats_context=full_stats.get("text", "") 
    )
    
    if analysis:
        match.ai_prediction = analysis
        db.commit()
        return {"status": "success", "analysis": analysis, "match": f"{match.home_team} vs {match.away_team}"}
    return {"status": "error", "message": "Fallo IA"}

@app.get("/analyze-batch")
def analyze_pending_matches(limit: int = 5, db: Session = Depends(get_db)):
    pending_matches = db.query(models.Match).filter(
        models.Match.ai_prediction == None,
        models.Match.status == "NS"
    ).limit(limit).all()

    if not pending_matches: return {"status": "info", "message": "No hay partidos pendientes."}

    brain = AIPredictionService()
    stats_agent = StatsService() 
    results = []

    for match in pending_matches:
        try:
            if match.league_id:
                full_stats = stats_agent.get_match_context(
                    match.api_id, match.home_team_id, match.away_team_id, 
                    match.league_id, match.season_year
                )
                analysis = brain.analyze_match(
                    home_team=match.home_team, away_team=match.away_team,
                    date=str(match.date), league=match.league_name, stats_context=full_stats.get("text", "") 
                )
                if analysis:
                    match.ai_prediction = analysis
                    db.commit()
                    results.append({"match": f"{match.home_team} vs {match.away_team}", "market": analysis.get("market")})
                time.sleep(1)
        except Exception as e:
            continue
    return {"status": "success", "processed": len(results), "details": results}

@app.post("/analyze-manual")
def analyze_manual_text_pure(request: ManualAnalysisRequest):
    brain = AIPredictionService()
    analysis = brain.analyze_match(
        home_team="Manual A", away_team="Manual B", date="Hoy", 
        league="Manual", stats_context=f"DATOS MANUALES:\n{request.raw_text}"
    )
    return {"status": "success", "analysis": analysis}

@app.get("/recommend-parlay")
def recommend_parlay_advanced(league_filter: str = Query(None), db: Session = Depends(get_db)):
    query = db.query(models.Bet).filter(models.Bet.status == "PENDING")
    if league_filter and league_filter != "Todas":
        query = query.join(models.Match).filter(models.Match.league_name == league_filter)
    
    active_bets = query.all()
    if len(active_bets) < 2: return {"status": "info", "message": "Insuficientes apuestas."}

    safe_picks = []
    value_picks = []
    lotto_picks = []

    for bet in active_bets:
        pred = bet.match.ai_prediction or {}
        conf = pred.get("confidence_score", 0)
        ev = pred.get("estimated_ev", "NEUTRAL")
        odds = bet.odds
        item = {
            "match": f"{bet.match.home_team} vs {bet.match.away_team}",
            "selection": bet.selection,
            "odds": odds, "confidence": conf, "league": bet.match.league_name
        }
        if conf >= 80 and 1.20 <= odds <= 1.60: safe_picks.append(item)
        elif ev == "POSITIVE" and 1.50 <= odds <= 2.20: value_picks.append(item)
        elif odds > 2.20: lotto_picks.append(item)
        elif conf >= 70: value_picks.append(item)

    def build_combo(picks, name):
        if len(picks) < 2: return None
        picks.sort(key=lambda x: x['odds'] if name=="Lotto" else x['confidence'], reverse=True)
        selected = picks[:3]
        total = 1.0
        for p in selected: total *= p['odds']
        return {"name": name, "total_odds": round(total, 2), "picks": selected}

    return {"status": "success", "combos": {
        "safe": build_combo(safe_picks, "🛡️ El Muro"),
        "value": build_combo(value_picks, "⚖️ Valor"),
        "lotto": build_combo(lotto_picks, "🚀 Lotto")
    }}

@app.get("/view-matches")
def view_matches_for_dashboard(db: Session = Depends(get_db)):
    today = datetime.now().date()
    upcoming = db.query(models.Match).filter(func.date(models.Match.date) >= today, models.Match.status == "NS").order_by(models.Match.league_name.asc(), models.Match.date.asc()).all()
    finished = db.query(models.Match).filter(func.date(models.Match.date) >= today, models.Match.status != "NS").order_by(models.Match.date.desc()).all()
    return {"status": "success", 
            "upcoming": [{"id": m.id, "teams": f"{m.home_team} vs {m.away_team}", "league": m.league_name, "time": m.date.strftime("%H:%M"), "prediction": m.ai_prediction} for m in upcoming],
            "finished": [{"id": m.id, "teams": f"{m.home_team} vs {m.away_team}", "status": m.status, "score": f"{m.home_score}-{m.away_score}"} for m in finished]}

@app.get("/bankroll")
def get_bankroll(db: Session = Depends(get_db)):
    bankroll = db.query(models.Bankroll).first()
    return {"current_balance": round(bankroll.current_balance, 2) if bankroll else 0.0, "currency": "USD"}

@app.post("/reset-bankroll")
def reset_bankroll(amount: float = Body(..., embed=True), db: Session = Depends(get_db)):
    db.query(models.Transaction).delete()
    db.query(models.Bet).delete()
    try: db.query(models.Match).delete()
    except: pass
    db.query(models.Bankroll).delete()
    db.add(models.Bankroll(current_balance=amount, initial_capital=amount, currency="USD"))
    db.commit()
    return {"status": "success", "message": "Sistema reiniciado."}

# --- 🔥 GESTIÓN DE FONDOS SIMPLIFICADA (RF-14) ---
@app.post("/manage-funds")
def manage_funds(request: ManageFundsRequest, db: Session = Depends(get_db)):
    bankroll = db.query(models.Bankroll).first()
    if not bankroll: 
        raise HTTPException(status_code=404, detail="No se encontró la banca.")

    # Lógica de Sincronización Directa (SET_REAL_BALANCE)
    if request.amount < 0:
        raise HTTPException(status_code=400, detail="El saldo no puede ser negativo.")
    
    # 1. Calculamos la diferencia para el historial
    diff = request.amount - bankroll.current_balance
    
    if diff == 0:
        return {"status": "info", "message": "El saldo ya está actualizado."}
        
    # 2. Actualizamos el saldo al valor exacto que pediste
    bankroll.current_balance = request.amount
    
    # 3. Guardamos el registro (Auditoría)
    db.add(models.Transaction(
        bankroll_id=bankroll.id, 
        type="MANUAL_SYNC", 
        amount=diff, 
        description=request.description
    ))
    
    db.commit()
    return {
        "status": "success", 
        "new_balance": round(bankroll.current_balance, 2),
        "adjustment": diff
    }

@app.post("/auto-bet")
def place_automatic_bets(db: Session = Depends(get_db)):
    bankroll = db.query(models.Bankroll).first()
    analyzed_matches = db.query(models.Match).filter(models.Match.ai_prediction != None, models.Match.status == "NS").all()
    bets_placed = 0
    for match in analyzed_matches:
        if db.query(models.Bet).filter(models.Bet.match_id == match.id).first(): continue
        pred = match.ai_prediction
        if not pred: continue
        
        real_odd = 1.50
        p = pred.get("probability", 50) / 100.0
        b = real_odd - 1.0
        kelly = (b*p - (1-p))/b if b > 0 else 0
        safe_kelly = kelly * 0.25
        
        stake = 0.0
        status = "REJECTED"
        if safe_kelly > 0:
            stake = max(1.0, min(bankroll.current_balance * safe_kelly, bankroll.current_balance * 0.15))
            bankroll.current_balance -= stake
            db.add(models.Transaction(bankroll_id=bankroll.id, type="BET_STAKE", amount=-stake, description=f"Kelly Auto: {match.home_team}"))
            status = "PENDING"
            bets_placed += 1
            
        db.add(models.Bet(match_id=match.id, selection=f"{pred.get('market')} - {pred.get('selection')}", odds=real_odd, stake=round(stake,2), potential_return=stake*real_odd, status=status))
    db.commit()
    return {"status": "success", "bets_created": bets_placed}

@app.post("/update-bet-odds")
def update_bet_odds(request: UpdateOddsRequest, db: Session = Depends(get_db)):
    bet = db.query(models.Bet).filter(models.Bet.id == request.bet_id).first()
    bankroll = db.query(models.Bankroll).first()
    
    p = bet.match.ai_prediction.get("probability", 50) / 100.0
    b = request.real_odds - 1.0
    kelly = (b*p - (1-p))/b if b > 0 else 0
    safe_kelly = kelly * 0.25
    
    msg = ""
    if safe_kelly > 0:
        new_stake = max(1.0, min(bankroll.current_balance * safe_kelly, bankroll.current_balance * 0.15))
        if bet.status == "PENDING": bankroll.current_balance += bet.stake 
        bankroll.current_balance -= new_stake
        bet.stake = round(new_stake, 2)
        bet.status = "PENDING"
        msg = f"✅ Stake Ajustado: ${bet.stake}"
    else:
        if bet.status == "PENDING": bankroll.current_balance += bet.stake
        bet.stake = 0.0
        bet.status = "REJECTED"
        msg = "⚠️ EV Negativo."
        
    bet.odds = request.real_odds
    db.commit()
    return {"status": "success", "message": msg}

# ==============================================================================
# AUDITORÍA INTELIGENTE V4.4
# ==============================================================================

def is_team_match(team_db, team_sel):
    if not team_db or not team_sel: return False
    clean_db = team_db.upper().replace("FC ", "").replace("CF ", "").replace("AC ", "").strip()
    clean_sel = team_sel.upper().strip()
    if clean_db in clean_sel: return True
    parts = clean_db.split()
    for part in parts:
        if len(part) > 3 and part in clean_sel: return True
    return False

def check_bet_outcome(selection: str, home_score: int, away_score: int, home_name: str, away_name: str):
    """
    Auditor V4.4: Regex corregida para aceptar números decimales (2.5) y lógica BTTS blindada.
    """
    # 1. LIMPIEZA AGRESIVA CORREGIDA: Permitimos el PUNTO (.)
    sel_raw = selection.upper()
    sel = re.sub(r'[^\w\s:+.-]', '', sel_raw).strip() 
    
    print(f"🕵️ AUDITOR V4.4 -> Analizando: '{sel}' | Score: {home_score}-{away_score}")

    total_goals = home_score + away_score
    both_scored = (home_score > 0 and away_score > 0)

    # --- LÓGICA AMBOS MARCAN ---
    if "AMBOS" in sel or "BTTS" in sel or "MARCAN" in sel:
        if "NO" in sel or "NUNCA" in sel: return "WON" if not both_scored else "LOST"
        return "WON" if both_scored else "LOST"

    # --- MERCADOS DE GOLES (Regex corregida para floats) ---
    if "OVER" in sel or "MAS" in sel:
        # Busca numeros con o sin decimales (ej: 2.5, 2, 3.0)
        nums = re.findall(r"[-+]?\d*\.\d+|\d+", sel)
        if nums:
            line = float(nums[0])
            # Si hay 4 goles y la linea es 2.5 -> 4 > 2.5 -> WON
            res = "WON" if total_goals > line else "LOST"
            print(f"   -> Over {line} (Total: {total_goals}) -> {res}")
            return res
    
    if "UNDER" in sel or "MENOS" in sel:
        nums = re.findall(r"[-+]?\d*\.\d+|\d+", sel)
        if nums:
            line = float(nums[0])
            return "WON" if total_goals < line else "LOST"

    # --- GANADOR (1X2) ---
    if "GANADOR" in sel or "1X2" in sel or "VICTORIA" in sel:
        if "EMPATE" in sel: return "WON" if home_score == away_score else "LOST"
        if "LOCAL" in sel or is_team_match(home_name, sel): return "WON" if home_score > away_score else "LOST"
        if "VISITA" in sel or is_team_match(away_name, sel): return "WON" if away_score > home_score else "LOST"

    # --- DOBLE OPORTUNIDAD ---
    if "DOBLE" in sel or "OPORTUNIDAD" in sel:
        if ("LOCAL" in sel or is_team_match(home_name, sel)) and ("EMPATE" in sel):
            return "WON" if home_score >= away_score else "LOST"
        if ("VISITA" in sel or is_team_match(away_name, sel)) and ("EMPATE" in sel):
            return "WON" if away_score >= home_score else "LOST"
        if ("LOCAL" in sel or is_team_match(home_name, sel)) and ("VISITA" in sel or is_team_match(away_name, sel)):
            return "WON" if home_score != away_score else "LOST"

    return "PENDING"

@app.post("/settle-bets")
def settle_pending_bets(db: Session = Depends(get_db)):
    # Traemos SOLO PENDING para auditar
    pending = db.query(models.Bet).join(models.Match).filter(
        models.Bet.status == "PENDING",
        models.Match.status.in_(["FT", "AET", "PEN"])
    ).all()

    processed = 0
    total_profit = 0
    bankroll = db.query(models.Bankroll).first()

    for bet in pending:
        outcome = check_bet_outcome(
            selection=bet.selection, 
            home_score=bet.match.home_score, 
            away_score=bet.match.away_score,
            home_name=bet.match.home_team,
            away_name=bet.match.away_team
        )
        
        if outcome != "PENDING":
            bet.status = outcome
            processed += 1
            if outcome == "WON":
                payout = bet.stake * bet.odds
                profit = payout - bet.stake
                bet.result_profit = profit
                bankroll.current_balance += payout
                db.add(models.Transaction(bankroll_id=bankroll.id, type="BET_WIN", amount=payout, description=f"✅ {bet.match.home_team}"))
                total_profit += profit
            elif outcome == "LOST":
                bet.result_profit = -bet.stake

    db.commit()
    return {"status": "success", "processed": processed, "total_profit": round(total_profit, 2)}

@app.get("/my-bets")
def list_active_bets(db: Session = Depends(get_db)):
    bets = db.query(models.Bet).join(models.Match).order_by(models.Bet.id.desc()).limit(30).all()
    portfolio = []
    for bet in bets:
        pred = bet.match.ai_prediction or {}
        stats = bet.match.stats_data or {}
        score = f"({bet.match.home_score}-{bet.match.away_score})" if bet.match.status in ["FT", "AET", "PEN"] else ""
        
        portfolio.append({
            "id": bet.id,
            "match": f"{bet.match.home_team} vs {bet.match.away_team}",
            "match_score": score,
            "league": bet.match.league_name,
            "selection": bet.selection,
            "stake": round(bet.stake, 2),
            "odds": bet.odds,
            "status": bet.status,
            "profit": round(bet.result_profit, 2),
            "reasoning": pred.get("reasoning", "Sin análisis."),
            "stats": stats,
            "probability": pred.get("probability", 0),
            "key_stat": pred.get("key_stat", "")
        })
    return {"status": "success", "bets": portfolio}