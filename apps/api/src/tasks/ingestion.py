import datetime
from celery import shared_task
from sqlmodel import Session, select
from src.db.session import engine
from src.models.match import Match
from src.services.football.real_service import RealFootballService
from src.services.football.mapper import DataMapper

# ─── CONFIGURACIÓN CENTRALIZADA DE LIGAS ───────────────────────────────────
# Fuente única de verdad para todos los workers de ingesta.
# Importar desde aquí: from src.tasks.ingestion import PRIORITY_LEAGUES, ALLOWED_LEAGUES

# Tier 1: Ligas top — se procesan primero por el sort de prioridad
PRIORITY_LEAGUES = [1, 2, 3, 39, 140, 135, 78, 61]  # 1 = Mundial FIFA

# Todas las ligas autorizadas (Tier 1 + Tier 2 regionales)
ALLOWED_LEAGUES = [
    1, 2, 3, 39, 140, 135, 78, 61,     # Tier 1: Mundial, UCL, UEL, Premier, La Liga, Serie A, Bundesliga, Ligue 1
    71, 128, 239, 242, 106, 13, 11,    # Tier 2: Brasil, Ecuador, Copa Sudamericana...
    143, 66, 137, 96, 206, 45, 48,     # Tier 2: Ligas secundarias europeas
    848, 204, 83                        # Tier 2: Resto de competiciones
]
# ────────────────────────────────────────────────────────────────────────────

@shared_task(name="src.tasks.ingestion.run_daily_ingestion")
def run_daily_ingestion():
    """
    Rutina A: La Cosecha Diaria.
    Se ejecuta automáticamente cada madrugada.
    """
    print("⏰ [CRON] Iniciando Ingesta Diaria Automática...")
    
    # 1. Instanciar Servicios
    football_service = RealFootballService()
    
    # 2. Definir fecha (Mañana)
    tomorrow = (datetime.date.today() + datetime.timedelta(days=1)).strftime("%Y-%m-%d")
    
    # 3. Abrir Sesión de Base de Datos (Manual porque no hay FastAPI Depends)
    with Session(engine) as session:
        # A. Bajar Partidos
        fixtures = football_service.get_fixtures_by_date(tomorrow)
        print(f"📥 [CRON] Encontrados {len(fixtures)} partidos para {tomorrow}")
        
        count = 0
        allowed = ALLOWED_LEAGUES  # Usa la config centralizada del módulo

        for fixture_data in fixtures:
            # B. Filtros ("El Portero")
            league_id = fixture_data["league"]["id"]
            if league_id not in allowed: continue
            
            api_id = str(fixture_data["fixture"]["id"])
            
            # C. Datos Tácticos
            odds = football_service.get_odds(api_id)
            injuries = football_service.get_injuries(api_id)
            prediction = football_service.get_predictions(api_id)
            
            if not odds: continue

            # D. Mapeo
            match_obj = DataMapper.fixture_to_match(fixture_data, odds_data=odds)
            match_obj = DataMapper.update_tactical_data(match_obj, injuries=injuries, prediction=prediction)
            
            # E. Guardado (Upsert)
            existing = session.exec(select(Match).where(Match.api_id == api_id)).first()
            if existing:
                existing.status = match_obj.status
                existing.odds_data = match_obj.odds_data
                existing.injuries = match_obj.injuries
                existing.api_prediction = match_obj.api_prediction
                session.add(existing)
            else:
                session.add(match_obj)
            
            count += 1
        
        session.commit()
        print(f"✅ [CRON] Ingesta Finalizada. {count} partidos procesados.")
    
    return f"Ingesta completada: {count} partidos"