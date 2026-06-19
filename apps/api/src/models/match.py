from typing import Optional, List, Dict
from datetime import datetime
from sqlmodel import SQLModel, Field, Column
from sqlalchemy.dialects.postgresql import JSONB

class Match(SQLModel, table=True):
    __tablename__ = "matches"

    # --- IDENTIFICADORES ---
    id: Optional[int] = Field(default=None, primary_key=True)
    api_id: str = Field(unique=True, index=True) # ID único de API-Football
    date: datetime # Fecha UTC

    # --- CONTEXTO DEL TORNEO ---
    league_id: int
    league_name: str
    season_year: Optional[int] = None
    round: Optional[str] = None  # Ej: "Final", "Jornada 10"

    # --- EQUIPOS ---
    home_team: str
    away_team: str
    home_team_id: Optional[int] = None
    away_team_id: Optional[int] = None

    # --- ESTADO ---
    status: str = Field(default="NS") # NS, FT, LIVE, PST, SUSP
    home_score: Optional[int] = Field(default=None)
    away_score: Optional[int] = Field(default=None)

    # --- CEREBRO DE LA FASE 6 (DATOS TÁCTICOS - JSONB) ---
    # Usamos JSONB para búsquedas rápidas dentro del JSON
    
    # 1. Cuotas (Mercado)
    # Estructura: {"bookmaker": "Bet365", "values": [{"label": "Home", "odd": 1.80}...]}
    odds_data: Optional[Dict] = Field(default=None, sa_column=Column(JSONB))

    # 2. Radar de Fragilidad (NUEVO)
    # Lista de bajas: [{"player": "Haaland", "reason": "Muscle Injury", "type": "Missing Fixture"}]
    injuries: Optional[List[Dict]] = Field(default=None, sa_column=Column(JSONB))

    # 3. Alineaciones Confirmadas (NUEVO - Solo 40min antes)
    # Estructura: {"home": {"formation": "4-3-3", "startXI": [...]}, "away": ...}
    lineups: Optional[Dict] = Field(default=None, sa_column=Column(JSONB))

    # 4. Juez Comparativo (NUEVO)
    # Predicción matemática de la API externa
    api_prediction: Optional[Dict] = Field(default=None, sa_column=Column(JSONB))

    # 5. La Voz de GoalOS (NUESTRA IA)
    ai_analysis: Optional[Dict] = Field(default=None, sa_column=Column(JSONB))

    # 6. Auditoría
    accuracy_log: Optional[Dict] = Field(default=None, sa_column=Column(JSONB))

    # 7. Estadísticas post-partido (corners/tarjetas/posesión) — get_fixture_statistics()
    statistics: Optional[List[Dict]] = Field(default=None, sa_column=Column(JSONB))

    # 8. Marca si ya corrió el auto-análisis pre-partido (30min antes, con alineaciones)
    auto_analyzed: bool = Field(default=False)

    # Fechas de control
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)