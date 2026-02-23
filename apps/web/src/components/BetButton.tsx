"use client";

import { useState, useEffect } from "react";
import { useSession } from "next-auth/react";
import { useRouter } from "next/navigation";
import { calculateKellyStake, isValueBet } from "@/utils/kelly";
import { toast } from "sonner";

interface BetButtonProps {
  matchApiId: string;
  selection: string;
  odds: number;
  aiProbability?: number; // Nueva Prop: Probabilidad real de la IA
}

export default function BetButton({ matchApiId, selection, odds, aiProbability = 0 }: BetButtonProps) {
  const { data: session } = useSession();
  const [loading, setLoading] = useState(false);
  const [checking, setChecking] = useState(true);
  const [existingBet, setExistingBet] = useState<{selection: string, stake: number} | null>(null);
  
  // Estado para la apuesta y el banco
  const [stake, setStake] = useState(1.00); // Default seguro
  const [bankroll, setBankroll] = useState(0);
  const [suggestion, setSuggestion] = useState<{ amount: number, isValue: boolean } | null>(null);
  
  const router = useRouter();

  // 1. Cargar estado inicial (Saldo y si ya apostó)
  useEffect(() => {
    if (session?.user?.email) {
        checkStatus();
    }
  }, [session, matchApiId]);

  // 2. 🧠 CEREBRO: Calcular sugerencia de Kelly cuando tengamos datos
  useEffect(() => {
    if (bankroll > 0 && aiProbability > 0 && odds > 1) {
        // Calculamos cuánto apostar usando el módulo Kelly
        const suggested = calculateKellyStake(bankroll, odds, aiProbability);
        const hasValue = isValueBet(odds, aiProbability);
        
        setSuggestion({ amount: suggested, isValue: hasValue });
        
        // UX Pro: Si hay una sugerencia válida y positiva, pre-llenamos el input automáticamente
        if (suggested > 0) setStake(suggested);
    }
  }, [bankroll, aiProbability, odds]);

  const checkStatus = async () => {
    try {
        const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
        
        // Llamadas paralelas: Verificar apuesta Y obtener saldo actual
        const [resBet, resWallet] = await Promise.all([
            fetch(`${apiUrl}/bets/check/${matchApiId}/${session?.user?.email}`),
            fetch(`${apiUrl}/wallet/${session?.user?.email}`)
        ]);

        if (resBet.ok) {
            const data = await resBet.json();
            if (data.has_bet) setExistingBet({ selection: data.selection, stake: data.stake });
        }
        
        if (resWallet.ok) {
            const data = await resWallet.json();
            setBankroll(Number(data.bankroll));
        }

    } catch (error) {
        console.error("Error verificando estado:", error);
    } finally {
        setChecking(false);
    }
  };

  const handleBet = async () => {
    // --- VALIDACIONES CON TOAST (UX MEJORADA) ---
    if (!session?.user?.email) {
        toast.error("Acceso denegado", { description: "Debes iniciar sesión para realizar una apuesta." });
        return;
    }
    if (stake <= 0) {
        toast.warning("Monto inválido", { description: "Por favor ingresa una cantidad mayor a $0." });
        return;
    }
    if (stake > bankroll) {
        toast.error("Saldo insuficiente", { description: "No tienes suficientes fondos en tu billetera." });
        return;
    }

    setLoading(true);
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const res = await fetch(`${apiUrl}/bets/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          match_api_id: matchApiId,
          user_email: session.user.email,
          selection: selection,
          odds: odds,
          stake: stake,
          // Guardamos la estrategia para auditar si el usuario siguió a Kelly
          strategy: suggestion?.isValue ? "KELLY_VALUE_V1" : "MANUAL_STAKE" 
        }),
      });

      if (res.ok) {
        setExistingBet({ selection, stake });
        router.refresh(); 
        // Actualizar bankroll visualmente de inmediato
        setBankroll(prev => prev - stake);
        toast.success("🚀 ¡Apuesta registrada exitosamente!", { description: `Has invertido $${stake} en ${selection}` });
      } else {
        const error = await res.json();
        toast.error("Error en la transacción", { description: error.detail || "Intenta nuevamente." });
      }
    } catch (e) {
      toast.error("Error de conexión", { description: "Verifica tu conexión a internet o intenta nuevamente." });
    } finally {
      setLoading(false);
    }
  };

  if (checking) return <div className="text-xs text-slate-500 animate-pulse mt-4">Sincronizando billetera...</div>;

  // Si ya apostó, mostramos el recibo
  if (existingBet) {
    return (
      <div className="mt-4 p-3 bg-emerald-900/20 border border-emerald-500/30 rounded-lg text-center shadow-lg relative overflow-hidden">
        <div className="absolute top-0 left-0 w-1 h-full bg-emerald-500"></div>
        <p className="text-emerald-400 font-bold text-[10px] uppercase tracking-wider mb-1 flex items-center justify-center gap-1">
            <span>✅</span> Inversión Activa
        </p>
        <div className="text-sm text-white">
            <span className="font-mono font-bold text-emerald-300">${existingBet.stake}</span> 
            <span className="text-slate-500 mx-1">➜</span> 
            <span className="italic text-slate-300">"{existingBet.selection}"</span>
        </div>
      </div>
    );
  }

  return (
    <div className="mt-4 p-4 bg-slate-800/60 rounded-xl border border-slate-700/60 backdrop-blur-sm shadow-xl">
      
      {/* 🤖 SUGERENCIA DE LA IA (KELLY) */}
      {suggestion && suggestion.amount > 0 ? (
        <div className="mb-4 flex items-center justify-between bg-blue-950/40 p-3 rounded-lg border border-blue-500/20 relative overflow-hidden transition-all hover:bg-blue-900/30 group">
            <div className="absolute top-0 left-0 w-1 h-full bg-blue-500 shadow-[0_0_10px_rgba(59,130,246,0.5)] group-hover:w-1.5 transition-all"></div>
            <div className="flex flex-col z-10 pl-2">
                <span className="text-[9px] text-blue-300 font-black uppercase tracking-widest mb-0.5 flex items-center gap-1">
                    ✨ Sugerencia Kelly (15%)
                </span>
                <div className="flex items-center gap-2">
                    <span className="text-xs text-slate-300">
                        Prob. IA: <span className="text-white font-bold">{(aiProbability * 100).toFixed(0)}%</span>
                    </span>
                    {suggestion.isValue && (
                        <span className="text-[8px] bg-emerald-500/20 text-emerald-400 px-1.5 py-0.5 rounded border border-emerald-500/20 uppercase font-bold animate-pulse">
                            💎 Value Bet
                        </span>
                    )}
                </div>
            </div>
            <div className="text-right z-10">
                <span className="block text-xl font-mono font-black text-blue-400 tracking-tight drop-shadow-md">
                    ${suggestion.amount}
                </span>
            </div>
        </div>
      ) : (
        <div className="mb-4 p-2 text-center border border-dashed border-slate-700/50 rounded-lg bg-slate-900/30">
             <span className="text-[10px] text-slate-500 uppercase tracking-widest">
                {aiProbability > 0 ? "⚠️ Riesgo alto: No apostar (EV-)" : "Esperando análisis..."}
             </span>
        </div>
      )}

      {/* INPUT Y BOTÓN */}
      <div className="flex items-end gap-3">
        <div className="flex-1">
          <label className="block text-[10px] text-slate-400 uppercase font-bold mb-1.5">Tu Inversión</label>
          <div className="relative group">
              <span className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500 font-mono group-focus-within:text-emerald-500 transition-colors">$</span>
              <input 
                type="number" 
                value={stake}
                onChange={(e) => setStake(Number(e.target.value))}
                className="w-full bg-slate-950 border border-slate-700 rounded-lg py-2.5 pl-7 pr-3 text-white text-sm font-mono font-bold focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 outline-none transition-all placeholder-slate-700 shadow-inner"
                placeholder="0.00"
              />
          </div>
        </div>
        
        <button
          onClick={handleBet}
          disabled={loading || stake <= 0}
          className={`h-[42px] px-6 rounded-lg font-bold text-sm shadow-lg transition-all transform active:scale-95 flex items-center gap-2 border ${
            loading 
              ? "bg-slate-800 border-slate-700 text-slate-500 cursor-not-allowed" 
              : "bg-emerald-600 border-emerald-500 hover:bg-emerald-500 text-white shadow-emerald-900/40 hover:shadow-emerald-900/60"
          }`}
        >
          {loading ? (
            <span className="animate-pulse">Procesando...</span>
          ) : (
            <>
                <span>Apostar</span>
                <span className="bg-black/20 px-1.5 py-0.5 rounded text-[10px] font-mono opacity-90">@{odds.toFixed(2)}</span>
            </>
          )}
        </button>
      </div>
      
      <div className="text-right mt-2 flex justify-end items-center gap-1">
          <span className="text-[10px] text-slate-500">Saldo Disponible:</span>
          <span className={`text-[10px] font-mono font-bold ${bankroll < stake ? "text-red-400" : "text-slate-300"}`}>
            ${bankroll.toFixed(2)}
          </span>
      </div>
    </div>
  );
}