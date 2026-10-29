import type { ReactNode } from "react";

import type { SimulationSummary } from "../../types/simulation";
import { formatCredits, formatLabel, formatSimulatedTime } from "../../utils/format";
import { DataBadge } from "../DataBadge";

function Stat({ label, value, mono = false }: { label: string; value: ReactNode; mono?: boolean }) {
  return (
    <div className="topbar__stat">
      <span className="topbar__label">{label}</span>
      <span className={`topbar__value ${mono ? "mono" : ""}`}>{value}</span>
    </div>
  );
}

export function TopBar({ summary }: { summary: SimulationSummary | null }) {
  const dash = "—";
  return (
    <header className="topbar">
      <div className="topbar__title">
        <h1>{summary?.config.city_name ?? "CyberCity"} Command Center</h1>
        <div className="topbar__placeholders">
          <DataBadge source="placeholder" />
          <span>Clock paused · alert feed not active · arrives in a later phase</span>
        </div>
      </div>

      <div className="topbar__stats" aria-label="Simulation status">
        <Stat label="Sim time" value={summary ? formatSimulatedTime(summary.simulated_minutes) : dash} mono />
        <Stat label="Seed" value={summary?.config.seed ?? dash} mono />
        <Stat label="Difficulty" value={summary ? formatLabel(summary.config.difficulty) : dash} />
        <Stat
          label="Network"
          value={summary ? `${summary.device_count} devices · ${summary.zone_count} zones` : dash}
        />
        <Stat
          label="Budget (config)"
          value={summary ? formatCredits(summary.config.starting_budget) : dash}
          mono
        />
      </div>
    </header>
  );
}
