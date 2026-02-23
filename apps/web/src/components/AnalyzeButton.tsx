"use client"; // Esto es obligatorio para usar onClick

import { useState } from "react";
import { useRouter } from "next/navigation";

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
        alert("Error al conectar con la IA");
      }
    } catch (error) {
      console.error(error);
      alert("Error de conexión");
    } finally {
      setLoading(false);
    }
  };

  return (
    <button
      onClick={handleAnalyze}
      disabled={loading}
      className={`w-full font-bold py-3 rounded-lg transition-all shadow-lg mt-4 ${
        loading
          ? "bg-slate-700 text-slate-400 cursor-not-allowed"
          : "bg-emerald-600 hover:bg-emerald-500 text-white shadow-emerald-900/50"
      }`}
    >
      {loading ? (
        <span className="flex items-center justify-center gap-2">
          <span className="animate-spin">🔄</span> Analizando...
        </span>
      ) : (
        "🤖 Solicitar Análisis IA"
      )}
    </button>
  );
}