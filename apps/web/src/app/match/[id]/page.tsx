"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import UserMenu from "@/components/UserMenu";
import AnalyzeButton from "@/components/AnalyzeButton";
import BetButton from "@/components/BetButton";
import InjuryList from "@/components/InjuryList";

interface OddsData {
  homeWin?: number;
  draw?: number;
  awayWin?: number;
  [key: string]: any; // Permitir otras propiedades para flexibilidad
}

// --- TIPOS ---
interface MatchDetail {
  id: number;
  api_id: string;
  home_team: string;
  away_team: string;
  league_name: string;
  date: string;
  status: string;
  home_score?: number;
  away_score?: number;
  ai_analysis?: any;
  odds_data?: OddsData | string | any; // Tipado flexible para manejar la complejidad de la API
  injuries?: any;
  api_prediction?: any;
  lineups?: any;
}

export default function MatchPage() {
  const params = useParams();
  const id = params?.id as string;
  const [match, setMatch] = useState<MatchDetail | null>(null);
  const [loading, setLoading] = useState(true);

  // Función para obtener/recargar datos
  const fetchMatch = async () => {
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const res = await fetch(`${apiUrl}/matches/${id}`);

      if (res.ok) {
        const data = await res.json();
        setMatch(data);
      } else {
        console.error("Partido no encontrado en DB");
      }
    } catch (error) {
      console.error("Error de conexión:", error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (id) fetchMatch();
  }, [id]);

  if (loading) return (
    <div className="min-h-screen bg-slate-950 flex items-center justify-center">
        <div className="flex flex-col items-center gap-4">
            <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-emerald-500"></div>
            <p className="text-slate-500 text-sm animate-pulse">Cargando inteligencia...</p>
        </div>
    </div>
  );

  if (!match) return (
    <div className="min-h-screen bg-slate-950 text-white flex flex-col items-center justify-center p-6">
        <div className="bg-slate-900 p-8 rounded-2xl border border-slate-800 text-center max-w-md">
            <h1 className="text-2xl font-bold mb-2">Partido no encontrado 😕</h1>
            <p className="text-slate-400 mb-6 text-sm">Es posible que el ID sea incorrecto o el partido no se haya sincronizado aún.</p>
            <Link href="/" className="px-6 py-2 bg-emerald-600 hover:bg-emerald-500 rounded-lg text-white font-bold transition-colors">
                Volver al Dashboard
            </Link>
        </div>
    </div>
  );

  // Parseo seguro del análisis de IA
  let analysisData = null;
  try {
      if (match.ai_analysis) {
          analysisData = typeof match.ai_analysis === 'string' 
            ? JSON.parse(match.ai_analysis) 
            : match.ai_analysis;
      }
  } catch (e) { console.error("Error parsing analysis", e); }

  let injuriesCount = 0;
  if (match.injuries) {
    try {
      const parsedInjuries = typeof match.injuries === 'string' 
        ? JSON.parse(match.injuries) 
        : match.injuries;
      if (Array.isArray(parsedInjuries)) {
        injuriesCount = parsedInjuries.length;
      }
    } catch (e) {
      console.error("Error parsing match.injuries", e);
    }
  }

  // --- FUNCIÓN DECODIFICADORA DE CUOTAS MEJORADA ---
  const getOddsValue = (selectionCode: string, oddsData: any): number => {
    // 1. Si no hay datos, bye.
    if (!oddsData) return 1.0;

    let parsedOdds = oddsData;

    // 2. Si es string, intentamos parsear.
    if (typeof oddsData === 'string') {
      try {
        parsedOdds = JSON.parse(oddsData);
      } catch (e) {
        console.error("Error parsing oddsData string:", e);
        return 1.0;
      }
    }

    // 3. ESTRATEGIA A: Formato Simple (Objeto plano {homeWin, draw, awayWin})
    if (parsedOdds.homeWin) {
       switch (selectionCode) {
        case '1': return parsedOdds.homeWin || 1.0;
        case 'X': return parsedOdds.draw || 1.0;
        case '2': return parsedOdds.awayWin || 1.0;
        default: return 1.0;
      }
    }

    // 4. ESTRATEGIA B: Formato Real API-Football (Bookmakers -> Bets -> Values)
    // Estructura típica: { response: [ { bookmakers: [...] } ] } o directo { bookmakers: [...] }
    try {
        // Normalizamos para encontrar el array de bookmakers
        let bookmakers = null;
        
        if (parsedOdds.bookmakers) {
            bookmakers = parsedOdds.bookmakers;
        } else if (parsedOdds.response && Array.isArray(parsedOdds.response) && parsedOdds.response.length > 0) {
            bookmakers = parsedOdds.response[0].bookmakers;
        } else if (Array.isArray(parsedOdds)) {
             // A veces viene como array directo de bookmakers
             bookmakers = parsedOdds;
        }

        if (!bookmakers || !Array.isArray(bookmakers) || bookmakers.length === 0) return 1.0;

        // Usamos el primer bookmaker (usualmente Bet365 o similar, el más relevante)
        const bets = bookmakers[0].bets;
        if (!bets) return 1.0;

        // Buscamos la apuesta tipo "Match Winner" (ID 1 o nombre "Match Winner")
        const matchWinnerBet = bets.find((b: any) => b.name === "Match Winner" || b.id === 1);

        if (matchWinnerBet && matchWinnerBet.values) {
            let targetValue = "";
            // Mapeo: 1 -> Home, X -> Draw, 2 -> Away
            if (selectionCode === '1') targetValue = "Home";
            else if (selectionCode === 'X') targetValue = "Draw";
            else if (selectionCode === '2') targetValue = "Away";
            else return 1.0;

            const oddObj = matchWinnerBet.values.find((v: any) => v.value === targetValue);
            return oddObj ? parseFloat(oddObj.odd) : 1.0;
        }
    } catch (e) {
        console.error("Error digging into API-Football structure:", e);
    }

    return 1.0;
  };

  const getStatusLabel = (status: string) => {
    const map: Record<string, string> = {
      'NS': '🕒 Por Iniciar',
      '1H': '🔴 En Vivo (1T)',
      'HT': '⏸️ Entretiempo',
      '2H': '🔴 En Vivo (2T)',
      'FT': '🏁 Finalizado',
      'AET': '🔴 Prórroga',
      'PEN': '🥅 Penales',
      'PST': 'Postergado',
      'CANC': 'Cancelado'
    };
    return map[status] || status;
  };

  return (
    <main className="min-h-screen bg-slate-950 text-slate-100 font-sans pb-20">

      {/* HEADER DE NAVEGACIÓN */}
      <header className="px-6 py-4 border-b border-slate-800 flex justify-between items-center bg-slate-900/80 backdrop-blur-md sticky top-0 z-50">
        <Link href="/" className="text-xs font-bold text-emerald-400 hover:text-emerald-300 flex items-center gap-2 group uppercase tracking-wider">
            <span className="group-hover:-translate-x-1 transition-transform text-lg">←</span> Volver
        </Link>
        <UserMenu />
      </header>

      <div className="max-w-6xl mx-auto p-4 md:p-8 space-y-8">

        {/* 1. SCOREBOARD (Encabezado del Partido) */}
        <div className="bg-gradient-to-br from-slate-900 to-slate-950 border border-slate-800 rounded-3xl p-8 text-center shadow-2xl relative overflow-hidden group">
            <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-transparent via-emerald-500/50 to-transparent opacity-50 group-hover:opacity-100 transition-opacity"></div>

            <div className="flex flex-col items-center justify-center mb-6">
                <span className="px-3 py-1 rounded-full bg-slate-800/50 text-[10px] font-bold uppercase tracking-widest text-slate-400 border border-slate-700/50">
                    {match.league_name}
                </span>
                <span className="text-[10px] text-emerald-400 mt-2 font-mono font-bold">
                    {/* ✅ AQUÍ ESTÁ EL ARREGLO DE HORA LOCAL */}
                    {new Date(match.date).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}
                </span>
            </div>

            <div className="flex flex-col md:flex-row justify-between items-center max-w-2xl mx-auto gap-6 md:gap-0">
                <div className="flex-1 text-center md:text-right w-full">
                    <h2 className="text-2xl md:text-4xl font-black text-white leading-tight tracking-tight">{match.home_team}</h2> 
                </div>

                <div className="px-6 flex flex-col items-center">
                    <div className="text-5xl md:text-7xl font-mono font-bold text-emerald-400 tracking-tighter flex items-center gap-4 drop-shadow-[0_0_15px_rgba(52,211,153,0.3)]">
                        <span>{match.home_score ?? '-'}</span>
                        <span className="text-slate-700 text-3xl">:</span>
                        <span>{match.away_score ?? '-'}</span>
                    </div>
                    {/* Dynamic Status Label */}
                    {(() => {
                        const statusLabel = getStatusLabel(match.status);
                        let bgColorClass = 'bg-slate-600'; // Default for 'Por Iniciar'

                        if (statusLabel.includes('En Vivo') || statusLabel.includes('1T') || statusLabel.includes('2T') || statusLabel.includes('Prórroga') || statusLabel.includes('Penales')) {
                            bgColorClass = 'bg-rose-600';
                        } else if (statusLabel.includes('Finalizado')) {
                            bgColorClass = 'bg-slate-700';
                        }
                        return (
                            <div className={`mt-3 text-[10px] font-black text-white uppercase ${bgColorClass} px-3 py-1 rounded-full shadow-lg`}>
                                {statusLabel}
                            </div>
                        );
                    })()}
                </div>

                <div className="flex-1 text-center md:text-left w-full">
                    <h2 className="text-2xl md:text-4xl font-black text-white leading-tight tracking-tight">{match.away_team}</h2> 
                </div>
            </div>
        </div>

        {/* 2. HUD DE DATOS */}
        <div className="flex flex-wrap justify-center gap-2 mt-4">
          <span className={`text-xs font-bold px-3 py-1 rounded-full ${injuriesCount > 0 ? 'bg-red-900/50 text-red-300' : 'bg-slate-800/50 text-slate-400'} border border-current`}>
            🏥 Lesiones: {injuriesCount}
          </span>
          <span className="text-xs font-bold px-3 py-1 rounded-full bg-emerald-900/50 text-emerald-300 border border-current">
            ⚔️ H2H: Analizado
          </span>
          <span className="text-xs font-bold px-3 py-1 rounded-full bg-blue-900/50 text-blue-300 border border-current">
            🤖 IA: Gemini Flash
          </span>
          <span className={`text-xs font-bold px-3 py-1 rounded-full ${match.odds_data ? 'bg-yellow-900/50 text-yellow-300' : 'bg-slate-800/50 text-slate-400'} border border-current`}>
            💰 Cuotas: {match.odds_data ? 'Sincronizadas' : 'No Disponibles'}
          </span>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">

            {/* COLUMNA IZQUIERDA: ANÁLISIS E INFO */}
            <div className="lg:col-span-2 space-y-6">

                {/* 4. RESULTADOS DEL ANÁLISIS (Si existe) */}
                {analysisData && (
                    <div className="bg-slate-900 border border-slate-800 rounded-3xl p-8 shadow-2xl animate-in fade-in slide-in-from-bottom-4 duration-700 relative overflow-hidden">
                        <div className="absolute -top-20 -right-20 w-64 h-64 bg-blue-500/5 rounded-full blur-3xl"></div>

                        <div className="flex items-center gap-4 mb-8 pb-6 border-b border-slate-800 relative z-10">
                            <div className="h-12 w-12 rounded-xl bg-blue-500/10 border border-blue-500/20 flex items-center justify-center text-2xl shadow-[0_0_15px_rgba(59,130,246,0.1)]">
                                🔮
                            </div>
                            <div>
                                <h3 className="text-xl font-bold text-white">Veredicto del Algoritmo</h3>
                                <p className="text-xs text-slate-400 font-mono mt-1">Modelo: Gemini 2.0 Flash • Estrategia: Kelly Criterion</p>
                            </div>
                        </div>

                        <div className="space-y-8 relative z-10">
                            {/* Estadísticas Clave */}
                            <div className="grid grid-cols-3 gap-4">
                                <div className="bg-slate-950/50 p-4 rounded-xl border border-slate-800 text-center">
                                    <div className="text-[10px] text-slate-500 font-bold uppercase tracking-widest mb-1">Probabilidad</div>
                                    <div className="text-2xl font-black text-white">{(analysisData.win_probability * 100).toFixed(0)}%</div>
                                </div>
                                <div className="bg-slate-950/50 p-4 rounded-xl border border-slate-800 text-center">
                                    <div className="text-[10px] text-slate-500 font-bold uppercase tracking-widest mb-1">Confianza</div>
                                    <div className={`text-2xl font-black ${analysisData.confidence >= 80 ? 'text-emerald-400' : 'text-yellow-400'}`}>
                                        {analysisData.confidence}%
                                    </div>
                                </div>
                                <div className="bg-slate-950/50 p-4 rounded-xl border border-slate-800 text-center">
                                    <div className="text-[10px] text-slate-500 font-bold uppercase tracking-widest mb-1">Riesgo</div>
                                    <div className={`text-2xl font-black ${analysisData.risk_level === 'High' ? 'text-rose-400' : 'text-blue-400'}`}>
                                        {analysisData.risk_level || "Medium"}
                                    </div>
                                </div>
                            </div>

                            {/* Pick Principal & Razón */}
                            <div className="bg-slate-800/30 rounded-2xl border border-slate-700/50 p-6">
                                <div className="flex flex-col md:flex-row gap-6 items-start md:items-center">
                                    <div className="flex-1">
                                        <span className="text-xs font-bold text-blue-400 uppercase tracking-widest mb-2 block">Selección Recomendada</span>
                                        <div className="text-3xl font-black text-white tracking-tight">
                                            {analysisData.prediction}
                                        </div>
                                    </div>
                                    <div className="w-full md:w-2/3 bg-slate-900/80 p-4 rounded-xl border-l-2 border-blue-500">
                                        <p className="text-slate-300 text-sm leading-relaxed italic">
                                            "{analysisData.reasoning}"
                                        </p>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                )}

                {/* 5. LISTA DE LESIONES */}
                {match.injuries && (
                    <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6">
                        <InjuryList injuriesJson={match.injuries} />
                    </div>
                )}
            </div>

            {/* COLUMNA DERECHA: ACCIONES Y DETALLES TÉCNICOS */}
            <aside className="space-y-6">

                {/* CAJA DE ACCIONES (ANÁLISIS Y APUESTA) */}
                <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-6 shadow-lg">
                    {/* Botón Analizar */}
                    <div>
                        <h3 className="text-sm font-bold text-white mb-2 flex items-center gap-2">
                            🤖 Cerebro Táctico
                        </h3>
                        <AnalyzeButton matchId={match.api_id} onAnalyzeComplete={fetchMatch} />
                    </div>

                    <div className="border-t border-slate-800 pt-6">
                        <h3 className="text-sm font-bold text-white mb-2">💰 Ejecución</h3>
                        {analysisData ? (
                            <BetButton
                                matchApiId={match.api_id}
                                selection={analysisData.prediction}
                                odds={getOddsValue(analysisData.selection_code, match.odds_data)}
                                aiProbability={analysisData.win_probability || 0}
                            />
                        ) : (
                            <button disabled className="w-full py-3 bg-slate-800 text-slate-500 font-bold rounded-lg cursor-not-allowed text-xs uppercase tracking-widest border border-slate-700">
                                🔒 Requiere Análisis
                            </button>
                        )}
                    </div>
                </div>

            </aside>
        </div>

      </div>
    </main>
  );
}