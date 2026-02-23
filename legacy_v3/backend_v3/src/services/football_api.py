import os
import requests
import json
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from src import models
from src.config import LEAGUES_WHITELIST
from dotenv import load_dotenv
import time

load_dotenv()

class FootballAPIService:
    def __init__(self):
        self.api_key = os.getenv("API_FOOTBALL_KEY")
        self.base_url = "https://v3.football.api-sports.io"
        self.headers = {
            'x-rapidapi-host': "v3.football.api-sports.io",
            'x-rapidapi-key': self.api_key
        }

    def get_usage_stats(self):
        """
        Consulta el estado de la suscripción y el consumo diario.
        Vital para no exceder el plan gratuito de 100 requests.
        """
        url = f"{self.base_url}/status"
        try:
            # Timeout corto porque esto es para el UI
            response = requests.get(url, headers=self.headers, timeout=5)
            data = response.json()
            
            if "response" in data and data["response"]:
                requests_info = data["response"]["requests"]
                current = requests_info["current"]
                limit = requests_info["limit_day"]
                # Evitar división por cero
                percent = round((current / limit) * 100, 1) if limit > 0 else 100
                
                return {
                    "current": current,
                    "limit": limit,
                    "percent": percent
                }
            return {"current": 0, "limit": 100, "percent": 0}
        except Exception as e:
            print(f"⚠️ Error verificando consumo API: {e}")
            return {"current": 0, "limit": 100, "percent": 0}

    def fetch_and_save_matches(self, db: Session):
        """
        ESTRATEGIA "DOBLE HORIZONTE" (HOY + MAÑANA):
        Descarga partidos de 48 horas para asegurar materia prima para análisis.
        Consumo estimado: 4 Peticiones API (2 Fixtures + 2 Odds).
        """
        try:
            now = datetime.now()
            # Definimos los días a buscar: Hoy y Mañana
            dates_to_fetch = [
                now.strftime("%Y-%m-%d"),
                (now + timedelta(days=1)).strftime("%Y-%m-%d")
            ]
            
            total_saved = 0
            # Convertimos a set para búsqueda O(1) rápida
            target_league_ids = set(LEAGUES_WHITELIST)
            
            print(f"📡 Sincronizando Mercado para: {dates_to_fetch}...")

            for target_date in dates_to_fetch:
                print(f"   📅 Procesando día: {target_date}...")
                
                # --- 1. DESCARGAR PARTIDOS DEL DÍA ---
                url_fix = f"{self.base_url}/fixtures"
                # Usamos zona horaria de Ecuador para que coincida con tu reloj
                params_fix = {"date": target_date, "timezone": "America/Guayaquil"}
                
                try:
                    res_fix = requests.get(url_fix, headers=self.headers, params=params_fix).json()
                except Exception as e:
                    print(f"      ❌ Error conectando fixtures: {e}")
                    continue

                all_fixtures = res_fix.get("response", [])
                
                if not all_fixtures:
                    print(f"      ⚠️ No se encontraron partidos para {target_date}.")
                    continue

                # --- 2. FILTRADO LOCAL (Solo tus ligas) ---
                relevant_fixtures = [f for f in all_fixtures if f['league']['id'] in target_league_ids]
                print(f"      ✅ Relevantes: {len(relevant_fixtures)} partidos.")

                if not relevant_fixtures:
                    continue

                # --- 3. DESCARGAR CUOTAS DEL DÍA ---
                # Solo gastamos llamada de cuotas si hay partidos relevantes
                url_odds = f"{self.base_url}/odds"
                params_odds = {"date": target_date, "bookmaker": 1} # Bet365 (Estándar mundial)
                
                try:
                    res_odds = requests.get(url_odds, headers=self.headers, params=params_odds).json()
                except:
                    res_odds = {}

                # Mapa de cuotas para acceso rápido por ID de partido
                odds_map = {}
                for item in res_odds.get("response", []):
                    fixture_id = item['fixture']['id']
                    if item['bookmakers']:
                        odds_map[fixture_id] = item['bookmakers'][0]['bets']

                # --- 4. GUARDAR EN DB ---
                for item in relevant_fixtures:
                    match_id = item['fixture']['id']
                    goals = item['goals']
                    
                    # Convertir fecha ISO a objeto datetime
                    match_date = datetime.fromisoformat(item['fixture']['date'].replace('Z', '+00:00'))

                    exists = db.query(models.Match).filter(models.Match.api_id == str(match_id)).first()
                    
                    raw_odds = odds_map.get(match_id, None)
                    odds_json = json.dumps(raw_odds) if raw_odds else None

                    if not exists:
                        new_match = models.Match(
                            api_id=str(match_id),
                            date=match_date, 
                            home_team=item['teams']['home']['name'],
                            away_team=item['teams']['away']['name'],
                            league_name=item['league']['name'],
                            
                            # Datos técnicos para StatsService
                            league_id=item['league']['id'],
                            season_year=item['league']['season'],
                            home_team_id=item['teams']['home']['id'],
                            away_team_id=item['teams']['away']['id'],
                            
                            status=item['fixture']['status']['short'],
                            home_score=goals['home'],
                            away_score=goals['away'],
                            odds_data=odds_json
                        )
                        db.add(new_match)
                        total_saved += 1
                    else:
                        # Actualizar estado y resultado si ya existe
                        exists.status = item['fixture']['status']['short']
                        exists.home_score = goals['home']
                        exists.away_score = goals['away']
                        # Actualizar IDs por si acaso faltaban en versiones previas
                        exists.league_id = item['league']['id']
                        exists.season_year = item['league']['season']
                        exists.home_team_id = item['teams']['home']['id']
                        exists.away_team_id = item['teams']['away']['id']
                        
                        # Actualizar cuotas si llegaron nuevas
                        if odds_json: exists.odds_data = odds_json
                
                db.commit()
                # Pausa de cortesía entre días para no saturar
                time.sleep(1.0)

            print(f"💾 Sincronización completada. Nuevos en DB: {total_saved}")
            return {"status": "success", "new_matches": total_saved}

        except Exception as e:
            print(f"❌ Error Crítico API: {e}")
            return {"error": str(e)}