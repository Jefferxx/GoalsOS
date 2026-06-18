"use client";

import { useState, useEffect } from "react";
import { useSession } from "next-auth/react";
import { useRouter } from "next/navigation";
import { calculateKellyStake, isValueBet } from "@/utils/kelly";
import { apiFetch } from "@/lib/api";
import { toast } from "sonner";
import { Sparkles, Gem, AlertTriangle, CheckCircle2, ArrowRight } from "lucide-react";

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
        // Llamadas paralelas: Verificar apuesta Y obtener saldo actual
        const [resBet, resWallet] = await Promise.all([
            apiFetch(`/bets/check/${matchApiId}/${session?.user?.email}`),
            apiFetch(`/wallet/${session?.user?.email}`)
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
      const res = await apiFetch(`/bets/`, {
        method: "POST",
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
        toast.success("¡Apuesta registrada exitosamente!", { description: `Has invertido $${stake} en ${selection}` });
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

  if (checking) return <div className="text-xs text-zinc-500 animate-pulse mt-4">Sincronizando billetera...</div>;

  // Si ya apostó, mostramos el recibo
  if (existingBet) {
    return (
      <div className="mt-4 p-3 border border-zinc-800 rounded-lg text-center">
        <p className="text-emerald-500 font-bold text-[10px] uppercase tracking-widest mb-1 flex items-center justify-center gap-1">
            <CheckCircle2 size={11} /> Inversión Activa
        </p>
        <div className="text-sm text-zinc-200 flex items-center justify-center gap-1.5">
            <span className="font-mono font-bold text-emerald-500">${existingBet.stake}</span>
            <ArrowRight size={12} className="text-zinc-600" />
            <span className="italic text-zinc-400">&quot;{existingBet.selection}&quot;</span>
        </div>
      </div>
    );
  }

  return (
    <div className="mt-4 p-4 border border-zinc-800 rounded-xl">

      {/* SUGERENCIA DE LA IA (KELLY) */}
      {suggestion && suggestion.amount > 0 ? (
        <div className="mb-4 flex items-center justify-between border border-zinc-800 p-3 rounded-lg">
            <div className="flex flex-col">
                <span className="text-[9px] text-zinc-500 font-bold uppercase tracking-widest mb-0.5 flex items-center gap-1">
                    <Sparkles size={10} /> Sugerencia Kelly (15%)
                </span>
                <div className="flex items-center gap-2">
                    <span className="text-xs text-zinc-400">
                        Prob. IA: <span className="text-zinc-50 font-bold">{(aiProbability * 100).toFixed(0)}%</span>
                    </span>
                    {suggestion.isValue && (
                        <span className="text-[8px] text-emerald-500 uppercase font-bold flex items-center gap-1">
                            <Gem size={9} /> Value Bet
                        </span>
                    )}
                </div>
            </div>
            <div className="text-right">
                <span className="block text-xl font-mono font-bold text-emerald-500 tracking-tight">
                    ${suggestion.amount}
                </span>
            </div>
        </div>
      ) : (
        <div className="mb-4 p-2 text-center border border-dashed border-zinc-800 rounded-lg">
             <span className="text-[10px] text-zinc-500 uppercase tracking-widest flex items-center justify-center gap-1.5">
                {aiProbability > 0 ? (<><AlertTriangle size={11} className="text-red-600" /> Riesgo alto: No apostar (EV-)</>) : "Esperando análisis..."}
             </span>
        </div>
      )}

      {/* INPUT Y BOTÓN */}
      <div className="flex items-end gap-3">
        <div className="flex-1">
          <label className="block text-[10px] text-zinc-500 uppercase font-bold mb-1.5">Tu Inversión</label>
          <div className="relative group">
              <span className="absolute left-3 top-1/2 -translate-y-1/2 text-zinc-500 font-mono group-focus-within:text-emerald-500 transition-colors">$</span>
              <input
                type="number"
                value={stake}
                onChange={(e) => setStake(Number(e.target.value))}
                className="w-full bg-transparent border border-zinc-800 rounded-lg py-2.5 pl-7 pr-3 text-zinc-50 text-sm font-mono font-bold focus:border-emerald-500 outline-none transition-colors placeholder-zinc-700"
                placeholder="0.00"
              />
          </div>
        </div>

        <button
          onClick={handleBet}
          disabled={loading || stake <= 0}
          className={`h-[42px] px-6 rounded-lg font-bold text-sm transition-colors flex items-center gap-2 cursor-pointer ${
            loading
              ? "bg-zinc-800 text-zinc-500 cursor-not-allowed"
              : "bg-emerald-600 hover:bg-emerald-500 text-zinc-950"
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
          <span className="text-[10px] text-zinc-500">Saldo Disponible:</span>
          <span className={`text-[10px] font-mono font-bold ${bankroll < stake ? "text-red-600" : "text-zinc-300"}`}>
            ${bankroll.toFixed(2)}
          </span>
      </div>
    </div>
  );
}