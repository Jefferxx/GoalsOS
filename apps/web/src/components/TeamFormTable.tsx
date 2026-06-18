interface TeamFormStats {
  over_1_5_pct: number;
  over_2_5_pct: number;
  btts_pct: number;
  avg_cards: number;
  avg_corners: number;
  sample_size: number;
}

interface TeamFormMatch {
  date: string;
  opponent: string;
  result: string;
  corners: number;
  cards: number;
  goals_1st: number;
  goals_2nd: number;
}

interface TeamFormTableProps {
  teamName: string;
  stats: TeamFormStats;
  matches: TeamFormMatch[];
  cached: boolean;
  cachedAt?: string;
}

function StatPill({ label, value }: { label: string; value: string }) {
  return (
    <div className="text-center border border-zinc-800 rounded-lg py-3">
      <div className="text-[9px] text-zinc-500 uppercase font-bold tracking-widest mb-1">{label}</div>
      <div className="text-lg font-bold text-zinc-50">{value}</div>
    </div>
  );
}

export default function TeamFormTable({ teamName, stats, matches, cached, cachedAt }: TeamFormTableProps) {
  if (stats.sample_size === 0) {
    return (
      <p className="text-xs text-zinc-500 text-center py-4">
        Sin partidos finalizados de {teamName} en la base de datos todavía.
      </p>
    );
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-3">
        <h4 className="text-sm font-bold text-zinc-50">{teamName}</h4>
        {cached && cachedAt && (
          <span className="text-[10px] text-zinc-600">
            Datos en caché ({new Date(cachedAt).toLocaleString([], { day: "2-digit", month: "short", hour: "2-digit", minute: "2-digit" })})
          </span>
        )}
      </div>

      <div className="grid grid-cols-3 sm:grid-cols-5 gap-2 mb-4">
        <StatPill label="Más +1.5" value={`${stats.over_1_5_pct}%`} />
        <StatPill label="Más +2.5" value={`${stats.over_2_5_pct}%`} />
        <StatPill label="BTTS" value={`${stats.btts_pct}%`} />
        <StatPill label="Tarjetas" value={stats.avg_cards.toFixed(1)} />
        <StatPill label="Corners" value={stats.avg_corners.toFixed(1)} />
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs border-collapse">
          <thead>
            <tr className="text-zinc-500 text-[9px] uppercase tracking-widest border-b border-zinc-800">
              <th className="py-2 pr-3 font-bold">Rival</th>
              <th className="py-2 pr-3 font-bold">Resultado</th>
              <th className="py-2 pr-3 font-bold text-center">Corners</th>
              <th className="py-2 pr-3 font-bold text-center">Tarjetas</th>
              <th className="py-2 pr-3 font-bold text-center">Goles 1T</th>
              <th className="py-2 font-bold text-center">Goles 2T</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-zinc-800/60">
            {matches.map((m, i) => (
              <tr key={i}>
                <td className="py-2 pr-3 text-zinc-300">{m.opponent}</td>
                <td className={`py-2 pr-3 font-mono font-bold ${m.result.startsWith("W") ? "text-emerald-500" : m.result.startsWith("L") ? "text-red-600" : "text-zinc-400"}`}>
                  {m.result}
                </td>
                <td className="py-2 pr-3 text-center font-mono text-zinc-400">{m.corners}</td>
                <td className="py-2 pr-3 text-center font-mono text-zinc-400">{m.cards}</td>
                <td className="py-2 pr-3 text-center font-mono text-zinc-400">{m.goals_1st}</td>
                <td className="py-2 text-center font-mono text-zinc-400">{m.goals_2nd}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
