from typing import Optional, Dict, List
from datetime import datetime
from sqlmodel import SQLModel, Field, Column
from sqlalchemy.dialects.postgresql import JSONB


class TeamFormCache(SQLModel, table=True):
    """
    Caché de 18h de los últimos N partidos de un equipo (resultados, corners,
    tarjetas, goles por tiempo, agregados %over1.5/%over2.5/%BTTS). Evita
    gastar cuota de API-Football cada vez que se pide el histórico del mismo
    equipo (6 llamadas reales por equipo: 1 de fixtures + 5 de estadísticas).
    """
    __tablename__ = "team_form_cache"

    id: Optional[int] = Field(default=None, primary_key=True)
    team_id: int = Field(unique=True, index=True)
    team_name: Optional[str] = None
    last_n: int = Field(default=5)

    stats: Dict = Field(default={}, sa_column=Column(JSONB))
    matches_table: List[Dict] = Field(default=[], sa_column=Column(JSONB))

    fetched_at: datetime = Field(default_factory=datetime.utcnow)
