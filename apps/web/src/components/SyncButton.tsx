// apps/web/src/components/SyncButton.tsx
"use client";
import { useState } from "react";
import { apiFetch } from "@/lib/api";

export default function SyncButton() {
  const [loading, setLoading] = useState(false);

  const handleSync = async () => {
    setLoading(true);
    try {
      await apiFetch("/test/ingest");
      alert("Cosecha iniciada en segundo plano 🦅");
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  return (
    <button 
      onClick={handleSync}
      disabled={loading}
      className="bg-emerald-600 hover:bg-emerald-500 text-white px-4 py-2 rounded-lg text-sm font-bold disabled:opacity-50"
    >
      {loading ? "Sincronizando..." : "🔄 Sincronizar Mercados"}
    </button>
  );
}