import requests
import os
from typing import List, Dict, Any

class RealFootballService:
    def __init__(self):
        self.api_key = os.getenv("API_FOOTBALL_KEY")
        self.base_url = "https://v3.football.api-sports.io"
        self.headers = {
            'x-apisports-key': self.api_key
        }
        
    def _get(self, endpoint: str, params: Dict = None) -> Any:
        """Helper para hacer peticiones seguras"""
        if not self.api_key:
            print("🔥 ERROR: API Key no configurada.")
            return None
            
        try:
            print(f"📡 API-SPORTS CALL: /{endpoint} {params}")
            response = requests.get(f"{self.base_url}/{endpoint}", headers=self.headers, params=params)
            
            if response.status_code != 200:
                print(f"⚠️ API Error {response.status_code}: {response.text}")
                return None
                
            data = response.json()
            
            # Verificar errores de lógica de la API (ej. Rate Limit)
            if data.get("errors"):
                # Si hay errores pero devuelve respuesta vacía, suele ser un error de plan
                print(f"⚠️ API Logic Warning: {data['errors']}")
                if not data.get("response"):
                    return None
                
            return data.get("response")
            
        except Exception as e:
            print(f"🔥 Network Error: {e}")
            return None

    def get_fixtures_by_date(self, date_str: str) -> List[Dict]:
        """
        Obtiene partidos por FECHA (Permitido en Plan Free).
        """
        return self._get("fixtures", {"date": date_str}) or []

    def get_odds(self, fixture_id: str) -> Dict:
        """Obtiene cuotas de Bet365 (ID 1)"""
        # Nota: El plan free a veces limita las odds pre-match a 7 días antes.
        data = self._get("odds", {"fixture": fixture_id, "bookmaker": "1"})
        return data[0] if data else None

    def get_injuries(self, fixture_id: str) -> List[Dict]:
        """Obtiene reporte médico"""
        return self._get("injuries", {"fixture": fixture_id}) or []

    def get_predictions(self, fixture_id: str) -> Dict:
        """Obtiene análisis matemático de la API"""
        data = self._get("predictions", {"fixture": fixture_id})
        return data[0] if data else None
        
    def get_lineups(self, fixture_id: str) -> List[Dict]:
        """Obtiene alineaciones confirmadas"""
        return self._get("fixtures/lineups", {"fixture": fixture_id}) or []