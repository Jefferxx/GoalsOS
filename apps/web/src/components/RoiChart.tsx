"use client";

import { useEffect, useState } from "react";
import { useSession } from "next-auth/react";
import { apiFetch } from "@/lib/api";
import { Pencil } from "lucide-react";
import { toast } from "sonner";
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
        toast.warning("Por favor ingresa un número válido.");
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
            toast.success("Saldo sincronizado correctamente.");
        } else {
            toast.error("Error al guardar el saldo.");
        }
    } catch (e) {
        console.error(e);
        toast.error("Error de conexión con el servidor.");
    }
  };

  if (loading) return (
    <div className="h-full min-h-[300px] border border-zinc-800 rounded-xl p-6 animate-pulse flex flex-col justify-between">
      <div className="space-y-4">
        <div className="h-4 w-32 bg-zinc-800 rounded"></div>
        <div className="h-12 w-48 bg-zinc-800 rounded"></div>
      </div>
      <div className="h-24 w-full bg-zinc-800/30 rounded-lg mt-4"></div>
    </div>
  );

  const safeStats = stats || DEFAULT_STATS;
  const isPositive = safeStats.net_profit >= 0;

  const colorHex = isPositive ? "#10b981" : "#dc2626";
  const txtColor = isPositive ? "text-emerald-500" : "text-red-600";

  return (
    <div className="relative h-full min-h-[300px] w-full border border-zinc-800 rounded-xl overflow-hidden flex flex-col">

      {/* 1. HEADER */}
      <div className="relative z-20 px-6 pt-6 pb-2 flex flex-col sm:flex-row justify-between items-start sm:items-end gap-4">
        <div>
            <h3 className="text-zinc-500 text-[10px] font-bold uppercase tracking-widest mb-1 flex items-center gap-2">
              Mi Banca Real
              <button
                onClick={handleManualSync}
                className="flex items-center gap-1 text-[9px] text-zinc-500 hover:text-zinc-200 transition-colors cursor-pointer"
                title="Ajustar saldo manualmente"
              >
                <Pencil size={10} /> Ajustar
              </button>
            </h3>
            <div className="flex items-baseline gap-2">
                <span className="text-4xl font-mono font-bold text-zinc-50 tracking-tight">
                    ${currentBankroll.toFixed(2)}
                </span>
                <span className="text-sm text-zinc-600 font-bold">USD</span>
            </div>
        </div>

        <div className="text-right">
             <div className={`flex items-center justify-end gap-2 ${txtColor}`}>
                <span className="text-3xl font-bold tracking-tighter">
                    {/* PROTECCIÓN CONTRA NULOS: Usamos ?? 0 */}
                    {(safeStats.roi_percent ?? 0) > 0 ? "+" : ""}{(safeStats.roi_percent ?? 0).toFixed(1)}%
                </span>
                <span className="text-[10px] font-bold uppercase text-zinc-600">ROI</span>
             </div>
             <p className={`text-xs font-mono font-medium mt-1 ${txtColor}`}>
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
                <stop offset="0%" stopColor={colorHex} stopOpacity={0.25} />
                <stop offset="100%" stopColor={colorHex} stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.03)" vertical={false} />
            <XAxis dataKey="name" hide />
            <YAxis hide domain={['auto', 'auto']} />
            <Tooltip
              cursor={{ stroke: 'rgba(255,255,255,0.1)', strokeWidth: 1 }}
              contentStyle={{ backgroundColor: "#09090b", borderColor: "#27272a", borderRadius: '8px' }}
              itemStyle={{ color: colorHex }}
              formatter={(value: number) => [`$${value.toFixed(2)}`, "Saldo"]}
            />
            <Area
              type="monotone"
              dataKey="balance"
              stroke={colorHex}
              strokeWidth={2}
              fill="url(#chartGradient)"
              animationDuration={1500}
              dot={{ r: 3, fill: colorHex, strokeWidth: 0 }}
              activeDot={{ r: 5, strokeWidth: 0 }}
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>

      {/* 3. FOOTER */}
      <div className="relative z-20 border-t border-zinc-800 p-3">
        <div className="flex justify-around text-center divide-x divide-zinc-800">
            <div className="w-full">
                <p className="text-[9px] text-zinc-600 uppercase font-bold tracking-widest">Ganadas</p>
                <p className="text-lg font-bold text-emerald-500">{safeStats.wins}</p>
            </div>
            <div className="w-full">
                <p className="text-[9px] text-zinc-600 uppercase font-bold tracking-widest">Perdidas</p>
                <p className="text-lg font-bold text-red-600">{safeStats.losses}</p>
            </div>
            <div className="w-full">
                <p className="text-[9px] text-zinc-600 uppercase font-bold tracking-widest">Efectividad</p>
                <p className="text-lg font-bold text-zinc-300">{safeStats.strike_rate}%</p>
            </div>
        </div>
      </div>
    </div>
  );
}
