"use client";

import { useState } from "react";

export default function AuditButton() {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<string | null>(null);

  const handleAudit = async () => {
    setLoading(true);
    setResult(null);
    try {
      const res = await fetch("http://localhost:8000/audit/run");
      const data = await res.json();
      
      if (data.bets_settled > 0) {
        setResult(`✅ ${data.bets_settled} apuestas liquidadas.`);
        // Recargar la página para ver el nuevo saldo
        setTimeout(() => window.location.reload(), 2000);
      } else {
        setResult("👍 Todo al día. No hay resultados nuevos.");
        setTimeout(() => setResult(null), 3000);
      }
    } catch (error) {
      console.error(error);
      setResult("❌ Error contactando al Juez.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex items-center gap-2">
      {result && (
        <span className="text-xs font-mono text-emerald-400 animate-pulse">
          {result}
        </span>
      )}
      <button
        onClick={handleAudit}
        disabled={loading}
        className={`
          flex items-center gap-2 px-4 py-2 rounded-lg font-bold text-xs uppercase tracking-wider transition-all
          ${loading 
            ? "bg-slate-800 text-slate-500 cursor-wait" 
            : "bg-indigo-600 hover:bg-indigo-500 text-white shadow-lg shadow-indigo-900/20"
          }
        `}
      >
        {loading ? (
          <>⚖️ Auditando...</>
        ) : (
          <>🕵️‍♂️ Cobrar / Auditar</>
        )}
      </button>
    </div>
  );
}