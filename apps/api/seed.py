from src.db.session import engine, init_db
from src.models.match import Match
from sqlmodel import Session
from datetime import datetime, timedelta

def create_fake_matches():
    print("🌱 Sembrando Datos PRO en GoalOS V4...")
    init_db()
    
    # 1. Escenario: Partido de Alta Jerarquía (Champions)
    match_pro = Match(
        api_id="seed_001",
        date=datetime.now() + timedelta(hours=24),
        league_id=2, league_name="UEFA Champions League", season_year=2026,
        home_team="Real Madrid", away_team="Manchester City",
        home_team_id=541, away_team_id=50,
        status="NS",
        
        # Simulamos bajas (campo injuries del modelo)
        injuries=[
            {"player": "Courtois", "reason": "Duda", "type": "Questionable"},
            {"player": "De Bruyne", "reason": "Baja", "type": "Missing Fixture"}
        ],

        # Simulamos Cuotas
        odds_data={
            "1x2": {"1": 2.80, "X": 3.50, "2": 2.45},
            "over_25": 1.70,
            "btts": 1.55
        },
        
        # Simulamos Análisis de la "Colmena de Agentes"
        ai_analysis={
            "summary": "Partido de alto voltaje ofensivo.",
            "confidence": 88,
            "agents": {
                "goleador": {"pick": "Over 2.5", "reason": "Ambos promedian +2.5 goles en Champions."},
                "tactico": {"pick": "Tarjetas Over 4.5", "reason": "Árbitro estricto en fases finales."},
                "scout": {"pick": "Vinicius +1.5 Remates al arco", "reason": "Enfrenta lateral suplente."}
            }
        }
    )

    # 2. Escenario: Partido de "Relleno" (Para probar filtros)
    match_low = Match(
        api_id="seed_002",
        date=datetime.now() + timedelta(hours=48),
        league_id=140, league_name="La Liga", season_year=2026,
        home_team="Getafe", away_team="Leganés",
        home_team_id=540, away_team_id=530,
        status="NS",
        odds_data={"1x2": {"1": 2.10, "X": 2.90, "2": 3.80}},
        ai_analysis={
            "summary": "Partido trabado, poco valor.",
            "confidence": 40,
            "agents": {"goleador": {"pick": "Under 2.5", "reason": "Equipos defensivos."}}
        }
    )

    with Session(engine) as session:
        for m in [match_pro, match_low]:
            existing = session.query(Match).filter(Match.api_id == m.api_id).first()
            if not existing:
                session.add(m)
        session.commit()
    
    print("✅ ¡Semilla Plantada! Base de datos lista para pruebas de UI.")

if __name__ == "__main__":
    create_fake_matches()