// Mirrors backend/app/models/simulation.py plus shared API shapes.

export type Difficulty = "training" | "standard" | "challenging";

export interface SimulationConfig {
  seed: number;
  city_name: string;
  difficulty: Difficulty;
  starting_budget: number;
  tick_minutes: number;
}

export interface SimulationSummary {
  config: SimulationConfig;
  tick: number;
  simulated_minutes: number;
  zone_count: number;
  device_count: number;
  connection_count: number;
  organization_count: number;
  service_count: number;
}

export interface HealthResponse {
  status: string;
  version: string;
}

export interface ApiErrorDetail {
  location?: (string | number)[];
  message: string;
  type?: string;
  code?: string;
}

export interface ApiErrorBody {
  error: {
    code: string;
    message: string;
    details: ApiErrorDetail[];
  };
}
