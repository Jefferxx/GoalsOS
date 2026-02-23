"""
GoalOS — Scraper Understat xG
==============================
Extrae Expected Goals (xG) y Expected Goals Against (xGA) de Understat.com
para equipos de la Premier League (liga_id = EPL).

Understat embebe los datos como un objeto JavaScript dentro del HTML:
    <script> ... var teamsData = JSON.parse('...') ... </script>

Este scraper parsea ese payload sin necesidad de Selenium, usando solo
httpx (async) + BeautifulSoup + json.

Estándares aigents.md:
  ✅ async def + httpx para todo I/O externo
  ✅ Manejo seguro de None y formatos inesperados (.get())
  ✅ Sin lógica de negocio en main.py ni routers
"""

from __future__ import annotations

import json
import re
import asyncio
import logging
from dataclasses import dataclass
from typing import Optional

import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger("goalos.scrapers.understat")

# ─── CONSTANTES ───────────────────────────────────────────────────────────────
UNDERSTAT_BASE_URL = "https://understat.com"
# Liga IDs de Understat (distintos a los de API-Football)
LEAGUE_SLUGS = {
    "EPL":        "Premier League",
    "La_liga":    "La Liga",
    "Bundesliga": "Bundesliga",
    "Serie_A":    "Serie A",
    "Ligue_1":    "Ligue 1",
    "RFPL":       "Russian Premier League",
}
DEFAULT_LEAGUE = "EPL"
REQUEST_TIMEOUT = 15  # segundos

# Headers para simular un browser real y evitar bloqueos simples
_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/121.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}


# ─── DATACLASSES ──────────────────────────────────────────────────────────────

@dataclass
class TeamXGStats:
    """Estadísticas xG de un equipo para la temporada actual."""
    team_name: str
    league: str
    season: int

    # Totales de temporada
    xg_total: float         # xG producido (ataque)
    xga_total: float        # xG concedido (defensa)

    # Promedios por partido (los más útiles para el motor Poisson)
    xg_per_game: float
    xga_per_game: float

    # Métricas adicionales de Understat
    matches_played: int
    goals_scored: int
    goals_conceded: int

    # Diferencial de calidad: xG - xGA (positivo = equipo dominante)
    xg_diff: float

    def to_dict(self) -> dict:
        return {
            "team": self.team_name,
            "league": self.league,
            "season": self.season,
            "xg": {
                "total": round(self.xg_total, 2),
                "per_game": round(self.xg_per_game, 3),
            },
            "xga": {
                "total": round(self.xga_total, 2),
                "per_game": round(self.xga_per_game, 3),
            },
            "xg_differential": round(self.xg_diff, 2),
            "matches_played": self.matches_played,
            "goals": {
                "scored": self.goals_scored,
                "conceded": self.goals_conceded,
            },
        }


@dataclass
class LeagueXGSnapshot:
    """Snapshot completo de xG para todos los equipos de una liga."""
    league_slug: str
    season: int
    teams: list[TeamXGStats]

    def get_team(self, name_fragment: str) -> Optional[TeamXGStats]:
        """Búsqueda insensible a mayúsculas por fragmento de nombre."""
        name_lower = name_fragment.lower()
        for team in self.teams:
            if name_lower in team.team_name.lower():
                return team
        return None

    def to_dict(self) -> dict:
        return {
            "league": self.league_slug,
            "season": self.season,
            "team_count": len(self.teams),
            "teams": [t.to_dict() for t in self.teams],
        }


# ─── SCRAPER ──────────────────────────────────────────────────────────────────

class UnderstatScraper:
    """
    Scraper async para Understat.com.

    Uso:
        scraper = UnderstatScraper()
        snapshot = await scraper.get_league_xg(season=2024)
        arsenal = snapshot.get_team("Arsenal")
        # arsenal.xg_per_game -> 2.14

        # O directamente para un partido:
        home, away = await scraper.get_match_lambdas("Arsenal", "Chelsea", season=2024)
    """

    def __init__(self, timeout: int = REQUEST_TIMEOUT):
        self._timeout = timeout

    async def _fetch_html(self, url: str) -> Optional[str]:
        """Descarga HTML de forma asíncrona con httpx. Retorna None en error."""
        try:
            async with httpx.AsyncClient(
                headers=_HEADERS,
                timeout=self._timeout,
                follow_redirects=True,
            ) as client:
                logger.info(f"📡 [Understat] GET {url}")
                response = await client.get(url)
                response.raise_for_status()
                return response.text
        except httpx.TimeoutException:
            logger.error(f"⏱️ [Understat] Timeout en {url}")
            return None
        except httpx.HTTPStatusError as e:
            logger.error(f"🔥 [Understat] HTTP {e.response.status_code} en {url}")
            return None
        except Exception as e:
            logger.error(f"🔥 [Understat] Error inesperado: {e}")
            return None

    def _extract_json_var(self, html: str, var_name: str) -> Optional[dict | list]:
        """
        Extrae una variable JavaScript del HTML de Understat.
        Understat embebe los datos así:
            var teamsData = JSON.parse('{ ... }')
        El JSON interno está con comillas escapadas (\\' y unicode \\x).
        """
        # Patrón para capturar el contenido del JSON.parse('...')
        pattern = rf"var\s+{var_name}\s*=\s*JSON\.parse\('(.+?)'\)"
        match = re.search(pattern, html, re.DOTALL)
        if not match:
            logger.warning(f"⚠️ [Understat] Variable '{var_name}' no encontrada en HTML.")
            return None

        raw = match.group(1)
        # Understat escapa las comillas simples internas con backslash
        # También usa unicode escapes como \x22 (") y \x27 (')
        raw = raw.encode("utf-8").decode("unicode_escape")
        raw = raw.replace("\\'", "'").replace('\\"', '"')

        try:
            return json.loads(raw)
        except json.JSONDecodeError as e:
            logger.error(f"❌ [Understat] Error parseando JSON de '{var_name}': {e}")
            return None

    def _parse_teams_data(
        self, teams_data: dict, league_slug: str, season: int
    ) -> list[TeamXGStats]:
        """
        Transforma el dict crudo de Understat en objetos TeamXGStats.
        Formato de entrada: { "team_id": { "title": "...", "xG": "...", "xGA": "...", ... } }
        """
        result = []
        league_label = LEAGUE_SLUGS.get(league_slug, league_slug)

        for team_id, data in teams_data.items():
            try:
                title       = data.get("title", f"Team_{team_id}")
                xg_total    = float(data.get("xG",   0) or 0)
                xga_total   = float(data.get("xGA",  0) or 0)
                matches     = int(data.get("matches", 0) or 1)   # evitar div/0
                scored      = int(data.get("scored",  0) or 0)
                missed      = int(data.get("missed",  0) or 0)

                result.append(TeamXGStats(
                    team_name=title,
                    league=league_label,
                    season=season,
                    xg_total=xg_total,
                    xga_total=xga_total,
                    xg_per_game=xg_total / matches,
                    xga_per_game=xga_total / matches,
                    matches_played=matches,
                    goals_scored=scored,
                    goals_conceded=missed,
                    xg_diff=xg_total - xga_total,
                ))
            except (ValueError, TypeError, ZeroDivisionError) as e:
                logger.warning(f"⚠️ [Understat] Error parseando equipo {team_id}: {e}")
                continue

        # Ordenar por xG_diff descendente (mejores equipos arriba)
        return sorted(result, key=lambda t: t.xg_diff, reverse=True)

    async def get_league_xg(
        self,
        league_slug: str = DEFAULT_LEAGUE,
        season: int = 2024,
    ) -> Optional[LeagueXGSnapshot]:
        """
        Obtiene el snapshot completo de xG para todos los equipos de una liga.

        Args:
            league_slug: Slug de Understat (ej. "EPL", "La_liga", "Bundesliga")
            season: Año de inicio de la temporada (ej. 2024 para 2024/25)

        Returns:
            LeagueXGSnapshot con stats de todos los equipos, o None si falla.
        """
        if league_slug not in LEAGUE_SLUGS:
            raise ValueError(
                f"Liga '{league_slug}' no soportada. "
                f"Opciones: {list(LEAGUE_SLUGS.keys())}"
            )

        url = f"{UNDERSTAT_BASE_URL}/league/{league_slug}/{season}"
        html = await self._fetch_html(url)
        if not html:
            return None

        teams_data = self._extract_json_var(html, "teamsData")
        if not teams_data:
            return None

        teams = self._parse_teams_data(teams_data, league_slug, season)
        logger.info(f"✅ [Understat] {len(teams)} equipos extraídos para {league_slug} {season}.")

        return LeagueXGSnapshot(
            league_slug=league_slug,
            season=season,
            teams=teams,
        )

    async def get_match_lambdas(
        self,
        home_team: str,
        away_team: str,
        league_slug: str = DEFAULT_LEAGUE,
        season: int = 2024,
    ) -> tuple[Optional[float], Optional[float]]:
        """
        Retorna (lambda_home, lambda_away) listos para el PoissonEngine.
        Usa xg_per_game del local y xga_per_game del visitante para estimar
        cuántos goles esperamos que marque el local, y viceversa.

        Fórmula:
            λ_home = (xg_home_ataque + xga_away_defensa) / 2
            λ_away = (xg_away_ataque + xga_home_defensa) / 2

        Args:
            home_team: Fragmento del nombre del equipo local (ej. "Arsenal")
            away_team: Fragmento del nombre del equipo visitante (ej. "Chelsea")

        Returns:
            Tupla (lambda_home, lambda_away) o (None, None) si no encuentra equipos.
        """
        snapshot = await self.get_league_xg(league_slug=league_slug, season=season)
        if not snapshot:
            logger.error("❌ [Understat] No se pudo obtener el snapshot de liga.")
            return None, None

        home_stats = snapshot.get_team(home_team)
        away_stats = snapshot.get_team(away_team)

        if not home_stats:
            logger.warning(f"⚠️ [Understat] Equipo local '{home_team}' no encontrado.")
        if not away_stats:
            logger.warning(f"⚠️ [Understat] Equipo visitante '{away_team}' no encontrado.")

        if not home_stats or not away_stats:
            return None, None

        # λ combinado: promedio entre la capacidad atacante del equipo y la
        # debilidad defensiva del rival (modelo de fuerza relativa)
        lambda_home = (home_stats.xg_per_game + away_stats.xga_per_game) / 2
        lambda_away = (away_stats.xg_per_game + home_stats.xga_per_game) / 2

        logger.info(
            f"🎯 [Understat] {home_team} vs {away_team} → "
            f"λ_home={lambda_home:.3f}, λ_away={lambda_away:.3f}"
        )

        return round(lambda_home, 3), round(lambda_away, 3)
