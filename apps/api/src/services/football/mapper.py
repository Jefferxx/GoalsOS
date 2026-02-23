import json
from datetime import datetime
from typing import Dict, Optional
from src.models.match import Match

class DataMapper:
    """
    Transforma el JSON crudo de API-Football en nuestro modelo de Base de Datos (Match).
    Incluye refinería de datos para la IA.
    """

    @staticmethod
    def fixture_to_match(fixture_data: Dict, odds_data: Optional[Dict] = None) -> Match:
        fixture = fixture_data.get("fixture", {})
        league = fixture_data.get("league", {})
        teams = fixture_data.get("teams", {})
        goals = fixture_data.get("goals", {})

        date_str = fixture.get("date")
        match_date = datetime.fromisoformat(date_str.replace("Z", "+00:00")) if date_str else datetime.utcnow()

        match = Match(
            api_id=str(fixture.get("id")),
            date=match_date,
            league_id=league.get("id"),
            league_name=league.get("name"),
            season_year=league.get("season"),
            round=league.get("round"),
            home_team=teams.get("home", {}).get("name", "Unknown Home"),
            away_team=teams.get("away", {}).get("name", "Unknown Away"),
            home_team_id=teams.get("home", {}).get("id"),
            away_team_id=teams.get("away", {}).get("id"),
            status=fixture.get("status", {}).get("short", "NS"),
            home_score=goals.get("home"),
            away_score=goals.get("away"),
            odds_data=odds_data,
            injuries=[], 
            lineups={},
            api_prediction={}
        )
        return match

    @staticmethod
    def update_tactical_data(match: Match, injuries: list = None, lineups: dict = None, prediction: dict = None):
        if injuries: match.injuries = injuries
        if lineups: match.lineups = lineups
        if prediction: match.api_prediction = prediction
        return match

    @staticmethod
    def get_ai_context(match: Match) -> Dict[str, str]:
        """
        ETL: Extrae, Transforma y Carga datos limpios para la IA.
        Convierte JSONs crudos en 'Insights' legibles.
        """
        return {
            "odds_summary": TacticalRefinery.digest_odds(match.odds_data),
            "form_analysis": TacticalRefinery.digest_form(match.api_prediction),
            "injury_report": TacticalRefinery.digest_injuries(match.injuries),
            "h2h_trends": TacticalRefinery.digest_h2h(match.api_prediction)
        }

class TacticalRefinery:
    """
    Refinería de Datos: Limpia la basura antes de enviarla a la IA.
    """
    
    @staticmethod
    def digest_odds(odds_json) -> str:
        """Extrae la cuota de ganador del partido limpia."""
        try:
            if not odds_json: return "Mercado cerrado o sin cuotas."
            data = odds_json if isinstance(odds_json, dict) else json.loads(odds_json)
            
            # Buscar cuotas de 'Match Winner'
            bookmakers = data.get('response', [])
            if bookmakers and len(bookmakers) > 0:
                bets = bookmakers[0].get('bets', [])
                for bet in bets:
                    if bet['id'] == 1: # ID 1 suele ser Match Winner
                        values = bet['values'] # [{value: 1.5, odd: 2.1}, ...]
                        return f"Cuotas 1X2: {json.dumps(values)}"
            return "Cuotas no estandarizadas."
        except: return "Error procesando cuotas."

    @staticmethod
    def digest_form(pred_json) -> str:
        """Convierte 'WWLDW' en texto narrativo o utiliza el consejo de la API."""
        try:
            if not pred_json: return "Sin datos de forma recientes."
            data = pred_json if isinstance(pred_json, dict) else json.loads(pred_json)
            
            # Accedemos a la estructura típica de API-Football predictions
            resp = data.get('response', [])
            if not resp: return "Sin predicción disponible."
            
            predictions = resp[0].get('predictions', {})
            if predictions:
                winner = predictions.get('winner')
                advice = predictions.get('advice')
                percent = predictions.get('percent')
                return f"Consejo de la API: {advice}. Probabilidad de {winner}: {percent}%"
            
            teams = resp[0].get('teams', {})
            home = teams.get('home', {})
            away = teams.get('away', {})
            
            def parse_form(form_str):
                if not form_str: return "desconocida"
                wins = form_str.count('W')
                loss = form_str.count('L')
                return f"Últimos 5: {form_str} ({wins} victorias, {loss} derrotas)"

            # Extraemos la 'form' (e.g. "WLWDD")
            home_form = parse_form(home.get('league', {}).get('form', ''))
            away_form = parse_form(away.get('league', {}).get('form', ''))
            
            return f"Local: {home_form}. Visitante: {away_form}."
        except: return "Datos de forma corruptos."

    @staticmethod
    def digest_injuries(inj_json) -> str:
        """Lista jugadores lesionados formateados."""
        try:
            if not inj_json: return "Plantillas completas (Sin bajas reportadas)."
            data = inj_json if isinstance(inj_json, list) else json.loads(inj_json)
            
            if isinstance(data, dict): data = data.get('response', [])
            if not data: return "Sin reporte médico."

            # Extraemos nombres
            players = []
            for item in data:
                p_name = item.get('player', {}).get('name', 'Desconocido')
                p_reason = item.get('player', {}).get('reason', 'Lesión')
                players.append(f"{p_name} ({p_reason})")
            
            if not players: return "Sin bajas significativas."
            # Limitamos a 7 para no saturar el prompt
            return "Bajas confirmadas: " + ", ".join(players[:7])
        except: return "Error leyendo reporte de lesiones."

    @staticmethod
    def digest_h2h(pred_json) -> str:
        """Analiza enfrentamientos directos."""
        try:
            if not pred_json: return ""
            data = pred_json if isinstance(pred_json, dict) else json.loads(pred_json)
            h2h = data.get('response', [])[0].get('h2h', [])
            
            if not h2h: return "Sin historial reciente entre ellos."
            
            # Resumen rápido
            results = []
            for match in h2h[:3]: # Últimos 3
                score = match.get('score', {}).get('fulltime', '?-?')
                home = match.get('teams', {}).get('home', {}).get('name')
                away = match.get('teams', {}).get('away', {}).get('name')
                results.append(f"{home} {score} {away}")
            
            return "Últimos H2H: " + " | ".join(results)
        except: return ""
