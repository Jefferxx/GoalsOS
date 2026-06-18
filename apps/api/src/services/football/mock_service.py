import json
import redis
import os
from typing import List, Dict, Optional
from .interface import FootballDataService

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")

class MockFootballService(FootballDataService):
    def __init__(self):
        self.redis = redis.from_url(REDIS_URL)
        print("🛡️ MOCK SERVICE (RICH MODE): Simulando datos tácticos completos")

    def _get_from_cache(self, key: str) -> Optional[Dict]:
        data = self.redis.get(key)
        if data:
            # print(f"⚡ CACHE HIT: {key}") 
            return json.loads(data)
        return None

    def _save_to_cache(self, key: str, data: any, ttl_seconds: int = 3600):
        self.redis.setex(key, ttl_seconds, json.dumps(data))

    def get_fixtures_by_date(self, date_str: str) -> List[Dict]:
        cache_key = f"mock_fixtures:{date_str}"
        if cached := self._get_from_cache(cache_key): return cached

        # Simulamos 2 partidos de Alta Gama (Champions/Premier)
        mock_response = [
            {
                "fixture": {"id": 1001, "date": f"{date_str}T20:00:00+00:00", "status": {"short": "NS"}},
                "league": {"id": 39, "name": "Premier League", "country": "England", "season": 2026},
                "teams": {
                    "home": {"id": 33, "name": "Manchester United", "logo": "https://media.api-sports.io/football/teams/33.png"},
                    "away": {"id": 34, "name": "Newcastle", "logo": "https://media.api-sports.io/football/teams/34.png"}
                },
                "goals": {"home": None, "away": None}
            },
            {
                "fixture": {"id": 1002, "date": f"{date_str}T19:00:00+00:00", "status": {"short": "NS"}},
                "league": {"id": 2, "name": "UEFA Champions League", "country": "World", "season": 2026},
                "teams": {
                    "home": {"id": 529, "name": "Barcelona", "logo": "https://media.api-sports.io/football/teams/529.png"},
                    "away": {"id": 541, "name": "Real Madrid", "logo": "https://media.api-sports.io/football/teams/541.png"}
                },
                "goals": {"home": None, "away": None}
            }
        ]
        self._save_to_cache(cache_key, mock_response)
        return mock_response

    def get_odds(self, fixture_id: str) -> Optional[Dict]:
        # Simula cuotas
        return {
            "fixture": int(fixture_id),
            "bookmakers": [{
                "id": 6, "name": "Bwin",
                "bets": [{"id": 1, "name": "Match Winner", "values": [
                    {"value": "Home", "odd": "2.10"}, {"value": "Draw", "odd": "3.50"}, {"value": "Away", "odd": "3.20"}
                ]}]
            }]
        }

    def get_injuries(self, fixture_id: str) -> List[Dict]:
        """
        Simula el 'Radar de Fragilidad'.
        """
        # Para el partido 1001 (Man Utd), simulamos lesión de Bruno Fernandes
        if str(fixture_id) == "1001":
            return [
                {
                    "player": {"id": 18, "name": "Bruno Fernandes", "photo": "https://media.api-sports.io/football/players/18.png"},
                    "team": {"id": 33, "name": "Manchester United"},
                    "fixture": {"id": 1001},
                    "type": "Missing Fixture",
                    "reason": "Muscle Injury"
                }
            ]
        return []

    def get_predictions(self, fixture_id: str) -> Optional[Dict]:
        """
        Simula el 'Juez Comparativo'.
        """
        return {
            "winner": {"id": 33, "name": "Manchester United", "comment": "Win or Draw"},
            "win_or_draw": True,
            "under_over": "-3.5",
            "goals": {"home": "-1.5", "away": "-1.5"},
            "advice": "Double Chance : Manchester United or Draw",
            "percent": {"home": "45%", "draw": "35%", "away": "20%"}
        }

    def get_lineups(self, fixture_id: str) -> Optional[Dict]:
        """
        Simula Alineaciones.
        """
        return {
            "home": {
                "team": {"id": 33, "name": "Manchester United"},
                "formation": "4-2-3-1",
                "startXI": [{"player": {"id": 1, "name": "De Gea", "number": 1, "pos": "G"}}]
            },
            "away": {
                "team": {"id": 34, "name": "Newcastle"},
                "formation": "4-3-3",
                "startXI": [{"player": {"id": 2, "name": "Pope", "number": 1, "pos": "G"}}]
            }
        }

    def get_fixture_by_id(self, fixture_id: str) -> Optional[Dict]:
        """Simula el detalle (con marcador por tiempo) de un fixture puntual."""
        return {
            "fixture": {"id": int(fixture_id), "date": "2026-06-01T20:00:00+00:00", "status": {"short": "FT"}},
            "league": {"id": 39, "name": "Premier League"},
            "teams": {
                "home": {"id": 1, "name": "Mock FC"},
                "away": {"id": 2, "name": "Rival FC"},
            },
            "goals": {"home": 2, "away": 1},
            "score": {"halftime": {"home": 1, "away": 0}, "fulltime": {"home": 2, "away": 1}},
        }

    def get_fixture_statistics(self, fixture_id: str) -> List[Dict]:
        """Simula estadísticas (corners, tarjetas) de un partido."""
        return [
            {"team": {"id": 1}, "statistics": [
                {"type": "Corner Kicks", "value": 5},
                {"type": "Yellow Cards", "value": 2},
            ]},
            {"team": {"id": 2}, "statistics": [
                {"type": "Corner Kicks", "value": 4},
                {"type": "Yellow Cards", "value": 1},
            ]},
        ]