// apps/web/src/types/match.ts

export interface Match {
  id: number;
  api_id: string;
  date: string;
  league_name: string;
  home_team: string;
  away_team: string;
  status: string;
  pro_data?: {
    referee?: string;
    injuries?: string[];
    lineups_available?: boolean;
  };
  odds_data?: {
    "1x2"?: { "1": number; "X": number; "2": number };
  };
  ai_analysis?: {
    summary: string;
    generated_at?: string;
    picks: AiPick[];
  };
}

export interface AiPick {
  market: string;
  selection: string;
  probability: number;
  confidence: number;
  risk_level: "Low" | "Medium" | "High" | string;
  reasoning: string;
}