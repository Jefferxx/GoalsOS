"use client";

import Link from "next/link";
import UserMenu from "@/components/UserMenu";
import { useSession } from "next-auth/react";
import { useEffect, useState } from "react";

// Interfaz actualizada con audit_reason
interface HistoryItem {
  bet_id: number;
  date: string;
  league: string;
  match: string;
  selection: string;
  odds: number;
  stake: number;
  status: string;
  score: string;
  profit: number;
  audit_reason?: string; // <--- Nuevo campo opcional
}

export default function HistoryPage() {
  const { data: session } = useSession();
  const [history, setHistory] = useState<HistoryItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (session?.user?.email) {
      fetchHistory();
    }
  }, [session]);

  const fetchHistory = async () => {
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      // Usamos el nuevo endpoint que hace el JOIN
      const res = await fetch(`${apiUrl}/wallet/history/${session?.user?.email}`);
      if (res.ok) {
        const data = await res.json();
        setHistory(data);
      }
    } catch (error) {
      console.error("Error fetching history:", error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="min-h-screen bg-slate-950 text-slate-100 p-8 font-sans">
      <header className="mb-8 flex justify-between items-center">
        <div>
            <Link href="/" className="text-sm text-emerald-400 hover:text-emerald-300 mb-2 flex items-center gap-1 group">
                <span className="group-hover:-translate-x-1 transition-transform">←</span> Volver al Dashboard
            </Link>
            <h1 className="text-3xl font-bold text-white">Historial de Operaciones</h1>
        </div>
        <UserMenu />
      </header>

      <section>
        <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-2xl">
            <div className="overflow-x-auto">
                <table className="w-full text-left border-collapse">
                    <thead>
                        <tr className="bg-slate-950/50 text-slate-400 text-[10px] uppercase tracking-wider border-b border-slate-800">
                            <th className="p-4 font-bold">Fecha</th>
                            <th className="p-4 font-bold">Evento</th>
                            <th className="p-4 font-bold">Tu Selección (Pick)</th>
                            <th className="p-4 font-bold text-center">Cuota</th>
                            <th className="p-4 font-bold text-center">Inversión</th>
                            <th className="p-4 font-bold text-center">Estado</th>
                            <th className="p-4 font-bold text-right">P/L</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800 text-sm">
                        {loading ? (
                            <tr><td colSpan={7} className="p-8 text-center text-slate-500 animate-pulse">Cargando operaciones...</td></tr>
                        ) : history.length === 0 ? (
                            <tr>
                                <td colSpan={7} className="p-12 text-center text-slate-500 flex flex-col items-center">
                                    <span className="text-2xl mb-2">📭</span>
                                    No hay apuestas registradas aún.
                                </td>
                            </tr>
                        ) : (
                            history.map((item) => (
                                <tr key={item.bet_id} className="hover:bg-slate-800/30 transition-colors group">
                                    {/* Fecha y Liga */}
                                    <td className="p-4">
                                        <div className="text-slate-300 font-medium">
                                            {new Date(item.date).toLocaleDateString()}
                                        </div>
                                        <div className="text-[10px] text-slate-500 uppercase font-bold mt-1">
                                            {item.league}
                                        </div>
                                    </td>
                                    
                                    {/* Partido y Marcador */}
                                    <td className="p-4">
                                        <div className="text-white font-bold group-hover:text-emerald-300 transition-colors">
                                            {item.match}
                                        </div>
                                        <div className="text-xs text-slate-500 mt-1 font-mono">
                                            Marcador Final: <span className="text-slate-300">{item.score || "-"}</span>
                                        </div>
                                    </td>

                                    {/* Selección */}
                                    <td className="p-4">
                                        <span className="bg-slate-800/50 text-slate-300 px-2 py-1 rounded text-xs border border-slate-700 font-mono">
                                            {item.selection}
                                        </span>
                                    </td>

                                    {/* Cuota */}
                                    <td className="p-4 text-center font-mono text-slate-400">
                                        {item.odds.toFixed(2)}
                                    </td>

                                    {/* Stake */}
                                    <td className="p-4 text-center font-mono text-slate-300">
                                        ${item.stake.toFixed(2)}
                                    </td>

                                    {/* Estado (Badge con Tooltip) */}
                                    <td className="p-4 text-center">
                                        <div className="relative group/tooltip inline-block cursor-help">
                                            {item.status === 'WON' && (
                                                <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                                                    ✅ GANADA
                                                </span>
                                            )}
                                            {item.status === 'LOST' && (
                                                <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-rose-500/10 text-rose-400 border border-rose-500/20">
                                                    ❌ PERDIDA
                                                </span>
                                            )}
                                            {item.status === 'PENDING' && (
                                                <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-yellow-500/10 text-yellow-400 border border-yellow-500/20">
                                                    ⏳ PENDIENTE
                                                </span>
                                            )}

                                            {/* TOOLTIP: Solo si hay razón y no está pendiente */}
                                            {item.audit_reason && (
                                                <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 w-64 p-3 bg-slate-800 border border-slate-600 rounded-lg shadow-2xl text-xs text-slate-200 opacity-0 group-hover/tooltip:opacity-100 transition-opacity pointer-events-none z-50 text-left leading-relaxed">
                                                    <div className="font-bold mb-1 text-slate-400 uppercase text-[10px]">Auditoría del Juez:</div>
                                                    {item.audit_reason}
                                                    {/* Flechita abajo */}
                                                    <div className="absolute top-full left-1/2 -translate-x-1/2 border-4 border-transparent border-t-slate-600"></div>
                                                </div>
                                            )}
                                        </div>
                                    </td>

                                    {/* Profit/Loss */}
                                    <td className={`p-4 text-right font-mono font-bold ${item.profit >= 0 ? (item.status === 'PENDING' ? 'text-slate-500' : 'text-emerald-400') : 'text-rose-400'}`}>
                                        {item.status === 'PENDING' ? '--' : (
                                            <>
                                                {item.profit > 0 ? "+" : ""}{item.profit.toFixed(2)} USD
                                            </>
                                        )}
                                    </td>
                                </tr>
                            ))
                        )}
                    </tbody>
                </table>
            </div>
        </div>
      </section>
    </main>
  );
}