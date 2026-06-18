"use client";

import Link from "next/link";
import UserMenu from "@/components/UserMenu";
import { useSession } from "next-auth/react";
import { useEffect, useState } from "react";
import { apiFetch } from "@/lib/api";
import { ArrowLeft, Inbox, CheckCircle2, XCircle, Clock } from "lucide-react";

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
      // Usamos el nuevo endpoint que hace el JOIN
      const res = await apiFetch(`/wallet/history/${session?.user?.email}`);
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
    <main className="min-h-screen bg-zinc-950 text-zinc-200 p-8 font-sans">
      <header className="mb-8 flex justify-between items-center">
        <div>
            <Link href="/" className="text-sm text-zinc-500 hover:text-zinc-200 mb-2 flex items-center gap-1.5 group transition-colors">
                <ArrowLeft size={14} className="group-hover:-translate-x-1 transition-transform" /> Volver al Dashboard
            </Link>
            <h1 className="text-2xl font-bold text-zinc-50">Historial de Operaciones</h1>
        </div>
        <UserMenu />
      </header>

      <section>
        <div className="border border-zinc-800 rounded-xl overflow-hidden">
            <div className="overflow-x-auto">
                <table className="w-full text-left border-collapse">
                    <thead>
                        <tr className="text-zinc-500 text-[10px] uppercase tracking-widest border-b border-zinc-800">
                            <th className="p-4 font-bold">Fecha</th>
                            <th className="p-4 font-bold">Evento</th>
                            <th className="p-4 font-bold">Tu Selección (Pick)</th>
                            <th className="p-4 font-bold text-center">Cuota</th>
                            <th className="p-4 font-bold text-center">Inversión</th>
                            <th className="p-4 font-bold text-center">Estado</th>
                            <th className="p-4 font-bold text-right">P/L</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-zinc-800 text-sm">
                        {loading ? (
                            <tr><td colSpan={7} className="p-8 text-center text-zinc-500 animate-pulse">Cargando operaciones...</td></tr>
                        ) : history.length === 0 ? (
                            <tr>
                                <td colSpan={7} className="p-12 text-center text-zinc-500">
                                    <Inbox size={24} className="mx-auto mb-2 text-zinc-700" />
                                    No hay apuestas registradas aún.
                                </td>
                            </tr>
                        ) : (
                            history.map((item) => (
                                <tr key={item.bet_id} className="hover:bg-zinc-900/50 transition-colors group">
                                    {/* Fecha y Liga */}
                                    <td className="p-4">
                                        <div className="text-zinc-300 font-medium">
                                            {new Date(item.date).toLocaleDateString()}
                                        </div>
                                        <div className="text-[10px] text-zinc-600 uppercase font-bold mt-1">
                                            {item.league}
                                        </div>
                                    </td>

                                    {/* Partido y Marcador */}
                                    <td className="p-4">
                                        <div className="text-zinc-50 font-bold">
                                            {item.match}
                                        </div>
                                        <div className="text-xs text-zinc-500 mt-1 font-mono">
                                            Marcador Final: <span className="text-zinc-300">{item.score || "-"}</span>
                                        </div>
                                    </td>

                                    {/* Selección */}
                                    <td className="p-4">
                                        <span className="text-zinc-300 text-xs font-mono border border-zinc-800 px-2 py-1 rounded">
                                            {item.selection}
                                        </span>
                                    </td>

                                    {/* Cuota */}
                                    <td className="p-4 text-center font-mono text-zinc-400">
                                        {item.odds.toFixed(2)}
                                    </td>

                                    {/* Stake */}
                                    <td className="p-4 text-center font-mono text-zinc-300">
                                        ${item.stake.toFixed(2)}
                                    </td>

                                    {/* Estado (Badge con Tooltip) */}
                                    <td className="p-4 text-center">
                                        <div className="relative group/tooltip inline-block cursor-help">
                                            {item.status === 'WON' && (
                                                <span className="inline-flex items-center gap-1 text-xs font-medium text-emerald-500">
                                                    <CheckCircle2 size={12} /> GANADA
                                                </span>
                                            )}
                                            {item.status === 'LOST' && (
                                                <span className="inline-flex items-center gap-1 text-xs font-medium text-red-600">
                                                    <XCircle size={12} /> PERDIDA
                                                </span>
                                            )}
                                            {item.status === 'PENDING' && (
                                                <span className="inline-flex items-center gap-1 text-xs font-medium text-zinc-500">
                                                    <Clock size={12} /> PENDIENTE
                                                </span>
                                            )}

                                            {/* TOOLTIP: Solo si hay razón y no está pendiente */}
                                            {item.audit_reason && (
                                                <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 w-64 p-3 bg-zinc-900 border border-zinc-800 rounded-lg text-xs text-zinc-300 opacity-0 group-hover/tooltip:opacity-100 transition-opacity pointer-events-none z-50 text-left leading-relaxed">
                                                    <div className="font-bold mb-1 text-zinc-500 uppercase text-[10px]">Auditoría:</div>
                                                    {item.audit_reason}
                                                </div>
                                            )}
                                        </div>
                                    </td>

                                    {/* Profit/Loss */}
                                    <td className={`p-4 text-right font-mono font-bold ${item.profit >= 0 ? (item.status === 'PENDING' ? 'text-zinc-500' : 'text-emerald-500') : 'text-red-600'}`}>
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
