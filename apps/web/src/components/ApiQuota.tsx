"use client";
import { useEffect, useState } from "react";
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
    <div className="bg-slate-900 border border-slate-800 p-3 rounded-lg flex items-center gap-4">
      <div className="text-xs font-bold text-slate-500 uppercase">API Credits</div>
      <div className="flex-1 bg-slate-800 h-2 rounded-full overflow-hidden">
        <div 
          className={`h-full transition-all ${percentage > 80 ? 'bg-red-500' : 'bg-emerald-500'}`}
          style={{ width: `${percentage}%` }}
        ></div>
      </div>
      <div className="text-xs font-mono text-slate-300">{quota.current}/{quota.limit}</div>
    </div>
  );
}