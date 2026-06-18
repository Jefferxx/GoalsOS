"use client";
import { useEffect, useState } from "react";
import { Gauge } from "lucide-react";
import { apiFetch } from "@/lib/api";

export default function ApiQuota() {
  const [quota, setQuota] = useState({ current: 0, limit: 100 });

  useEffect(() => {
    const fetchQuota = async () => {
      const res = await apiFetch("/api-status");
      if (res.ok) setQuota(await res.json());
    };
    fetchQuota();
  }, []);

  const percentage = (quota.current / quota.limit) * 100;

  return (
    <div className="flex items-center gap-3 px-2">
      <Gauge size={14} className="text-zinc-500" />
      <div className="w-20 bg-zinc-800 h-1 rounded-full overflow-hidden">
        <div
          className={`h-full transition-all ${percentage > 80 ? "bg-red-600" : "bg-zinc-500"}`}
          style={{ width: `${percentage}%` }}
        ></div>
      </div>
      <span className="text-xs font-mono text-zinc-500">{quota.current}/{quota.limit}</span>
    </div>
  );
}
