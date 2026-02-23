import requests
import os
import json
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

class StatsService:
    def __init__(self):
        self.api_key = os.getenv("API_FOOTBALL_KEY")
        self.base_url = "https://v3.football.api-sports.io"
        self.headers = {
            'x-rapidapi-host': "v3.football.api-sports.io",
            'x-rapidapi-key': self.api_key
        }

    def _fetch(self, endpoint):
        """Helper robusto: siempre devuelve una lista."""
        try:
            url = f"{self.base_url}/{endpoint}"
            response = requests.get(url, headers=self.headers)
            if response.status_code == 200:
                data = response.json()
                if "errors" in data and data["errors"]:
                    print(f"⚠️ API Error: {data['errors']}")
                    return []
                return data.get("response", []) if isinstance(data.get("response"), list) else []
            return []
        except Exception as e:
            print(f"   ⚠️ Error fetch {endpoint}: {e}")
            return []

    def get_match_context(self, match_id, home_id, away_id, league_id, season, manual_input=None):
        """
        Versión V2.7 (Filtro Inteligente de Fechas):
        1. Recupera H2H.
        2. FILTRA partidos con antigüedad > 4 años (RF-04).
        3. Formatea y limpia datos para la IA.
        """
        if not self.api_key: return {"text": "Error: No API Key.", "json": None}

        print(f"📡 [StatsService] Construyendo contexto para API ID {match_id}...")
        
        try:
            # --- 1. HISTORIAL H2H ---
            h2h_raw = self._fetch(f"fixtures/headtohead?h2h={home_id}-{away_id}")
            clean_h2h = []
            
            # Año actual para el filtro (RF-04)
            current_year = datetime.now().year
            cutoff_year = current_year - 4  # Ej: 2026 - 4 = 2022. Ignorar < 2022.
            
            if h2h_raw:
                # Ordenar por fecha descendente (más reciente primero)
                h2h_raw.sort(key=lambda x: x['fixture']['date'], reverse=True)
                
                for h in h2h_raw:
                    try:
                        # --- FILTRO RF-04: OBSOLESCENCIA ---
                        match_date_str = h['fixture']['date']
                        match_year = int(match_date_str[:4])
                        
                        if match_year < cutoff_year:
                            continue # Saltamos partidos muy viejos
                        
                        # Filtro de estado (Solo terminados)
                        if h['fixture']['status']['short'] not in ['FT', 'AET', 'PEN']:
                            continue
                        
                        goals_h = h['goals']['home']
                        goals_a = h['goals']['away']
                        
                        if goals_h is None or goals_a is None:
                            continue

                        clean_item = {
                            "date": match_date_str.split('T')[0],
                            "home": h['teams']['home']['name'],
                            "away": h['teams']['away']['name'],
                            "score": f"{goals_h}-{goals_a}"
                        }
                        clean_h2h.append(clean_item)
                    except: continue

                # Nos quedamos solo con los Top 5 más recientes tras el filtro
                clean_h2h = clean_h2h[:5]

            # --- 2. CONSTRUCCIÓN DEL REPORTE TEXTUAL PARA LA IA ---
            text_output = "--- REPORTE DE ANÁLISIS TÁCTICO (V2.7) ---\n\n"
            
            text_output += f"1. HISTORIAL DIRECTO (H2H - Desde {cutoff_year}):\n"
            if clean_h2h:
                for h in clean_h2h:
                    text_output += f"   - {h['date']}: {h['home']} {h['score']} {h['away']}\n"
            else:
                text_output += "   - Sin enfrentamientos recientes relevantes (Data obsoleta filtrada).\n"

            # Inyección de datos manuales (Cyborg)
            if manual_input and len(manual_input) > 5:
                text_output += "\n2. FORMA RECIENTE Y NOTICIAS (Fuente: Análisis Manual):\n"
                text_output += f"{manual_input}\n"
                text_output += "\n⚠️ INSTRUCCIÓN AL ANALISTA: Prioriza estos datos manuales (lesiones, racha actual) sobre el H2H histórico si hay contradicción."
            else:
                text_output += "\n2. FORMA RECIENTE:\n   - No provista. El análisis se basará puramente en probabilidad H2H y Valor Esperado."

            # JSON estructurado para el Frontend
            full_json = {
                "h2h": clean_h2h, 
                "filter_year": cutoff_year
            }

            return {"text": text_output, "json": full_json}

        except Exception as e:
            print(f"❌ [StatsService] Error Crítico: {e}")
            return {"text": f"Error obteniendo stats: {str(e)}", "json": None}