"""
GoalOS — Motor de Probabilidades Poisson
=========================================
Servicio de cálculo de probabilidades para mercados de apuestas deportivas
usando la distribución de Poisson (scipy.stats).

Mercados implementados:
  - 1X2 (Victoria Local / Empate / Victoria Visitante)
  - Over/Under 2.5 goles

Referencia matemática:
  - P(k goles) = (λ^k * e^-λ) / k!
  - λ_home / λ_away se estiman desde xG (Expected Goals)
  - La probabilidad de empate requiere sumar P(k=k) para todos los k
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Optional
from functools import partial

from scipy.stats import poisson
from scipy.special import factorial
import numpy as np


# ─── CONSTANTES ───────────────────────────────────────────────────────────────
# Máximo de goles a contemplar en la distribución (truncado en 10 es suficiente
# para cualquier partido; P(X>=10) es prácticamente 0 con λ < 4)
_MAX_GOALS = 10

# Factor de ventaja local promedio en el fútbol europeo de élite
# Fuente: literature review Maher (1982), Dixon & Coles (1997)
HOME_ADVANTAGE_FACTOR = 1.10


# ─── DATACLASSES DE RESULTADO ─────────────────────────────────────────────────

@dataclass
class PoissonResult1X2:
    """Probabilidades para el mercado 1X2."""
    home_win: float             # P(Home Goals > Away Goals)
    draw: float                 # P(Home Goals == Away Goals)
    away_win: float             # P(Away Goals > Home Goals)
    lambda_home: float          # λ esperado del equipo local
    lambda_away: float          # λ esperado del equipo visitante
    implied_home_odds: float    # Cuota justa implícita (1 / prob)
    implied_draw_odds: float
    implied_away_odds: float

    def to_dict(self) -> dict:
        return {
            "market": "1X2",
            "probabilities": {
                "1": round(self.home_win, 4),
                "X": round(self.draw, 4),
                "2": round(self.away_win, 4),
            },
            "implied_fair_odds": {
                "1": round(self.implied_home_odds, 2),
                "X": round(self.implied_draw_odds, 2),
                "2": round(self.implied_away_odds, 2),
            },
            "model_inputs": {
                "lambda_home": round(self.lambda_home, 3),
                "lambda_away": round(self.lambda_away, 3),
            },
        }


@dataclass
class PoissonResultOU:
    """Probabilidades para el mercado Over/Under 2.5 goles."""
    over: float      # P(Total Goals > 2.5)  ≡  P(Total Goals >= 3)
    under: float     # P(Total Goals <= 2)
    lambda_total: float
    implied_over_odds: float
    implied_under_odds: float

    def to_dict(self) -> dict:
        return {
            "market": "Over/Under 2.5",
            "probabilities": {
                "over_2.5": round(self.over, 4),
                "under_2.5": round(self.under, 4),
            },
            "implied_fair_odds": {
                "over_2.5": round(self.implied_over_odds, 2),
                "under_2.5": round(self.implied_under_odds, 2),
            },
            "model_inputs": {
                "lambda_total": round(self.lambda_total, 3),
            },
        }


@dataclass
class FullPoissonAnalysis:
    """Resultado completo del motor Poisson para un partido."""
    result_1x2: PoissonResult1X2
    result_ou: PoissonResultOU
    value_bets: list[dict] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "1X2": self.result_1x2.to_dict(),
            "over_under": self.result_ou.to_dict(),
            "value_bets": self.value_bets,
        }


# ─── MOTOR PRINCIPAL ──────────────────────────────────────────────────────────

class PoissonEngine:
    """
    Motor de probabilidades Poisson para mercados de fútbol.

    Uso:
        engine = PoissonEngine()
        result = await engine.analyze(xg_home=1.8, xg_away=1.1)
        result = await engine.analyze(xg_home=1.8, xg_away=1.1, odds_home=2.10, odds_draw=3.40, odds_away=3.60)
    """

    def _compute_1x2(
        self, lambda_home: float, lambda_away: float
    ) -> PoissonResult1X2:
        """
        Calcula la matriz de probabilidades de marcador y colapsa a 1X2.
        Complejidad O(MAX_GOALS^2) — pura CPU, ejecutar en threadpool.
        """
        k_range = np.arange(0, _MAX_GOALS + 1)

        # Vectores de probabilidad Poisson para cada equipo
        prob_home = poisson.pmf(k_range, lambda_home)   # P(home = k)
        prob_away = poisson.pmf(k_range, lambda_away)   # P(away = k)

        # Matriz de marcadores exactos: M[i][j] = P(home=i, away=j)
        score_matrix = np.outer(prob_home, prob_away)

        # Sumar triángulos de la matriz
        home_win = float(np.sum(np.tril(score_matrix, -1)))   # home > away
        away_win = float(np.sum(np.triu(score_matrix, 1)))    # away > home
        draw     = float(np.sum(np.diag(score_matrix)))       # home == away

        # Normalización (manejo de precision floating point)
        total = home_win + away_win + draw
        home_win /= total
        away_win /= total
        draw     /= total

        return PoissonResult1X2(
            home_win=home_win,
            draw=draw,
            away_win=away_win,
            lambda_home=lambda_home,
            lambda_away=lambda_away,
            implied_home_odds=1 / home_win if home_win > 0 else 99.0,
            implied_draw_odds=1 / draw     if draw     > 0 else 99.0,
            implied_away_odds=1 / away_win if away_win > 0 else 99.0,
        )

    def _compute_ou(
        self, lambda_home: float, lambda_away: float
    ) -> PoissonResultOU:
        """
        Over/Under 2.5: suma la distribución de la convolución Poisson(λ_home + λ_away).
        La suma de dos Poisson independientes es Poisson(λ₁ + λ₂).
        """
        lambda_total = lambda_home + lambda_away
        # Under 2.5 = P(0 goles) + P(1 gol) + P(2 goles)
        under = float(poisson.cdf(2, lambda_total))
        over  = 1.0 - under

        return PoissonResultOU(
            over=over,
            under=under,
            lambda_total=lambda_total,
            implied_over_odds=1 / over  if over  > 0 else 99.0,
            implied_under_odds=1 / under if under > 0 else 99.0,
        )

    def _detect_value_bets(
        self,
        result_1x2: PoissonResult1X2,
        result_ou: PoissonResultOU,
        odds_home: Optional[float],
        odds_draw: Optional[float],
        odds_away: Optional[float],
        odds_over: Optional[float],
        odds_under: Optional[float],
        edge_threshold: float = 0.05,
    ) -> list[dict]:
        """
        Detecta Value Bets comparando probabilidades del modelo vs cuotas del mercado.
        Value Bet: prob_model > prob_implícita + edge_threshold (5% por defecto)
        """
        value_bets = []

        candidates = [
            ("1 (Local)",         result_1x2.home_win, odds_home),
            ("X (Empate)",        result_1x2.draw,     odds_draw),
            ("2 (Visitante)",     result_1x2.away_win, odds_away),
            ("Over 2.5",          result_ou.over,      odds_over),
            ("Under 2.5",         result_ou.under,     odds_under),
        ]

        for label, prob_model, odd in candidates:
            if odd is None or odd <= 1.0:
                continue
            prob_market = 1.0 / odd
            edge = prob_model - prob_market
            if edge >= edge_threshold:
                value_bets.append({
                    "selection": label,
                    "model_probability": round(prob_model, 4),
                    "market_probability": round(prob_market, 4),
                    "edge": round(edge, 4),
                    "market_odds": round(odd, 2),
                    "fair_odds": round(1 / prob_model, 2) if prob_model > 0 else None,
                    "verdict": "✅ VALUE BET",
                })

        return sorted(value_bets, key=lambda x: x["edge"], reverse=True)

    async def analyze(
        self,
        xg_home: float,
        xg_away: float,
        apply_home_advantage: bool = True,
        odds_home: Optional[float] = None,
        odds_draw: Optional[float] = None,
        odds_away: Optional[float] = None,
        odds_over: Optional[float] = None,
        odds_under: Optional[float] = None,
        edge_threshold: float = 0.05,
    ) -> FullPoissonAnalysis:
        """
        Punto de entrada principal. Es async para cumplir con aigents.md.
        El cálculo CPU-bound se delega a asyncio.to_thread para no bloquear el event loop.

        Args:
            xg_home: xG esperado del equipo local (ej. 1.8)
            xg_away: xG esperado del equipo visitante (ej. 1.1)
            apply_home_advantage: Aplica factor 1.10 al lambda del local
            odds_*: Cuotas del mercado para detección de value bets
            edge_threshold: Ventaja mínima sobre el mercado para declarar value bet

        Returns:
            FullPoissonAnalysis con 1X2, O/U y value bets detectados
        """
        if xg_home <= 0 or xg_away <= 0:
            raise ValueError(
                f"xG debe ser > 0. Recibido: home={xg_home}, away={xg_away}"
            )

        lambda_home = xg_home * (HOME_ADVANTAGE_FACTOR if apply_home_advantage else 1.0)
        lambda_away = xg_away

        # Ejecutar cómputo bloqueante en thread separado (no bloquea el event loop)
        result_1x2, result_ou = await asyncio.gather(
            asyncio.to_thread(self._compute_1x2, lambda_home, lambda_away),
            asyncio.to_thread(self._compute_ou,  lambda_home, lambda_away),
        )

        value_bets = self._detect_value_bets(
            result_1x2, result_ou,
            odds_home, odds_draw, odds_away, odds_over, odds_under,
            edge_threshold,
        )

        return FullPoissonAnalysis(
            result_1x2=result_1x2,
            result_ou=result_ou,
            value_bets=value_bets,
        )
