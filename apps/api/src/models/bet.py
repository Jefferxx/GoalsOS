from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime

class Bet(SQLModel, table=True):
    __tablename__ = "bets"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id")
    
    # Referencias al partido
    match_id: int = Field(foreign_key="matches.id") # Relación Interna (SQL)
    match_api_id: str # ID Externo (API-Football) para búsquedas rápidas del Juez
    
    # Detalles de la apuesta
    selection: str  # Ej: "Gana Local", "Empate"
    odds: float     # Ej: 2.10
    stake: float    # Cantidad apostada
    potential_payout: float # Ganancia potencial
    
    # Estado y Auditoría
    status: str = Field(default="PENDING") # PENDING, WON, LOST, VOID
    result_score: Optional[str] = None     # Marcador final (Ej: "2-1")
    audit_reason: Optional[str] = None     # <--- NUEVO: Explicación del resultado (Transparencia)
    
    # Metadatos
    strategy: str = Field(default="MANUAL") # MANUAL, KELLY_VALUE_V1, etc.
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)