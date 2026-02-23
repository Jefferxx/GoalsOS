"use client";

import { useState } from "react";

interface ParleyPick {
  match: string;
  selection: string;
  confidence: number;
  reason: string;
}

export default function ParleyGenerator() {
  const [picks, setPicks] = useState<ParleyPick[] | null>(null);
  const [loading, setLoading] = useState(false);

  const generateParley = async () => {
    setLoading(true);
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      // Pedimos un parley de 3 picks con confianza > 70%
      const res = await fetch(`${apiUrl}/bets/parley/generate?limit=3&min_confidence=70`);
      if (res.ok) {
        const data = await res.json();
        setPicks(data.picks);
      }
    } catch (error) {
      console.error("Error generando parley", error);
    } finally {
      setLoading(false);
    }
  };

  // Estado Inicial (Botón)
  if (!picks) {
    return (
      <div className="bg-gradient-to-r from-violet-900/50 to-fuchsia-900/50 border border-violet-500/30 p-6 rounded-xl text-center">
        <h3 className="text-violet-200 font-bold mb-2">🚀 Parley de Alta Probabilidad</h3>
        <p className="text-xs text-violet-300/70 mb-4">
          Combina los 3 picks más seguros del día analizados por la IA.
        </p>
        <button 
          onClick={generateParley}
          disabled={loading}
          className="bg-violet-600 hover:bg-violet-500 text-white px-6 py-2 rounded-full font-bold text-sm transition-all shadow-lg shadow-violet-900/50 flex items-center gap-2 mx-auto disabled:opacity-50"
        >
          {loading ? "Analizando..." : "🔮 Generar Parley del Día"}
        </button>
      </div>
    );
  }

  // Estado con Resultados
  return (
    <div className="bg-slate-900 border border-violet-500/50 p-5 rounded-xl relative overflow-hidden">
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-violet-400 font-bold text-sm uppercase tracking-wider">🎯 Parley Sugerido</h3>
        <button 
            onClick={() => setPicks(null)}
            className="text-slate-500 hover:text-white text-xs"
        >
            ↻ Reset
        </button>
      </div>

      <div className="space-y-3">
        {picks.length === 0 ? (
            <p className="text-slate-500 text-sm text-center py-4">
                No hay suficientes partidos analizados con alta confianza hoy.
            </p>
        ) : (
            picks.map((pick, i) => (
            <div key={i} className="bg-slate-950/50 p-3 rounded border border-slate-800 flex justify-between items-center">
                <div>
                <div className="text-xs text-slate-400 mb-1">{pick.match}</div>
                <div className="text-white font-bold text-sm text-emerald-400">{pick.selection}</div>
                </div>
                <div className="text-right">
                <span className="bg-emerald-900 text-emerald-300 text-xs px-2 py-1 rounded font-mono">
                    {pick.confidence}%
                </span>
                </div>
            </div>
            ))
        )}
      </div>

      {picks.length > 0 && (
        <div className="mt-4 pt-3 border-t border-slate-800 text-center">
            <p className="text-xs text-slate-500 mb-2">Copia estos picks en Betano</p>
            {/* Aquí podríamos sumar las cuotas reales en el futuro */}
        </div>
      )}
    </div>
  );
}