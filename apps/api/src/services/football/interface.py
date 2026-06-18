from abc import ABC, abstractmethod
from typing import Dict, List, Optional

class FootballDataService(ABC):
    """
    Contrato que debe cumplir cualquier proveedor de datos de fútbol
    (Ya sea el Mock simulado o la API real de RapidAPI).
    """

    @abstractmethod
    def get_fixtures_by_date(self, date_str: str) -> List[Dict]:
        """Obtiene partidos para una fecha (YYYY-MM-DD)"""
        pass

    @abstractmethod
    def get_odds(self, fixture_id: str) -> Optional[Dict]:
        """Obtiene cuotas pre-match para un partido"""
        pass

    @abstractmethod
    def get_injuries(self, fixture_id: str) -> List[Dict]:
        """Obtiene lista de lesionados para un partido"""
        pass
    
    @abstractmethod
    def get_lineups(self, fixture_id: str) -> Optional[Dict]:
        """Obtiene alineaciones confirmadas"""
        pass
    
    @abstractmethod
    def get_predictions(self, fixture_id: str) -> Optional[Dict]:
        """Obtiene la predicción matemática de la API"""
        pass

    @abstractmethod
    def get_fixture_by_id(self, fixture_id: str) -> Optional[Dict]:
        """Obtiene el detalle de un fixture puntual (incluye marcador por tiempo)"""
        pass

    @abstractmethod
    def get_fixture_statistics(self, fixture_id: str) -> List[Dict]:
        """Obtiene estadísticas (corners, tarjetas, etc.) de un partido"""
        pass