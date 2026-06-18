"use client";

import { useState } from "react";
import { ShieldCheck } from "lucide-react";
import { apiFetch } from "@/lib/api";

export default function AuditButton() {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<string | null>(null);

  const handleAudit = async () => {
    setLoading(true);
    setResult(null);
    try {
      const res = await apiFetch("/audit/run");
      const data = await res.json();

      if (data.processed > 0) {
        setResult(`${data.processed} apuestas liquidadas.`);
        // Recargar la página para ver el nuevo saldo
        setTimeout(() => window.location.reload(), 2000);
      } else {
        setResult("Todo al día. No hay resultados nuevos.");
        setTimeout(() => setResult(null), 3000);
      }
    } catch (error) {
      console.error(error);
      setResult("Error contactando al auditor.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex items-center gap-2">
      {result && (
        <span className="text-xs font-mono text-zinc-400 animate-pulse">
          {result}
        </span>
      )}
      <button
        onClick={handleAudit}
        disabled={loading}
        className="flex items-center gap-1.5 text-zinc-500 hover:text-zinc-200 px-3 py-2 rounded text-xs font-bold uppercase tracking-wider transition-colors disabled:opacity-50 cursor-pointer"
      >
        <ShieldCheck size={14} className={loading ? "animate-pulse" : ""} />
        {loading ? "Auditando..." : "Auditar"}
      </button>
    </div>
  );
}
