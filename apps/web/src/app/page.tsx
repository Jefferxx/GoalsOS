import Link from "next/link";
import { ArrowRight, Inbox, TrendingUp } from "lucide-react";
import UserMenu from "@/components/UserMenu";
import RoiChart from "@/components/RoiChart";
import ParleyGenerator from "@/components/ParleyGenerator";
import ApiQuota from "@/components/ApiQuota";
import SyncButton from "@/components/SyncButton";
import AuditButton from "@/components/AuditButton";

// Definición simple de Match
interface Match {
  id: number;
  api_id: string;
  home_team: string;
  away_team: string;
  league_name: string;
  date: string;
  status: string; // Necesitamos el estado para filtrar
  ai_analysis: any;
}

async function getMatches(): Promise<Match[]> {
  try {
    const res = await fetch("http://api:8000/matches", {
      cache: "no-store"
    });

    if (!res.ok) return [];
    const json = await res.json();
    return json.data || [];
  } catch (error) {
    console.error("Error fetching matches:", error);
    return [];
  }
}

export default async function Home() {
  const allMatches = await getMatches();

  // --- FILTRO DE LIMPIEZA ---
  // Ocultamos partidos terminados (FT, AET, PEN) para que no ensucien el dashboard
  // Solo mostramos pendientes (NS), en juego (1H, 2H, HT) o pospuestos (PST)
  const activeMatches = allMatches.filter(match =>
    !["FT", "AET", "PEN"].includes(match.status || "NS")
  );

  return (
    <main className="min-h-screen bg-zinc-950 text-zinc-200 p-4 md:p-8 font-sans">

      {/* --- HEADER --- */}
      <header className="mb-10 flex flex-col xl:flex-row justify-between items-center gap-6">
        <div className="text-center xl:text-left">
          <h1 className="text-3xl font-bold text-zinc-50">
            GoalOS
          </h1>
          <p className="text-zinc-500 text-xs font-medium tracking-widest uppercase mt-1">
            Sistema de Inversión Inteligente
          </p>
        </div>

        {/* BARRA DE HERRAMIENTAS */}
        <div className="flex flex-wrap items-center justify-center gap-1">
            <AuditButton />
            <div className="h-4 w-px bg-zinc-800 mx-1 hidden md:block"></div>
            <SyncButton />
            <div className="h-4 w-px bg-zinc-800 mx-1 hidden md:block"></div>
            <ApiQuota />
            <div className="h-4 w-px bg-zinc-800 mx-1 hidden md:block"></div>
            <UserMenu />
        </div>
      </header>

      {/* --- SECCIÓN HERO (FINANZAS) --- */}
      <section className="mb-12 max-w-5xl mx-auto">
        <div className="h-[350px] w-full">
            <RoiChart />
        </div>
      </section>

      {/* --- GENERADOR DE PARLEYS --- */}
      <section className="mb-12 max-w-4xl mx-auto">
         <ParleyGenerator />
      </section>

      {/* --- GRID DE PARTIDOS --- */}
      <section>
        <div className="flex items-center justify-between mb-6 border-b border-zinc-800 pb-4">
            <h2 className="text-lg font-bold text-zinc-50 flex items-center gap-3">
                <TrendingUp size={18} className="text-zinc-500" />
                Mercado Activo
                <span className="text-xs text-zinc-500 font-mono">
                    {activeMatches.length}
                </span>
            </h2>

            {/* ENLACE AL HISTORIAL */}
            <Link href="/history" className="text-xs font-bold text-zinc-500 hover:text-zinc-200 transition-colors flex items-center gap-1.5 group">
                Ver Historial
                <ArrowRight size={12} className="group-hover:translate-x-1 transition-transform" />
            </Link>
        </div>

        {activeMatches.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-px bg-zinc-800">
                {activeMatches.map((match) => (
                <Link href={`/match/${match.api_id}`} key={match.id} className="group block h-full bg-zinc-950 hover:bg-zinc-900 transition-colors">
                    <article className="p-5 h-full relative">

                    <div className="flex justify-between items-center mb-5">
                        <span className="text-[10px] font-bold text-zinc-600 uppercase tracking-widest">
                        {match.league_name}
                        </span>
                        {match.ai_analysis?.confidence && (
                        <span className="text-[10px] text-zinc-500 font-mono">
                            {match.ai_analysis.confidence}% IA
                        </span>
                        )}
                    </div>

                    <div className="flex justify-between items-center mb-6 px-2">
                        <div className="text-center w-[40%]">
                            <div className="font-bold text-base leading-tight text-zinc-50">
                                {match.home_team}
                            </div>
                        </div>
                        <div className="text-zinc-700 font-bold text-[10px]">VS</div>
                        <div className="text-center w-[40%]">
                            <div className="font-bold text-base leading-tight text-zinc-50">
                                {match.away_team}
                            </div>
                        </div>
                    </div>

                    {match.ai_analysis ? (
                        <div className="pt-3 border-t border-zinc-800/80">
                            <p className="text-xs text-zinc-500 italic mb-3 line-clamp-2 leading-relaxed">
                                &quot;{match.ai_analysis.summary || match.ai_analysis.reasoning}&quot;
                            </p>
                            {match.ai_analysis.prediction && (
                                <div className="flex items-center justify-between">
                                    <span className="text-[10px] text-zinc-600 font-bold uppercase tracking-widest">Recomendación</span>
                                    <span className="text-xs font-bold text-emerald-500 font-mono">
                                        {match.ai_analysis.prediction}
                                    </span>
                                </div>
                            )}
                        </div>
                    ) : (
                        <div className="text-xs text-zinc-600 text-center py-6">
                            Esperando análisis...
                        </div>
                    )}
                    </article>
                </Link>
                ))}
            </div>
        ) : (
            <div className="text-center py-20 border border-zinc-800 border-dashed rounded-xl">
                <Inbox size={24} className="mx-auto mb-3 text-zinc-700" />
                <p className="text-zinc-500">No hay partidos activos.</p>
                <p className="text-zinc-600 text-sm mt-2">Sincroniza el mercado para ver nuevas oportunidades.</p>
            </div>
        )}
      </section>
    </main>
  );
}
