import React from 'react';
import { Stethoscope } from 'lucide-react';

interface Injury {
  player: {
    id: number;
    name: string;
    photo?: string;
    type?: string;     // Tipo de lesión
    reason?: string;   // Razón (ej: "Knee Injury")
  };
  team: {
    id: number;
    name: string;
    logo: string;
  };
  fixture: {
    id: number;
    date: string;
  };
}

interface InjuryListProps {
  injuriesJson: any; // Recibe el JSON crudo o parseado
}

export default function InjuryList({ injuriesJson }: InjuryListProps) {
  if (!injuriesJson) return null;

  let injuries: Injury[] = [];

  // Parseo seguro del JSON
  try {
    if (typeof injuriesJson === 'string') {
      // A veces la IA o la DB devuelve strings "None" o vacíos
      if (injuriesJson === "None" || injuriesJson === "[]") return null;
      injuries = JSON.parse(injuriesJson);
    } else if (Array.isArray(injuriesJson)) {
      injuries = injuriesJson;
    }

    // Si viene en formato wrapper 'response' de API-Football
    if (!Array.isArray(injuries) && (injuries as any).response) {
        injuries = (injuries as any).response;
    }
  } catch (e) {
    console.error("Error parseando lesiones:", e);
    return null;
  }

  if (injuries.length === 0) return null;

  return (
    <div>
      <h4 className="text-xs font-bold text-zinc-400 uppercase tracking-widest mb-3 flex items-center gap-2">
        <Stethoscope size={13} /> Reporte Médico / Bajas
      </h4>
      <div className="space-y-2">
        {injuries.map((item, idx) => (
          <div key={idx} className="flex items-center gap-3 text-sm border-b border-zinc-800 last:border-0 pb-2 last:pb-0">
            {/* Foto del jugador (opcional) */}
            {item.player.photo && (
                <img
                    src={item.player.photo}
                    alt={item.player.name}
                    className="w-6 h-6 rounded-full object-cover bg-zinc-800"
                />
            )}

            <div className="flex-1">
                <span className="text-zinc-200 font-semibold">{item.player.name}</span>
                <span className="text-zinc-500 text-xs ml-2">({item.team.name})</span>
            </div>

            <div className="text-right">
                <span className="text-red-600 text-xs">
                    {item.player.reason || item.player.type || "Baja"}
                </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
