"use client"; // Esto es obligatorio para usar onClick

import { useState } from "react";
import { Bot, RefreshCw } from "lucide-react";
import { toast } from "sonner";
import { apiFetch } from "@/lib/api";

interface AnalyzeButtonProps {
  matchId: string;
  onAnalyzeComplete?: () => void | Promise<void>;
}

export default function AnalyzeButton({ matchId, onAnalyzeComplete }: AnalyzeButtonProps) {
  const [loading, setLoading] = useState(false);

  const handleAnalyze = async () => {
    setLoading(true);
    try {
      const res = await apiFetch(`/matches/${matchId}/analyze`, { method: "POST" });

      if (res.ok) {
        await onAnalyzeComplete?.();
      } else if (res.status === 429) {
        toast.error("Demasiados análisis seguidos", { description: "Espera un momento antes de intentar de nuevo." });
      } else if (res.status === 401) {
        toast.error("Sesión expirada", { description: "Vuelve a iniciar sesión para analizar partidos." });
      } else {
        toast.error("Error al conectar con la IA");
      }
    } catch (error) {
      console.error(error);
      toast.error("Error de conexión");
    } finally {
      setLoading(false);
    }
  };

  return (
    <button
      onClick={handleAnalyze}
      disabled={loading}
      className={`w-full flex items-center justify-center gap-2 font-bold py-3 rounded transition-colors mt-4 cursor-pointer ${
        loading
          ? "bg-zinc-800 text-zinc-500 cursor-not-allowed"
          : "bg-emerald-600 hover:bg-emerald-500 text-zinc-950"
      }`}
    >
      {loading ? (
        <>
          <RefreshCw size={14} className="animate-spin" /> Analizando...
        </>
      ) : (
        <>
          <Bot size={14} /> Solicitar Análisis IA
        </>
      )}
    </button>
  );
}
