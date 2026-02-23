/**
 * 🧠 CEREBRO FINANCIERO: Criterio de Kelly Fraccional
 * * Calcula el tamaño óptimo de la apuesta para maximizar el crecimiento geométrico
 * de la banca, minimizando el riesgo de ruina.
 */

export function calculateKellyStake(
  bankroll: number,
  odds: number,
  winProbability: number, // 0.0 a 1.0 (Ej: 0.65 para 65%)
  fraction: number = 0.15 // 🛡️ MODO SEGURO: Usamos solo el 15% de lo que recomienda Kelly puro
): number {
  // 1. Validaciones de seguridad
  if (odds <= 1 || winProbability <= 0 || bankroll <= 0) return 0;

  // 2. Fórmula de Kelly: f* = (bp - q) / b
  const b = odds - 1; // Ganancia neta (Ej: Cuota 2.0 -> b=1.0)
  const p = winProbability;
  const q = 1 - p; // Probabilidad de perder

  const f = (b * p - q) / b;

  // 3. Si f es negativo, la apuesta tiene Valor Esperado Negativo (EV-). NO APOSTAR.
  if (f <= 0) return 0;

  // 4. Aplicamos el factor de seguridad (Kelly Fraccional)
  let suggestedStake = bankroll * f * fraction;

  // 5. 🔒 STOP LOSS DURO: Nunca arriesgar más del 5% del bankroll en una sola ficha
  // Esto protege contra errores de la IA o "Alucinaciones"
  const MAX_STAKE_PERCENT = 0.05; 
  const maxSafeStake = bankroll * MAX_STAKE_PERCENT;

  // Elegimos el menor entre la sugerencia matemática y el límite de seguridad
  const finalStake = Math.min(suggestedStake, maxSafeStake);

  // Redondear a 2 decimales hacia abajo para no pasarse
  return Math.floor(finalStake * 100) / 100;
}

/**
 * Detecta si una apuesta es una "Value Bet" (La casa paga más de lo que debería)
 * True si: Probabilidad IA > Probabilidad Implícita de la Cuota
 */
export function isValueBet(odds: number, winProbability: number): boolean {
  if (odds <= 0) return false;
  const impliedProbability = 1 / odds;
  // Margen de seguridad del 2% para filtrar falsos positivos
  return winProbability > (impliedProbability + 0.02); 
}