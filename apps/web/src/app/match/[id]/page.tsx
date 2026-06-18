"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import UserMenu from "@/components/UserMenu";
import AnalyzeButton from "@/components/AnalyzeButton";
import BetButton from "@/components/BetButton";
import InjuryList from "@/components/InjuryList";
import {
  ArrowLeft,
  SearchX,
  Clock,
  Circle,
  Pause,
  Flag,
  Target,
  Stethoscope,
  Swords,
  Bot,
  Wallet,
  Lock,
  Sparkles,
} from "lucide-react";

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
    <div className="min-h-screen bg-zinc-950 flex items-center justify-center">
        <div className="flex flex-col items-center gap-4">
            <div className="animate-spin rounded-full h-10 w-10 border-t-2 border-emerald-500"></div>
            <p className="text-zinc-500 text-sm animate-pulse">Cargando inteligencia...</p>
        </div>
    </div>
  );

  if (!match) return (
    <div className="min-h-screen bg-zinc-950 text-zinc-200 flex flex-col items-center justify-center p-6">
        <div className="text-center max-w-md">
            <SearchX size={28} className="mx-auto mb-4 text-zinc-600" />
            <h1 className="text-xl font-bold mb-2">Partido no encontrado</h1>
            <p className="text-zinc-500 mb-6 text-sm">Es posible que el ID sea incorrecto o el partido no se haya sincronizado aún.</p>
            <Link href="/" className="px-6 py-2 bg-emerald-600 hover:bg-emerald-500 rounded text-zinc-950 font-bold transition-colors">
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

  // Estado del partido: texto + icono + si es "en vivo" (para el color)
  const getStatusInfo = (status: string) => {
    const map: Record<string, { label: string; Icon: typeof Clock; live?: boolean }> = {
      'NS': { label: 'Por Iniciar', Icon: Clock },
      '1H': { label: 'En Vivo (1T)', Icon: Circle, live: true },
      'HT': { label: 'Entretiempo', Icon: Pause },
      '2H': { label: 'En Vivo (2T)', Icon: Circle, live: true },
      'FT': { label: 'Finalizado', Icon: Flag },
      'AET': { label: 'Prórroga', Icon: Circle, live: true },
      'PEN': { label: 'Penales', Icon: Target },
      'PST': { label: 'Postergado', Icon: Clock },
      'CANC': { label: 'Cancelado', Icon: Clock },
    };
    return map[status] || { label: status, Icon: Clock };
  };

  const statusInfo = getStatusInfo(match.status);

  return (
    <main className="min-h-screen bg-zinc-950 text-zinc-200 font-sans pb-20">

      {/* HEADER DE NAVEGACIÓN */}
      <header className="px-6 py-4 border-b border-zinc-800 flex justify-between items-center bg-zinc-950 sticky top-0 z-50">
        <Link href="/" className="text-xs font-bold text-zinc-500 hover:text-zinc-200 flex items-center gap-2 group uppercase tracking-wider transition-colors">
            <ArrowLeft size={14} className="group-hover:-translate-x-1 transition-transform" /> Volver
        </Link>
        <UserMenu />
      </header>

      <div className="max-w-6xl mx-auto p-4 md:p-8 space-y-8">

        {/* 1. SCOREBOARD (Encabezado del Partido) */}
        <div className="border border-zinc-800 rounded-xl p-8 text-center">

            <div className="flex flex-col items-center justify-center mb-6">
                <span className="text-[10px] font-bold uppercase tracking-widest text-zinc-500">
                    {match.league_name}
                </span>
                <span className="text-[10px] text-zinc-400 mt-2 font-mono font-bold">
                    {new Date(match.date).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    {" · "}
                    {new Date(match.date).toLocaleDateString([], { day: '2-digit', month: 'short' })}
                </span>
            </div>

            <div className="flex flex-col md:flex-row justify-between items-center max-w-2xl mx-auto gap-6 md:gap-0">
                <div className="flex-1 text-center md:text-right w-full">
                    <h2 className="text-2xl md:text-4xl font-bold text-zinc-50 leading-tight tracking-tight">{match.home_team}</h2>
                </div>

                <div className="px-6 flex flex-col items-center">
                    <div className="text-5xl md:text-7xl font-mono font-bold text-zinc-50 tracking-tighter flex items-center gap-4">
                        <span>{match.home_score ?? '-'}</span>
                        <span className="text-zinc-700 text-3xl">:</span>
                        <span>{match.away_score ?? '-'}</span>
                    </div>
                    <div className={`mt-3 flex items-center gap-1.5 text-[10px] font-bold uppercase tracking-widest ${statusInfo.live ? 'text-red-600' : 'text-zinc-500'}`}>
                        <statusInfo.Icon size={11} className={statusInfo.live ? "fill-red-600" : ""} />
                        {statusInfo.label}
                    </div>
                </div>

                <div className="flex-1 text-center md:text-left w-full">
                    <h2 className="text-2xl md:text-4xl font-bold text-zinc-50 leading-tight tracking-tight">{match.away_team}</h2>
                </div>
            </div>
        </div>

        {/* 2. HUD DE DATOS */}
        <div className="flex flex-wrap justify-center gap-4 text-xs text-zinc-500">
          <span className="flex items-center gap-1.5">
            <Stethoscope size={13} className={injuriesCount > 0 ? "text-red-600" : "text-zinc-600"} />
            Lesiones: {injuriesCount}
          </span>
          <span className="flex items-center gap-1.5">
            <Swords size={13} className="text-zinc-600" /> H2H: Analizado
          </span>
          <span className="flex items-center gap-1.5">
            <Bot size={13} className="text-zinc-600" /> IA: Gemini 3.1 Flash Lite
          </span>
          <span className="flex items-center gap-1.5">
            <Wallet size={13} className={match.odds_data ? "text-emerald-500" : "text-zinc-600"} />
            Cuotas: {match.odds_data ? 'Sincronizadas' : 'No Disponibles'}
          </span>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">

            {/* COLUMNA IZQUIERDA: ANÁLISIS E INFO */}
            <div className="lg:col-span-2 space-y-6">

                {/* 4. RESULTADOS DEL ANÁLISIS (Si existe) */}
                {analysisData && (
                    <div className="border border-zinc-800 rounded-xl p-8">
                        <div className="flex items-center gap-4 mb-8 pb-6 border-b border-zinc-800">
                            <Sparkles size={20} className="text-emerald-500" />
                            <div>
                                <h3 className="text-lg font-bold text-zinc-50">Veredicto del Algoritmo</h3>
                                <p className="text-xs text-zinc-500 font-mono mt-1">Modelo: Gemini 3.1 Flash Lite · Estrategia: Kelly Criterion</p>
                            </div>
                        </div>

                        <div className="space-y-8">
                            {/* Estadísticas Clave */}
                            <div className="grid grid-cols-3 gap-4">
                                <div className="text-center">
                                    <div className="text-[10px] text-zinc-500 font-bold uppercase tracking-widest mb-1">Probabilidad</div>
                                    <div className="text-2xl font-bold text-zinc-50">{(analysisData.win_probability * 100).toFixed(0)}%</div>
                                </div>
                                <div className="text-center">
                                    <div className="text-[10px] text-zinc-500 font-bold uppercase tracking-widest mb-1">Confianza</div>
                                    <div className="text-2xl font-bold text-zinc-50">
                                        {analysisData.confidence}%
                                    </div>
                                </div>
                                <div className="text-center">
                                    <div className="text-[10px] text-zinc-500 font-bold uppercase tracking-widest mb-1">Riesgo</div>
                                    <div className={`text-2xl font-bold ${analysisData.risk_level === 'High' ? 'text-red-600' : 'text-zinc-50'}`}>
                                        {analysisData.risk_level || "Medium"}
                                    </div>
                                </div>
                            </div>

                            {/* Pick Principal & Razón */}
                            <div className="border-t border-zinc-800 pt-6">
                                <div className="flex flex-col md:flex-row gap-6 items-start md:items-center">
                                    <div className="flex-1">
                                        <span className="text-xs font-bold text-zinc-500 uppercase tracking-widest mb-2 block">Selección Recomendada</span>
                                        <div className="text-3xl font-bold text-emerald-500 tracking-tight">
                                            {analysisData.prediction}
                                        </div>
                                    </div>
                                    <div className="w-full md:w-2/3">
                                        <p className="text-zinc-400 text-sm leading-relaxed italic">
                                            &quot;{analysisData.reasoning}&quot;
                                        </p>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                )}

                {/* 5. LISTA DE LESIONES */}
                {match.injuries && (
                    <div className="border border-zinc-800 rounded-xl p-6">
                        <InjuryList injuriesJson={match.injuries} />
                    </div>
                )}
            </div>

            {/* COLUMNA DERECHA: ACCIONES Y DETALLES TÉCNICOS */}
            <aside className="space-y-6">

                {/* CAJA DE ACCIONES (ANÁLISIS Y APUESTA) */}
                <div className="border border-zinc-800 rounded-xl p-6 space-y-6">
                    {/* Botón Analizar */}
                    <div>
                        <h3 className="text-sm font-bold text-zinc-50 mb-2 flex items-center gap-2">
                            <Bot size={14} className="text-zinc-500" /> Cerebro Táctico
                        </h3>
                        <AnalyzeButton matchId={match.api_id} onAnalyzeComplete={fetchMatch} />
                    </div>

                    <div className="border-t border-zinc-800 pt-6">
                        <h3 className="text-sm font-bold text-zinc-50 mb-2 flex items-center gap-2">
                            <Wallet size={14} className="text-zinc-500" /> Ejecución
                        </h3>
                        {analysisData ? (
                            <BetButton
                                matchApiId={match.api_id}
                                selection={analysisData.prediction}
                                odds={getOddsValue(analysisData.selection_code, match.odds_data)}
                                aiProbability={analysisData.win_probability || 0}
                            />
                        ) : (
                            <button disabled className="w-full flex items-center justify-center gap-2 py-3 bg-transparent text-zinc-600 font-bold rounded cursor-not-allowed text-xs uppercase tracking-widest border border-zinc-800">
                                <Lock size={12} /> Requiere Análisis
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
