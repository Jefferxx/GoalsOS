"use client";

import { useState } from "react";
import { Target, RotateCcw } from "lucide-react";
import { apiFetch } from "@/lib/api";

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
      // Pedimos un parley de 3 picks con confianza > 70%
      const res = await apiFetch(`/bets/parley/generate?limit=3&min_confidence=70`);
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
      <div className="border border-zinc-800 p-6 rounded-xl text-center">
        <h3 className="text-zinc-200 font-bold mb-2 flex items-center justify-center gap-2">
          <Target size={16} className="text-emerald-500" /> Parley de Alta Probabilidad
        </h3>
        <p className="text-xs text-zinc-500 mb-4">
          Combina los 3 picks más seguros del día analizados por la IA.
        </p>
        <button
          onClick={generateParley}
          disabled={loading}
          className="bg-emerald-600 hover:bg-emerald-500 text-zinc-950 px-6 py-2 rounded-full font-bold text-sm transition-colors flex items-center gap-2 mx-auto disabled:opacity-50 cursor-pointer"
        >
          {loading ? "Analizando..." : "Generar Parley del Día"}
        </button>
      </div>
    );
  }

  // Estado con Resultados
  return (
    <div className="border border-zinc-800 p-5 rounded-xl">
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-zinc-200 font-bold text-sm uppercase tracking-wider flex items-center gap-2">
          <Target size={14} className="text-emerald-500" /> Parley Sugerido
        </h3>
        <button
            onClick={() => setPicks(null)}
            className="flex items-center gap-1 text-zinc-500 hover:text-zinc-200 text-xs cursor-pointer"
        >
            <RotateCcw size={12} /> Reset
        </button>
      </div>

      <div className="space-y-2">
        {picks.length === 0 ? (
            <p className="text-zinc-600 text-sm text-center py-4">
                No hay suficientes partidos analizados con alta confianza hoy.
            </p>
        ) : (
            picks.map((pick, i) => (
            <div key={i} className="border border-zinc-800 p-3 rounded flex justify-between items-center">
                <div>
                <div className="text-xs text-zinc-500 mb-1">{pick.match}</div>
                <div className="text-zinc-50 font-bold text-sm">{pick.selection}</div>
                </div>
                <div className="text-right">
                <span className="text-emerald-500 text-xs font-mono">
                    {pick.confidence}%
                </span>
                </div>
            </div>
            ))
        )}
      </div>

      {picks.length > 0 && (
        <div className="mt-4 pt-3 border-t border-zinc-800 text-center">
            <p className="text-xs text-zinc-600">Copia estos picks en Betano</p>
        </div>
      )}
    </div>
  );
}
