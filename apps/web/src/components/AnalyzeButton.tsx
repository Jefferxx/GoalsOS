"use client"; // Esto es obligatorio para usar onClick

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Bot, RefreshCw } from "lucide-react";
import { toast } from "sonner";

export default function AnalyzeButton({ matchId }: { matchId: string }) {
  const [loading, setLoading] = useState(false);
  const router = useRouter();

  const handleAnalyze = async () => {
    setLoading(true);
    try {
      // Usamos localhost:8000 porque este fetch ocurre en TU navegador (Cliente),
      // no en el servidor de Docker.
      const res = await fetch(`http://localhost:8000/matches/${matchId}/analyze`, {
        method: "POST",
      });

      if (res.ok) {
        // Si todo sale bien, recargamos la página para ver el análisis nuevo
        router.refresh();
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
