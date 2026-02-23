import React from 'react';

interface ApiStatusProps {
  match: any;
}

export default function ApiStatusList({ match }: ApiStatusProps) {
  
  // Función para verificar si un campo JSON tiene datos reales
  const hasData = (field: any) => {
    if (!field) return false;
    if (Array.isArray(field) && field.length === 0) return false; // Array vacío no cuenta como dato útil aquí
    if (typeof field === 'object' && Object.keys(field).length === 0) return false;
    
    // Si viene como string JSON
    if (typeof field === 'string') {
        if (field === 'null' || field === '{}' || field === '[]') return false;
        try {
            const parsed = JSON.parse(field);
            if (Array.isArray(parsed) && parsed.length === 0) return false;
            if (!parsed) return false;
            return true;
        } catch { return false; }
    }
    return true;
  };

  // Lógica de disponibilidad según tu Worker actual (main.py)
  // El Worker descarga: Fixtures, Odds, Injuries, Predictions.
  const coverage = [
    { name: "Countries", status: true }, // Viene en Fixture
    { name: "Seasons", status: true },   // Viene en Fixture
    { name: "Leagues", status: true },   // Viene en Fixture
    { name: "Teams", status: true },     // Viene en Fixture
    { name: "Fixtures", status: true },  // Es la base
    { name: "Livescore", status: match.status !== 'NS' },
    
    // Datos Específicos que descargamos
    { name: "Pre-match Odds", status: hasData(match.odds_data) },
    { name: "Injuries", status: hasData(match.injuries) },
    { name: "Sidelined", status: hasData(match.injuries) }, // Alias de Injuries
    { name: "Predictions", status: hasData(match.api_prediction) },
    { name: "Head 2 Head", status: hasData(match.api_prediction) }, // H2H viene dentro de Predictions
    
    // Datos que AÚN NO descargamos (Para futuras fases)
    { name: "Line Ups", status: hasData(match.lineups) }, // Actualmente {}
    { name: "Statistics", status: false },
    { name: "Events", status: false },
    { name: "Standings", status: false },
    { name: "Top Scorers", status: false },
    { name: "Players", status: false },
    { name: "Transfers", status: false },
    { name: "Trophies", status: false },
    { name: "In-play Odds", status: false },
  ];

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-lg">
      <div className="flex items-center justify-between mb-4 border-b border-slate-800 pb-3">
        <h3 className="text-xs font-bold text-slate-400 uppercase tracking-widest flex items-center gap-2">
          📡 Cobertura API
        </h3>
        <span className="text-[10px] bg-slate-800 text-slate-500 px-2 py-1 rounded">
            Plan Free Limit
        </span>
      </div>

      <div className="grid grid-cols-2 gap-y-2 gap-x-4">
        {coverage.map((item, idx) => (
          <div key={idx} className="flex items-center justify-between group">
            <span className={`text-[10px] font-medium transition-colors ${item.status ? 'text-slate-300' : 'text-slate-600 group-hover:text-slate-500'}`}>
                {item.name}
            </span>
            {item.status ? (
                <span className="text-[10px] text-emerald-500 bg-emerald-500/10 px-1.5 rounded border border-emerald-500/20">
                    GET
                </span>
            ) : (
                <span className="text-[10px] text-slate-700 bg-slate-800/50 px-1.5 rounded">
                    ---
                </span>
            )}
          </div>
        ))}
      </div>
      
      <div className="mt-4 pt-3 border-t border-slate-800 text-center">
        <p className="text-[9px] text-slate-600">
            Datos sincronizados desde API-Football v3
        </p>
      </div>
    </div>
  );
}