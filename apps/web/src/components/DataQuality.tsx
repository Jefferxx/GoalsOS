import React from 'react';

interface DataQualityProps {
  match: any; // Usamos any para flexibilidad con los campos JSON del backend
}

export default function DataQuality({ match }: DataQualityProps) {
  
  // Función auxiliar para verificar si hay datos reales
  const hasData = (field: any) => {
    if (!field) return false;
    if (field === 'null') return false;
    if (field === '{}') return false;
    if (field === '[]') return true; // Array vacío de lesiones cuenta como "Datos revisados: 0 lesiones"
    try {
        // Si es un string JSON, intentamos ver si tiene contenido
        if (typeof field === 'string') {
            const parsed = JSON.parse(field);
            // Si es un objeto vacío o null
            if (!parsed) return false;
            if (Object.keys(parsed).length === 0) return false;
        }
        return true;
    } catch (e) {
        return false;
    }
  };

  const status = {
    odds: hasData(match.odds_data),
    injuries: hasData(match.injuries),
    prediction: hasData(match.api_prediction), // Contiene Forma y H2H
    analysis: hasData(match.ai_analysis)
  };

  // Calculamos un porcentaje de "Integridad"
  const totalPoints = 3; // Odds + Injuries + Prediction (AI Analysis es consecuencia)
  const currentPoints = (status.odds ? 1 : 0) + (status.injuries ? 1 : 0) + (status.prediction ? 1 : 0);
  const integrity = Math.round((currentPoints / totalPoints) * 100);

  const getBadgeColor = (active: boolean) => 
    active 
      ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20" 
      : "bg-slate-800 text-slate-500 border-slate-700 opacity-50 grayscale";

  return (
    <div className="bg-slate-900/50 border border-slate-800 rounded-xl p-4 mb-6 backdrop-blur-sm">
      <div className="flex justify-between items-center mb-3">
        <h3 className="text-xs font-bold text-slate-400 uppercase tracking-widest flex items-center gap-2">
          📡 Fuentes de Inteligencia
        </h3>
        <div className={`text-[10px] px-2 py-0.5 rounded-full font-bold border ${
            integrity === 100 ? 'bg-emerald-500 text-slate-950 border-emerald-400' :
            integrity >= 66 ? 'bg-yellow-500 text-slate-950 border-yellow-400' :
            'bg-rose-500 text-white border-rose-400'
        }`}>
            CALIDAD DATOS: {integrity}%
        </div>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
        {/* 1. CUOTAS */}
        <div className={`flex items-center gap-2 px-3 py-2 rounded-lg border text-xs font-medium transition-all ${getBadgeColor(status.odds)}`}>
            <span>{status.odds ? "✅" : "⚠️"}</span>
            <div className="flex flex-col">
                <span>Mercado / Cuotas</span>
                <span className="text-[9px] opacity-70">{status.odds ? "Sincronizado" : "No disponible"}</span>
            </div>
        </div>

        {/* 2. REPORTE MÉDICO */}
        <div className={`flex items-center gap-2 px-3 py-2 rounded-lg border text-xs font-medium transition-all ${getBadgeColor(status.injuries)}`}>
            <span>{status.injuries ? "✅" : "⚠️"}</span>
            <div className="flex flex-col">
                <span>Reporte Médico</span>
                <span className="text-[9px] opacity-70">{status.injuries ? "Escaneado" : "Sin reporte"}</span>
            </div>
        </div>

        {/* 3. FORMA & H2H (API PREDICTION) */}
        <div className={`flex items-center gap-2 px-3 py-2 rounded-lg border text-xs font-medium transition-all ${getBadgeColor(status.prediction)}`}>
            <span>{status.prediction ? "✅" : "⚠️"}</span>
            <div className="flex flex-col">
                <span>Contexto Táctico</span>
                <span className="text-[9px] opacity-70">{status.prediction ? "H2H + Forma" : "Datos insuficientes"}</span>
            </div>
        </div>

        {/* 4. ANÁLISIS IA */}
        <div className={`flex items-center gap-2 px-3 py-2 rounded-lg border text-xs font-medium transition-all ${
            status.analysis ? "bg-blue-500/10 text-blue-400 border-blue-500/20 shadow-[0_0_10px_rgba(59,130,246,0.1)]" : "bg-slate-800 text-slate-500 border-slate-700"
        }`}>
            <span>{status.analysis ? "🤖" : "💤"}</span>
            <div className="flex flex-col">
                <span>Cerebro IA</span>
                <span className="text-[9px] opacity-70">{status.analysis ? "Procesado" : "Pendiente"}</span>
            </div>
        </div>
      </div>
    </div>
  );
}