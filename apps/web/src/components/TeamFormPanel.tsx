"use client";

import { useState } from "react";
import { History, Loader2 } from "lucide-react";
import { apiFetch } from "@/lib/api";
import TeamFormTable from "./TeamFormTable";

interface TeamFormResponse {
  team_id: number;
  team_name: string;
  cached: boolean;
  cached_at: string;
  stats: {
    over_1_5_pct: number;
    over_2_5_pct: number;
    btts_pct: number;
    avg_cards: number;
    avg_corners: number;
    sample_size: number;
  };
  matches: Array<{
    date: string;
    opponent: string;
    result: string;
    corners: number;
    cards: number;
    goals_1st: number;
    goals_2nd: number;
  }>;
}

interface TeamSlotProps {
  teamId?: number;
  teamLabel: string;
}

function TeamSlot({ teamId, teamLabel }: TeamSlotProps) {
  const [data, setData] = useState<TeamFormResponse | null>(null);
  const [loading, setLoading] = useState(false);

  const loadForm = async () => {
    if (!teamId) return;
    setLoading(true);
    try {
      const res = await apiFetch(`/teams/${teamId}/recent-form?last=5`);
      if (res.ok) {
        setData(await res.json());
      }
    } catch (e) {
      console.error("Error cargando histórico de equipo", e);
    } finally {
      setLoading(false);
    }
  };

  if (!teamId) {
    return (
      <div className="text-xs text-zinc-600 text-center py-4">
        No hay identificador de equipo para {teamLabel}.
      </div>
    );
  }

  if (data) {
    return (
      <TeamFormTable
        teamName={data.team_name || teamLabel}
        stats={data.stats}
        matches={data.matches}
        cached={data.cached}
        cachedAt={data.cached_at}
      />
    );
  }

  return (
    <button
      onClick={loadForm}
      disabled={loading}
      className="w-full flex items-center justify-center gap-2 border border-zinc-800 hover:border-zinc-700 text-zinc-300 py-3 rounded-lg text-sm font-bold transition-colors disabled:opacity-50 cursor-pointer"
    >
      {loading ? <Loader2 size={14} className="animate-spin" /> : <History size={14} />}
      {loading ? "Cargando..." : `Ver historial — ${teamLabel}`}
    </button>
  );
}

interface TeamFormPanelProps {
  homeTeamId?: number;
  awayTeamId?: number;
  homeTeamName: string;
  awayTeamName: string;
}

export default function TeamFormPanel({ homeTeamId, awayTeamId, homeTeamName, awayTeamName }: TeamFormPanelProps) {
  return (
    <div className="border border-zinc-800 rounded-xl p-6">
      <h3 className="text-sm font-bold text-zinc-50 mb-4 flex items-center gap-2">
        <History size={14} className="text-zinc-500" /> Forma Reciente
      </h3>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <TeamSlot teamId={homeTeamId} teamLabel={homeTeamName} />
        <TeamSlot teamId={awayTeamId} teamLabel={awayTeamName} />
      </div>
    </div>
  );
}
