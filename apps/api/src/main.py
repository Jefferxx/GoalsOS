from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.concurrency import run_in_threadpool

# --- IMPORTS PROPIOS ---
from src.db.session import init_db
from src.celery_app import celery_app  # Registra esta app (Redis) como la "current app" de Celery
from src.services.football.real_service import RealFootballService
from src.routers import bets, wallet, matches, auth, teams
from src.routers import analysis

# --- LIFESPAN (ARRANQUE) ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    # INICIO
    init_db()
    print("🦅 GoalOS Enterprise DB Iniciada.")
    yield # App corre aquí

app = FastAPI(title="GoalOS Enterprise API", version="6.5.0 (Silicon Valley Ed.)", lifespan=lifespan)

origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

football_service = RealFootballService()

# --- REGISTRO DE RUTAS ---
app.include_router(bets.router)
app.include_router(wallet.router)
app.include_router(matches.router)
app.include_router(auth.router)
app.include_router(analysis.router)  # Sprint 1: Motor Poisson + Understat
app.include_router(teams.router)  # Históricos de equipo (a pedido + caché 18h)

# --- ENDPOINTS BÁSICOS ---
@app.get("/")
async def read_root():
    return {"system": "GoalOS v6.5", "status": "Online", "mode": "Automated"}

@app.get("/api-status")
async def get_api_status():
    """Chequeo de estado asíncrono para el API de Fútbol"""
    def fetch_status():
        res = football_service._get("status")
        if res:
            requests_info = res.get("requests", {})
            return {
                "current": requests_info.get("current", 0),
                "limit": requests_info.get("limit_day", 100),
                "remaining": (requests_info.get("limit_day", 100) - requests_info.get("current", 0))
            }
        return {"current": 0, "limit": 100, "remaining": 0}
        
    return await run_in_threadpool(fetch_status)