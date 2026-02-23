from sqlmodel import Session, select
from src.models.bet import Bet
from src.models.match import Match
from src.models.user import User

class ResultAuditor:
    def __init__(self, session: Session):
        self.session = session

    def audit_pending_bets(self):
        """
        AUDITORÍA INTELIGENTE (Lazy Audit - Silicon Valley Edition):
        Revisa apuestas PENDING.
        Asume que los datos del partido (Match) ya fueron actualizados por el Worker nocturno.
        No gasta créditos de API aquí.
        """
        # 1. Buscar apuestas pendientes
        pending_bets = self.session.exec(select(Bet).where(Bet.status == "PENDING")).all()
        processed = 0
        
        print(f"⚖️ El Juez: Revisando {len(pending_bets)} apuestas pendientes...")

        for bet in pending_bets:
            try:
                # Buscamos el partido usando el ID de la API (Referencia inmutable)
                # Si el bet no tiene match_api_id, intentamos buscar por match_id interno
                if bet.match_api_id:
                    match = self.session.exec(select(Match).where(Match.api_id == bet.match_api_id)).first()
                else:
                    match = self.session.exec(select(Match).where(Match.id == bet.match_id)).first()
                
                if not match: 
                    # print(f"   ⚠️ Partido no encontrado en DB para apuesta {bet.id}")
                    continue
                
                # 2. Solo auditamos si el partido terminó oficialmente
                # FT: Full Time, AET: After Extra Time, PEN: Penalties
                if match.status in ['FT', 'AET', 'PEN']:
                    self._audit_bet(bet, match)
                    processed += 1
            except Exception as e:
                print(f"🔥 Error auditando apuesta {bet.id}: {e}")

        return {"status": "success", "processed": processed}

    def _audit_bet(self, bet: Bet, match: Match):
        home_score = match.home_score if match.home_score is not None else 0
        away_score = match.away_score if match.away_score is not None else 0
        
        # Normalización para comparar texto
        selection = bet.selection.lower().strip()
        home_team = match.home_team.lower()
        away_team = match.away_team.lower()
        
        # Determinar ganador real
        winner = "draw"
        if home_score > away_score: winner = "home"
        elif away_score > home_score: winner = "away"

        won = False
        reason_suffix = f"(Marcador: {match.home_team} {home_score}-{away_score} {match.away_team})"
        explanation = ""

        # --- LÓGICA DE RESOLUCIÓN (CEREBRO DEL JUEZ) ---
        
        # 1. EMPATE
        if "empate" in selection or "draw" in selection or selection == "x":
            if winner == "draw":
                won = True
                explanation = "Hubo empate."
            else:
                explanation = "No hubo empate."

        # 2. GANA LOCAL (1)
        elif "gana local" in selection or "home" in selection or "1" == selection or home_team in selection:
            # Detectar Doble Oportunidad "Local o Empate"
            if " o " in selection or "doble" in selection:
                if winner in ["home", "draw"]:
                    won = True
                    explanation = "El local ganó o empató."
                else:
                    explanation = "Ganó el visitante."
            # Apuesta Simple
            else:
                if winner == "home":
                    won = True
                    explanation = "Ganó el local."
                else:
                    explanation = f"No ganó el local (Ganador: {winner})."

        # 3. GANA VISITANTE (2)
        elif "gana visitante" in selection or "away" in selection or "2" == selection or away_team in selection:
            # Detectar Doble Oportunidad "Visitante o Empate"
            if " o " in selection or "doble" in selection:
                if winner in ["away", "draw"]:
                    won = True
                    explanation = "El visitante ganó o empató."
                else:
                    explanation = "Ganó el local."
            # Apuesta Simple
            else:
                if winner == "away":
                    won = True
                    explanation = "Ganó el visitante."
                else:
                    explanation = f"No ganó el visitante (Ganador: {winner})."
        
        # 4. OVER/UNDER (Lógica Básica de Goles)
        elif "over" in selection or "mas de" in selection or "+" in selection:
            # Ejemplo: "Over 2.5"
            try:
                line = float(''.join([c for c in selection if c.isdigit() or c == '.']))
                total_goals = home_score + away_score
                if total_goals > line:
                    won = True
                    explanation = f"Hubo {total_goals} goles (Más de {line})."
                else:
                    explanation = f"Solo hubo {total_goals} goles."
            except:
                explanation = "Formato de goles no reconocido."

        # --- GUARDAR RESULTADO ---
        bet.result_score = f"{home_score}-{away_score}"
        
        if won:
            bet.status = "WON"
            bet.audit_reason = f"✅ ¡Acertaste! {explanation} {reason_suffix}"
            self._pay_user(bet)
            print(f"   💰 Pagar apuesta {bet.id}: ${bet.potential_payout}")
        else:
            bet.status = "LOST"
            bet.audit_reason = f"❌ Fallaste. {explanation} {reason_suffix}"
            print(f"   🗑️ Marcar perdida apuesta {bet.id}")
        
        self.session.add(bet)
        self.session.commit()

    def _pay_user(self, bet: Bet):
        """Transfiere las ganancias a la billetera del usuario"""
        user = self.session.get(User, bet.user_id)
        if user:
            user.bankroll += bet.potential_payout
            self.session.add(user)