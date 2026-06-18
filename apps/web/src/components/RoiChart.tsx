"use client";

import { useEffect, useState } from "react";
import { useSession } from "next-auth/react";
import { apiFetch } from "@/lib/api";
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";

// Interfaz exacta de lo que manda tu backend
interface RoiStats {
  roi_percent: number;
  net_profit: number;
  wins: number;
  losses: number;
  total_bets: number;
  total_invested: number;
  strike_rate: number;
}

// Valores por defecto para evitar errores de undefined
const DEFAULT_STATS: RoiStats = {
    roi_percent: 0,
    net_profit: 0,
    wins: 0,
    losses: 0,
    total_bets: 0,
    total_invested: 0,
    strike_rate: 0
};

export default function RoiChart() {
  const { data: session } = useSession();
  const [stats, setStats] = useState<RoiStats>(DEFAULT_STATS);
  const [chartData, setChartData] = useState<any[]>([]);
  const [currentBankroll, setCurrentBankroll] = useState(0);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (session?.user?.email) {
      fetchData();
    }
  }, [session]);

  const fetchData = async () => {
    try {
      // 1. Obtener Stats (Puede fallar si es usuario nuevo)
      let statsData = DEFAULT_STATS;
      try {
          const resStats = await apiFetch(`/wallet/stats/roi/${session?.user?.email}`);
          if (resStats.ok) {
              statsData = await resStats.json();
          }
      } catch (e) { console.warn("No stats found yet"); }

      // 2. Obtener Wallet (Siempre debería existir si el usuario existe)
      let walletData = { bankroll: 0 };
      try {
          const resWallet = await apiFetch(`/wallet/${session?.user?.email}`);
          if (resWallet.ok) {
              walletData = await resWallet.json();
          }
      } catch (e) { console.error("Wallet fetch error", e); }
      
      setStats(statsData);
      setCurrentBankroll(Number(walletData.bankroll));

      // Reconstrucción de historia para la gráfica
      const currentBalance = Number(walletData.bankroll);
      const profit = Number(statsData.net_profit) || 0;
      const startBalance = currentBalance - profit;

      setChartData([
        { name: "Inicio", balance: startBalance },
        { name: "Actual", balance: currentBalance },
      ]);

    } catch (error) {
      console.error("Error general cargando datos financieros:", error);
    } finally {
      setLoading(false);
    }
  };

  // --- FUNCIÓN PARA SINCRONIZAR MANUALMENTE ---
  const handleManualSync = async () => {
    const newBalanceStr = window.prompt("Ingresa tu saldo real actual en Betano (Ej: 4.90):", currentBankroll.toString());
    
    if (!newBalanceStr) return;

    const newBalance = parseFloat(newBalanceStr);
    if (isNaN(newBalance)) {
        alert("Por favor ingresa un número válido.");
        return;
    }

    try {
        const res = await apiFetch(`/wallet/sync`, {
            method: "POST",
            body: JSON.stringify({
                user_email: session?.user?.email,
                new_balance: newBalance
            })
        });

        if (res.ok) {
            await fetchData(); // Recargar datos
            alert("✅ Saldo sincronizado correctamente.");
        } else {
            alert("❌ Error al guardar el saldo.");
        }
    } catch (e) {
        console.error(e);
        alert("Error de conexión con el servidor.");
    }
  };

  if (loading) return (
    <div className="h-full min-h-[300px] bg-slate-900 border border-slate-800 rounded-2xl p-6 animate-pulse flex flex-col justify-between">
      <div className="space-y-4">
        <div className="h-4 w-32 bg-slate-800 rounded"></div>
        <div className="h-12 w-48 bg-slate-800 rounded"></div>
      </div>
      <div className="h-24 w-full bg-slate-800/30 rounded-lg mt-4"></div>
    </div>
  );

  const safeStats = stats || DEFAULT_STATS;
  const isPositive = safeStats.net_profit >= 0;
  
  const colorHex = isPositive ? "#10b981" : "#ef4444"; 
  const txtColor = isPositive ? "text-emerald-400" : "text-rose-500";
  const bgGradient = isPositive 
    ? "bg-[radial-gradient(ellipse_at_top_right,_var(--tw-gradient-stops))] from-emerald-900/20 via-slate-900 to-slate-900"
    : "bg-[radial-gradient(ellipse_at_top_right,_var(--tw-gradient-stops))] from-rose-900/20 via-slate-900 to-slate-900";
  const borderColor = isPositive ? "border-emerald-500/30" : "border-rose-500/30";

  return (
    <div className={`relative h-full min-h-[300px] w-full border ${borderColor} rounded-2xl overflow-hidden flex flex-col shadow-2xl ${bgGradient}`}>
      
      {/* 1. HEADER */}
      <div className="relative z-20 px-6 pt-6 pb-2 flex flex-col sm:flex-row justify-between items-start sm:items-end gap-4">
        <div>
            <h3 className="text-slate-400 text-[10px] font-bold uppercase tracking-widest mb-1 flex items-center gap-2">
              Mi Banca Real
              <button 
                onClick={handleManualSync}
                className="text-[9px] bg-slate-800 hover:bg-slate-700 text-slate-300 px-1.5 py-0.5 rounded border border-slate-700 transition-colors cursor-pointer"
                title="Ajustar saldo manualmente"
              >
                ✎ Ajustar
              </button>
            </h3>
            <div className="flex items-baseline gap-2">
                <span className="text-4xl font-mono font-bold text-white tracking-tight">
                    ${currentBankroll.toFixed(2)}
                </span>
                <span className="text-sm text-slate-500 font-bold">USD</span>
            </div>
        </div>

        <div className="text-right">
             <div className={`flex items-center justify-end gap-2 ${txtColor}`}>
                <span className="text-3xl font-black tracking-tighter">
                    {/* PROTECCIÓN CONTRA NULOS: Usamos ?? 0 */}
                    {(safeStats.roi_percent ?? 0) > 0 ? "+" : ""}{(safeStats.roi_percent ?? 0).toFixed(1)}%
                </span>
                <span className="text-[10px] font-bold uppercase bg-slate-950/50 px-1.5 py-0.5 rounded border border-white/5">ROI</span>
             </div>
             <p className={`text-xs font-mono font-medium mt-1 ${isPositive ? 'text-emerald-300' : 'text-rose-300'}`}>
                {safeStats.net_profit > 0 ? "+" : ""}${safeStats.net_profit} Profit
             </p>
        </div>
      </div>

      {/* 2. CHART */}
      <div className="flex-1 w-full relative min-h-[140px] mt-2">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={chartData} margin={{ top: 10, right: 0, left: 0, bottom: 0 }}>
            <defs>
              <linearGradient id="chartGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor={colorHex} stopOpacity={0.3} />
                <stop offset="100%" stopColor={colorHex} stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.03)" vertical={false} />
            <XAxis dataKey="name" hide />
            <YAxis hide domain={['auto', 'auto']} />
            <Tooltip 
              cursor={{ stroke: 'rgba(255,255,255,0.1)', strokeWidth: 1 }}
              contentStyle={{ backgroundColor: "#020617", borderColor: "#1e293b", borderRadius: '8px' }}
              itemStyle={{ color: colorHex }}
              formatter={(value: number) => [`$${value.toFixed(2)}`, "Saldo"]}
            />
            <Area
              type="monotone"
              dataKey="balance"
              stroke={colorHex}
              strokeWidth={3}
              fill="url(#chartGradient)"
              animationDuration={1500}
              dot={{ r: 4, fill: colorHex, strokeWidth: 2, stroke: '#0f172a' }} 
              activeDot={{ r: 6, strokeWidth: 0 }}
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>

      {/* 3. FOOTER */}
      <div className="relative z-20 bg-slate-950/40 backdrop-blur-md border-t border-white/5 p-3">
        <div className="flex justify-around text-center divide-x divide-white/5">
            <div className="w-full">
                <p className="text-[9px] text-slate-500 uppercase font-black tracking-widest">Ganadas</p>
                <p className="text-lg font-bold text-emerald-400">{safeStats.wins}</p>
            </div>
            <div className="w-full">
                <p className="text-[9px] text-slate-500 uppercase font-black tracking-widest">Perdidas</p>
                <p className="text-lg font-bold text-rose-400">{safeStats.losses}</p>
            </div>
            <div className="w-full">
                <p className="text-[9px] text-slate-500 uppercase font-black tracking-widest">Efectividad</p>
                <p className="text-lg font-bold text-blue-400">{safeStats.strike_rate}%</p>
            </div>
        </div>
      </div>
    </div>
  );
}