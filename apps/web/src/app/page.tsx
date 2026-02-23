import Link from "next/link";
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
    <main className="min-h-screen bg-slate-950 text-slate-100 p-4 md:p-8 font-sans">
      
      {/* --- HEADER --- */}
      <header className="mb-8 flex flex-col xl:flex-row justify-between items-center gap-6">
        <div className="text-center xl:text-left">
          <h1 className="text-4xl font-extrabold tracking-tight bg-gradient-to-r from-emerald-400 to-cyan-500 bg-clip-text text-transparent">
            GoalOS Enterprise
          </h1>
          <p className="text-slate-400 text-sm font-medium tracking-wide mt-1">
            SISTEMA DE INVERSIÓN INTELIGENTE v6.2
          </p>
        </div>
        
        {/* BARRA DE HERRAMIENTAS */}
        <div className="flex flex-wrap items-center justify-center gap-3 bg-slate-900/50 p-2 rounded-xl border border-slate-800/50 backdrop-blur-sm">
            <AuditButton />
            <div className="h-6 w-px bg-slate-800 mx-1 hidden md:block"></div>
            <SyncButton />
            <div className="h-6 w-px bg-slate-800 mx-1 hidden md:block"></div>
            <ApiQuota />
            <UserMenu />
        </div>
      </header>

      {/* --- SECCIÓN HERO (FINANZAS) --- */}
      <section className="mb-12 max-w-5xl mx-auto">
        <div className="h-[350px] w-full transform hover:scale-[1.01] transition-transform duration-500">
            <RoiChart />
        </div>
      </section>
      
      {/* --- GENERADOR DE PARLEYS --- */}
      <section className="mb-12 max-w-4xl mx-auto">
         <ParleyGenerator />
      </section>

      {/* --- GRID DE PARTIDOS --- */}
      <section>
        <div className="flex items-center justify-between mb-6 border-b border-slate-800 pb-4">
            <h2 className="text-2xl font-bold text-white flex items-center gap-3">
                ⚽ Mercado Activo
                <span className="text-xs bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 px-3 py-1 rounded-full font-bold">
                    {activeMatches.length} EN VIVO
                </span>
            </h2>
            
            {/* ENLACE AL HISTORIAL */}
            <Link href="/history" className="text-xs font-bold text-slate-400 hover:text-white transition-colors flex items-center gap-2 group">
                Ver Historial Completado
                <span className="group-hover:translate-x-1 transition-transform">→</span>
            </Link>
        </div>

        {activeMatches.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
                {activeMatches.map((match) => (
                <Link href={`/match/${match.api_id}`} key={match.id} className="group block h-full">
                    <article className="bg-slate-900/80 border border-slate-800 rounded-2xl p-5 hover:border-emerald-500/50 hover:bg-slate-900 transition-all duration-300 h-full relative overflow-hidden shadow-lg hover:shadow-emerald-900/20">
                    
                    {match.ai_analysis && (
                        <div className="absolute top-0 right-0 p-3">
                            <span className="flex h-3 w-3">
                                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-50"></span>
                                <span className="relative inline-flex rounded-full h-3 w-3 bg-emerald-500"></span>
                            </span>
                        </div>
                    )}

                    <div className="flex justify-between items-center mb-5">
                        <span className="text-[10px] font-black text-slate-500 uppercase tracking-widest bg-slate-950 px-2 py-1 rounded border border-slate-800">
                        {match.league_name}
                        </span>
                        {match.ai_analysis?.confidence && (
                        <span className={`text-[10px] px-2 py-1 rounded border font-bold uppercase tracking-wider ${
                            match.ai_analysis.confidence > 80 
                            ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20" 
                            : "bg-yellow-500/10 text-yellow-400 border-yellow-500/20"
                        }`}>
                            {match.ai_analysis.confidence}% IA
                        </span>
                        )}
                    </div>

                    <div className="flex justify-between items-center mb-6 px-2">
                        <div className="text-center w-[40%]">
                            <div className="font-bold text-lg leading-tight text-white group-hover:text-emerald-300 transition-colors">
                                {match.home_team}
                            </div>
                        </div>
                        <div className="text-slate-700 font-black text-xs bg-slate-950 px-2 py-1 rounded-full">VS</div>
                        <div className="text-center w-[40%]">
                            <div className="font-bold text-lg leading-tight text-white group-hover:text-emerald-300 transition-colors">
                                {match.away_team}
                            </div>
                        </div>
                    </div>

                    {match.ai_analysis ? (
                        <div className="bg-slate-950/60 p-4 rounded-xl border border-slate-800/60 group-hover:border-slate-700/60 transition-colors">
                            <p className="text-xs text-slate-400 italic mb-3 line-clamp-2 leading-relaxed">
                                &quot;{match.ai_analysis.summary || match.ai_analysis.reasoning}&quot;
                            </p>
                            {match.ai_analysis.prediction && (
                                <div className="flex items-center justify-between border-t border-slate-800 pt-2 mt-1">
                                    <span className="text-[10px] text-slate-500 font-bold uppercase">Recomendación</span>
                                    <span className="text-xs font-bold text-emerald-400 font-mono bg-emerald-500/10 px-2 py-0.5 rounded">
                                        {match.ai_analysis.prediction}
                                    </span>
                                </div>
                            )}
                        </div>
                    ) : (
                        <div className="text-xs text-slate-600 text-center py-6 bg-slate-950/20 rounded-xl border border-slate-800/30 border-dashed group-hover:border-slate-700 transition-colors">
                            Esperando análisis...
                        </div>
                    )}
                    </article>
                </Link>
                ))}
            </div>
        ) : (
            <div className="text-center py-20 bg-slate-900/30 rounded-3xl border border-slate-800 border-dashed">
                <p className="text-slate-500 text-lg">No hay partidos activos.</p>
                <p className="text-slate-600 text-sm mt-2">Sincroniza el mercado para ver nuevas oportunidades.</p>
            </div>
        )}
      </section>
    </main>
  );
}