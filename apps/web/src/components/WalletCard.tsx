"use client";

import { useState, useEffect } from "react";
import { useSession } from "next-auth/react";

export default function WalletCard() {
  const { data: session } = useSession();
  const [balance, setBalance] = useState<number | null>(null);
  const [isEditing, setIsEditing] = useState(false);
  const [newBalance, setNewBalance] = useState("");

  // Cargar saldo al iniciar
  useEffect(() => {
    if (session?.user?.email) {
        fetchBalance();
    }
  }, [session]);

  const fetchBalance = async () => {
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
    try {
        const res = await fetch(`${apiUrl}/wallet/${session?.user?.email}`);
        if (res.ok) {
            const data = await res.json();
            setBalance(data.bankroll);
        }
    } catch (e) {
        console.error("Error cargando wallet", e);
    }
  };

  const handleSync = async () => {
    const amount = parseFloat(newBalance);
    if (isNaN(amount)) return;

    const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
    try {
        const res = await fetch(`${apiUrl}/wallet/sync`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                user_email: session?.user?.email,
                new_balance: amount
            })
        });
        
        if (res.ok) {
            setBalance(amount);
            setIsEditing(false);
            alert("✅ Banca sincronizada con Betano");
        }
    } catch (e) {
        alert("Error al sincronizar");
    }
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 flex flex-col justify-between relative overflow-hidden group">
      {/* Decoración de fondo */}
      <div className="absolute -right-6 -top-6 w-24 h-24 bg-emerald-500/10 rounded-full blur-2xl group-hover:bg-emerald-500/20 transition-all"></div>

      <div>
        <h3 className="text-slate-400 text-xs font-bold uppercase tracking-wider mb-1">Mi Banca Real (Betano)</h3>
        
        {isEditing ? (
            <div className="flex gap-2 mt-2">
                <input 
                    type="number" 
                    value={newBalance}
                    onChange={(e) => setNewBalance(e.target.value)}
                    placeholder={balance?.toString()}
                    className="w-full bg-slate-950 border border-slate-700 rounded p-2 text-white focus:border-emerald-500 outline-none"
                    autoFocus
                />
                <button onClick={handleSync} className="bg-emerald-600 px-3 rounded text-white text-sm">💾</button>
                <button onClick={() => setIsEditing(false)} className="bg-slate-700 px-3 rounded text-white text-sm">✕</button>
            </div>
        ) : (
            <div className="flex items-end gap-3 mt-1">
                <span className="text-3xl font-black text-white tracking-tight">
                    ${balance !== null ? balance.toLocaleString() : "..."}
                </span>
                <button 
                    onClick={() => setIsEditing(true)}
                    className="text-xs text-slate-500 hover:text-emerald-400 underline mb-1.5 transition-colors"
                >
                    Sincronizar
                </button>
            </div>
        )}
      </div>

      <div className="mt-4 pt-4 border-t border-slate-800 flex justify-between items-center">
        <span className="text-xs text-slate-500">ROI Actual</span>
        <span className="text-sm font-bold text-emerald-400">+0.0%</span> {/* Placeholder para Fase 9 */}
      </div>
    </div>
  );
}