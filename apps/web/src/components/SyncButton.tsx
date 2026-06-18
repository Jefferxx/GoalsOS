// apps/web/src/components/SyncButton.tsx
"use client";
import { useState } from "react";
import { RefreshCw } from "lucide-react";
import { apiFetch } from "@/lib/api";
import { toast } from "sonner";

export default function SyncButton() {
  const [loading, setLoading] = useState(false);

  const handleSync = async () => {
    setLoading(true);
    try {
      await apiFetch("/test/ingest");
      toast.success("Sincronización de mercados iniciada en segundo plano.");
    } catch (e) {
      console.error(e);
      toast.error("Error al iniciar la sincronización.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <button
      onClick={handleSync}
      disabled={loading}
      className="flex items-center gap-1.5 text-zinc-500 hover:text-zinc-200 px-3 py-2 rounded text-xs font-bold uppercase tracking-wider transition-colors disabled:opacity-50 cursor-pointer"
    >
      <RefreshCw size={14} className={loading ? "animate-spin" : ""} />
      {loading ? "Sincronizando..." : "Sincronizar"}
    </button>
  );
}
