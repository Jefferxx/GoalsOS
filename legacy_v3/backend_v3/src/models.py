"""
Modelos de Base de Datos (ORM) para GoalOS.
Define las tablas para partidos, bankroll, transacciones y apuestas.
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from src.database import Base

class Match(Base):
    """
    Tabla 'matches': Almacena la información de los partidos de fútbol.
    """
    __tablename__ = "matches"

    id = Column(Integer, primary_key=True, index=True)
    api_id = Column(Integer, unique=True, index=True)
    date = Column(DateTime(timezone=True))
    
    # --- OPTIMIZACIÓN V3: Guardamos IDs para no gastar API luego ---
    league_id = Column(Integer, nullable=True)
    season_year = Column(Integer, nullable=True)
    home_team_id = Column(Integer, nullable=True)
    away_team_id = Column(Integer, nullable=True)
    # -------------------------------------------------------------

    league_name = Column(String)
    home_team = Column(String)
    away_team = Column(String)
    status = Column(String, default="NS")

    # Resultados reales
    home_score = Column(Integer, nullable=True)
    away_score = Column(Integer, nullable=True)

    # --- DATOS AVANZADOS ---
    ai_prediction = Column(JSON, nullable=True)
    odds_data = Column(JSON, nullable=True) 
    stats_data = Column(JSON, nullable=True) # <--- AQUÍ GUARDARÁS LA EVIDENCIA (H2H)

    # Relaciones
    bets = relationship("Bet", back_populates="match")

class Bankroll(Base):
    __tablename__ = "bankroll"
    id = Column(Integer, primary_key=True, index=True)
    current_balance = Column(Float, default=0.0)
    initial_capital = Column(Float, default=0.0)
    currency = Column(String, default="USD")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    transactions = relationship("Transaction", back_populates="bankroll")

class Transaction(Base):
    __tablename__ = "transactions"
    id = Column(Integer, primary_key=True, index=True)
    bankroll_id = Column(Integer, ForeignKey("bankroll.id"))
    type = Column(String) 
    amount = Column(Float)
    description = Column(String, nullable=True)
    date = Column(DateTime(timezone=True), server_default=func.now())
    bankroll = relationship("Bankroll", back_populates="transactions")

class Bet(Base):
    __tablename__ = "bets"
    id = Column(Integer, primary_key=True, index=True)
    match_id = Column(Integer, ForeignKey("matches.id"))
    selection = Column(String)
    odds = Column(Float)
    stake = Column(Float)
    potential_return = Column(Float)
    status = Column(String, default="PENDING")
    result_profit = Column(Float, default=0.0)
    placed_at = Column(DateTime(timezone=True), server_default=func.now())
    match = relationship("Match", back_populates="bets")