import streamlit as st
import requests
import pandas as pd
import time
import os
import hashlib # <--- Para generar el token de sesión
from datetime import datetime, timedelta
from dotenv import load_dotenv
import altair as alt 

# Cargar variables de entorno (para local)
load_dotenv()

# --- CONFIGURACIÓN DE PÁGINA (WIDE MODE) ---
st.set_page_config(
    page_title="GoalOS V3.0 - Terminal",
    page_icon="🦅",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CONFIGURACIÓN DE API (URL DINÁMICA) ---
API_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8000")

# --- LOGIN PERSISTENTE (RF-15) ---
def check_password():
    """
    Retorna True si el usuario está logueado.
    Usa parámetros de URL para mantener la sesión activa tras F5.
    """
    # 1. Obtener la contraseña real
    secret_password = os.getenv("DASHBOARD_PASSWORD", "admin123")
    
    # 2. Generar un hash simple (token) de la contraseña para la URL
    session_token = hashlib.sha256(secret_password.encode()).hexdigest()[:12]

    # 3. Verificar si ya tiene el token en la URL (Persistencia)
    query_params = st.query_params
    if query_params.get("auth") == session_token:
        st.session_state.password_correct = True
        return True

    # 4. Verificar si ya pasó por el login en esta ejecución
    if st.session_state.get("password_correct", False):
        return True

    # 5. Interfaz de Login
    st.markdown("## 🦅 Acceso Restringido - GoalOS")
    st.caption("Solo personal autorizado: Jefferson & Fernando")
    pwd = st.text_input("Contraseña de Acceso:", type="password")
    
    if st.button("Entrar"):
        if pwd == secret_password:  
            st.session_state.password_correct = True
            # INYECTAMOS EL TOKEN EN LA URL PARA QUE NO PIDA CLAVE AL REFRESCAR
            st.query_params["auth"] = session_token
            st.rerun()
        else:
            st.error("🚫 Acceso Denegado")
    return False

if not check_password():
    st.stop() # Detiene la ejecución si no hay login

# --- INICIALIZACIÓN DE ESTADO ---
if 'analyzed_ids' not in st.session_state:
    st.session_state.analyzed_ids = set()

# --- ESTILOS CSS PRO (V3.0) ---
st.markdown("""
    <style>
    /* Métricas Superiores */
    .stMetric {
        background-color: #12141C;
        padding: 15px;
        border-radius: 10px;
        border-left: 4px solid #00D084;
        box-shadow: 0 2px 4px rgba(0,0,0,0.2);
    }
    
    /* Etiquetas de Ligas */
    .league-tag {
        background-color: #262730;
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 0.8em;
        color: #FFD700;
        border: 1px solid #444;
        margin-right: 5px;
    }

    /* Botones de Acción */
    .stButton>button {
        border-radius: 6px;
        font-weight: 600;
        width: 100%;
    }
    
    /* Expander Headers más limpios */
    .streamlit-expanderHeader {
        font-weight: 600 !important;
        background-color: #1E2130 !important;
    }
    </style>
""", unsafe_allow_html=True)

# --- FUNCIONES AUXILIARES ---
def get_data(endpoint):
    try: 
        response = requests.get(f"{API_URL}/{endpoint}")
        response.raise_for_status()
        return response.json()
    except: return {}

def post_data(endpoint, payload=None):
    try: 
        response = requests.post(f"{API_URL}/{endpoint}", json=payload)
        response.raise_for_status()
        return response.json()
    except: return {"status": "error"}

def format_market_name(raw_name, match_title=""):
    """
    Traduce los códigos de la API a texto legible.
    CORRECCIÓN: Detección precisa de equipos en 1X2.
    """
    if not raw_name: return "Mercado Desconocido"
    name = raw_name.upper()
    
    # --- BTTS (Ambos Marcan) ---
    if "BTTS" in name or "AMBOS" in name:
        if "NO" in name or "NUNCA" in name: return "🧤 Ambos Marcan: NO"
        return "🥅 Ambos Equipos Marcan: SÍ"
        
    # --- GOLES ---
    if "OVER" in name and "2.5" in name: return "⚽ +2.5 Goles (Over)"
    if "UNDER" in name and "2.5" in name: return "🛡️ -2.5 Goles (Under)"
    
    # --- GANADOR (1X2) - Lógica Blindada ---
    if "1X2" in name or "GANADOR" in name:
        # 1. Chequeo de Empate Explícito
        if "DRAW" in name or "EMPATE" in name:
            return "🤝 Empate"
            
        # 2. Chequeo de Local/Visita Genérico
        if "HOME" in name or "LOCAL" in name: return "🏆 Gana Local"
        if "AWAY" in name or "VISITA" in name: return "🏆 Gana Visita"
        
        # 3. Inteligencia de Nombres (Extraer del título)
        if match_title and " vs " in match_title:
            try:
                teams = match_title.split(" vs ")
                home_team = teams[0].strip()
                away_team = teams[1].strip()
                
                # Limpiar la selección de palabras basura para comparar mejor
                clean_sel = name.replace("GANADOR DIRECTO", "").replace("-", "").strip()
                
                # Búsqueda flexible (Si "Barcelona" está en "Ganador Barcelona")
                if home_team.upper() in clean_sel: return f"🏆 Gana {home_team}"
                if away_team.upper() in clean_sel: return f"🏆 Gana {away_team}"
            except: pass
        
        # 4. Fallback Seguro (Si falla todo, muestra el nombre original en vez de inventar "Empate")
        return f"🏆 {raw_name.replace('GANADOR DIRECTO -', '').strip()}"
        
    # --- DOBLE OPORTUNIDAD ---
    if "DOBLE" in name or "DOUBLE" in name:
        if "EMPATE" in name: return "🛡️ Doble Oportunidad (1X / X2)"
        return "⚡ Doble Oportunidad (12)"

    return raw_name.title()

def convert_time(utc_time_str):
    try:
        utc_time = datetime.strptime(utc_time_str, "%H:%M")
        ec_time = utc_time - timedelta(hours=5)
        return ec_time.strftime("%H:%M")
    except: return utc_time_str

def process_h2h_data(h2h_list):
    processed = []
    for m in h2h_list:
        try:
            processed.append({
                "Fecha": m.get('date', '-'),
                "Local": m.get('home', '-'),
                "Marcador": m.get('score', '-'),
                "Visita": m.get('away', '-')
            })
        except: continue
    return processed

# --- CARGA DE DATOS INICIAL ---
bank = get_data("bankroll")
matches_data = get_data("view-matches") 
bets_data = get_data("my-bets").get("bets", [])

upcoming_raw = matches_data.get("upcoming", [])
finished_raw = matches_data.get("finished", [])

# Filtrar analizados localmente
pending_analysis = [
    m for m in upcoming_raw 
    if not m.get('prediction') and m['id'] not in st.session_state.analyzed_ids
]

# --- SIDEBAR COMPLETO CON VISOR API ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2534/2534199.png", width=50)
    st.header("GoalOS V3.0")
    
    # --- 🔋 VISOR DE CONSUMO API (NUEVO) ---
    usage = get_data("api-usage")
    if usage:
        curr = usage.get("current", 0)
        lim = usage.get("limit", 100)
        pct = usage.get("percent", 0)
        
        # Color dinámico: Verde (bien), Naranja (medio), Rojo (peligro)
        # Nota: Streamlit progress bar usa float 0.0 - 1.0
        st.caption(f"📡 Consumo API: {curr}/{lim} ({pct}%)")
        st.progress(curr / lim if lim > 0 else 0)
        
        if pct >= 90:
            st.error("⚠️ ¡Límite diario casi lleno!")
    
    st.markdown("---")
    
    st.markdown("### 🎲 Parley Builder")
    available_leagues = sorted(list(set([m['league'] for m in upcoming_raw if m.get('league')])))
    league_filter = st.selectbox("Filtrar Liga:", ["Todas"] + available_leagues)
    
    if st.button("⚡ Generar Combo"):
        parlay_res = get_data(f"recommend-parlay?league_filter={league_filter}")
        if parlay_res.get("status") == "success":
            combos = parlay_res.get("combos", {})
            for type_name, data in combos.items():
                if data:
                    with st.expander(f"{data['name']} (@{data['total_odds']})"):
                        for p in data['picks']:
                            st.caption(f"⚽ {p['match']}")
                            st.markdown(f"**{format_market_name(p['selection'], p['match'])}**")
                        st.button(f"📌 Guardar {type_name}", key=f"btn_{type_name}")
        else:
            st.warning("Insuficientes apuestas pendientes.")

    st.divider()
    col1, col2 = st.columns(2)
    if col1.button("🔄 Sync"):
        with st.spinner("Sincronizando..."):
            get_data("sync-matches")
            time.sleep(1)
            st.rerun()
    if col2.button("🕵️ Auditar"):
        with st.spinner("Auditando..."):
            res = post_data("settle-bets")
            st.success(f"P/L: ${res.get('total_profit', 0)}")
            time.sleep(1)
            st.rerun()
    
    # --- 🔥 GESTIÓN DE BANCA SIMPLIFICADA (RF-14 Update) ---
    st.divider()
    with st.expander("🏦 Mi Banca Real"):
        current_val = float(bank.get('current_balance', 0.0))
        
        # Input directo del saldo real
        real_balance = st.number_input(
            "Saldo en Betano ($):", 
            value=current_val, 
            step=10.0,
            format="%.2f"
        )
        
        if st.button("💾 Actualizar Sistema", use_container_width=True):
            if real_balance >= 0:
                payload = {
                    "type": "SET_REAL_BALANCE", 
                    "amount": real_balance, 
                    "description": "Ajuste por usuario"
                }
                with st.spinner("Sincronizando..."):
                    res = post_data("manage-funds", payload)
                    
                if res.get("status") == "success":
                    st.toast(f"✅ Banca actualizada a: ${real_balance}")
                    time.sleep(1)
                    st.rerun()
                elif res.get("status") == "info":
                    st.info("El saldo ya está actualizado.")
                else:
                    st.error("Error al actualizar.")
            else:
                st.error("El saldo no puede ser negativo.")

    # --- BOTÓN DE LOGOUT ---
    st.divider()
    if st.button("🔒 Cerrar Sesión"):
        st.session_state.password_correct = False
        st.query_params.clear() # Borra el token de la URL
        st.rerun()

# --- HEADER ---
k1, k2, k3, k4 = st.columns(4)
active_bets_list = [b for b in bets_data if b['status'] == 'PENDING']
history_bets_list = [b for b in bets_data if b['status'] != 'PENDING']
today_profit = sum([b['profit'] for b in bets_data if b['status'] in ['WON', 'LOST']])

k1.metric("Capital Total", f"${bank.get('current_balance', 0)}", delta=f"{len(active_bets_list)} en juego")
k2.metric("Partidos Disponibles", len(upcoming_raw))
k3.metric("Tickets Activos", len(active_bets_list))
k4.metric("Profit Sesión", f"${round(today_profit, 2)}", delta_color="normal")

st.markdown("---")

# --- PESTAÑAS ---
tab_ops, tab_portfolio = st.tabs(["🌍 Terminal de Operaciones", "🎫 Cartera & Historial"])

# --- TAB 1: OPERACIONES ---
with tab_ops:
    c_top, c_auto = st.columns([3, 1])
    with c_auto:
        if st.button("⚡ Ejecutar Auto-Bet (Lote)"):
            with st.spinner("Procesando órdenes automáticas..."):
                res = post_data("auto-bet")
                st.toast(f"✅ {res.get('bets_created', 0)} apuestas colocadas.")
                time.sleep(1)
                st.rerun()

    if not upcoming_raw:
        st.info("No hay partidos en la agenda para hoy.")
    else:
        df = pd.DataFrame(upcoming_raw)
        df['time'] = df['time'].apply(convert_time)
        
        if 'league' in df.columns:
            leagues = df['league'].unique()
            for league in sorted(leagues):
                league_matches = df[df['league'] == league]
                with st.expander(f"🏆 {league} ({len(league_matches)} partidos)", expanded=True):
                    for _, row in league_matches.iterrows():
                        c_time, c_match, c_status, c_action = st.columns([1, 4, 2, 2])
                        c_time.caption(row['time'])
                        c_match.markdown(f"**{row['teams']}**")
                        
                        is_analyzed = row.get('prediction') is not None
                        is_local_processed = row['id'] in st.session_state.analyzed_ids
                        
                        if is_analyzed:
                            pred = row['prediction']
                            # Pasamos el nombre del partido para formatear bien
                            market_nice = format_market_name(pred.get('selection', ''), row['teams'])
                            c_status.success(f"✅ {market_nice}")
                            c_action.empty()
                        elif is_local_processed:
                            c_status.info("🔄 Procesado")
                            c_action.empty()
                        else:
                            c_status.warning("⏳ Pendiente")
                            with c_action:
                                with st.popover("🧠 Analizar"):
                                    st.markdown(f"**{row['teams']}**")
                                    manual_txt = st.text_area("Datos Manuales:", key=f"txt_{row['id']}", height=100)
                                    if st.button("🚀 Ejecutar", key=f"btn_an_{row['id']}"):
                                        with st.spinner("Consultando IA..."):
                                            payload = {"match_id": row['id'], "manual_text": manual_txt}
                                            res = post_data("analyze-single", payload)
                                            if res.get("status") == "success":
                                                st.session_state.analyzed_ids.add(row['id'])
                                                st.success("¡Listo!")
                                                time.sleep(1)
                                                st.rerun()
                                            else:
                                                st.error("Error")
        else:
            st.warning("Datos de liga no disponibles.")

# --- TAB 2: CARTERA ---
with tab_portfolio:
    st.markdown("### 🔥 En Juego (Pending)")
    if not active_bets_list:
        st.info("No hay apuestas activas.")
    
    for bet in active_bets_list:
        # Pasamos el nombre del partido para formatear bien
        market_pretty = format_market_name(bet['selection'], bet['match'])
        ticket_title = f"⏳ {bet['match']} {bet.get('match_score', '')} | {market_pretty}"
        
        with st.expander(ticket_title, expanded=True):
            c1, c2, c3 = st.columns(3)
            c1.write(f"**Stake:** ${bet['stake']}")
            c2.write(f"**Cuota:** {bet['odds']}")
            c3.write("**Estado:** Esperando resultado...")
            
            st.divider()
            new_odds = st.number_input("Ajustar Cuota:", value=float(bet['odds']), key=f"o_{bet['id']}")
            if st.button("Recalcular Kelly", key=f"k_{bet['id']}"):
                post_data("update-bet-odds", {"bet_id": bet['id'], "real_odds": new_odds})
                st.rerun()
            
            if 'reasoning' in bet: st.caption(f"🧠 **IA:** {bet['reasoning']}")

    st.markdown("---")
    st.markdown("### 📜 Historial Auditado")
    with st.expander(f"Ver {len(history_bets_list)} Tickets Cerrados", expanded=False):
        if not history_bets_list:
            st.info("No hay historial aún.")
        
        hist_data = []
        for bet in history_bets_list:
            status_icon = "✅" if bet['status'] == "WON" else "❌" if bet['status'] == "LOST" else "⛔"
            # Pasamos el nombre del partido para formatear bien
            market_fixed = format_market_name(bet['selection'], bet['match'])
            
            hist_data.append({
                "Estado": status_icon,
                "Partido": f"{bet['match']} {bet.get('match_score', '')}",
                "Selección": market_fixed,
                "Cuota": bet['odds'],
                "P/L": bet['profit']
            })
        
        if hist_data:
            st.dataframe(pd.DataFrame(hist_data), use_container_width=True, hide_index=True)