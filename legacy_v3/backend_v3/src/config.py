"""
Configuraciones globales del proyecto GoalOS.
"""
import os

# IDs de ligas permitidas (API-Football)
LEAGUES_WHITELIST = [
    # --- 🌍 ELITE EUROPEA ---
    39,   # Premier League
    140,  # La Liga
    135,  # Serie A
    78,   # Bundesliga
    61,   # Ligue 1
    2,    # Champions League
    3,    # Europa League
    
    # --- 🏆 REYES DE LATAM ---
    13,   # Copa Libertadores
    848,  # Copa Sudamericana
    128,  # Liga Profesional Argentina
    71,   # Brasileirão Serie A
    72,   # Brasileirão Serie B
    239,  # Primera A Colombia
    242,  # LigaPro Ecuador
    265,  # Primera División Chile
    268,  # Primera División Uruguay
    
    # --- 🇧🇷 ESTADUALES (Enero - Abril) ---
    106,  # Campeonato Paulista A1
    83,   # Campeonato Carioca Série A
    82,   # Campeonato Mineiro Módulo I
    102,  # Campeonato Gaúcho 1
    95,   # Campeonato Baiano 1

    # --- 💰 MINAS DE ORO (Goles) ---
    88,   # Eredivisie
    89,   # Eerste Divisie
    79,   # 2. Bundesliga
    203,  # Süper Lig
    144,  # Jupiler Pro League
    218,  # Bundesliga Austria
    207,  # Swiss Super League
    
    # --- ❄️ ESCANDINAVIA ---
    103,  # Eliteserien
    113,  # Allsvenskan
    119,  # Superliga
    
    # --- 🌎 RESTO DEL MUNDO ---
    253,  # MLS
    188,  # A-League
    98    # J1 League
]

# Límite diario del plan gratuito
MAX_DAILY_REQUESTS = 100