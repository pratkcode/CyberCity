import type { SimulationSummary } from "../../types/simulation";
import { formatLabel, formatSimulatedTime } from "../../utils/format";
import { DataBadge } from "../DataBadge";

export function TopBar({ summary }: { summary: SimulationSummary | null }) {
  return (
    <header className="topbar">
      <div className="topbar__title">
        <h1>{summary?.config.city_name ?? "CyberCity"} Command Center</h1>
      </div>

      <div className="topbar__stats" aria-label="Simulation status">
        <div className="topbar__stat">
          <span className="topbar__label">Sim time</span>
          <span className="topbar__value mono">
            {summary ? formatSimulatedTime(summary.simulated_minutes) : "—"}
          </span>
        </div>
        <div className="topbar__stat">
          <span className="topbar__label">Tick</span>
          <span className="topbar__value mono">{summary?.tick ?? "—"}</span>
        </div>
        <div className="topbar__stat">
          <span className="topbar__label">Seed</span>
          <span className="topbar__value mono">{summary?.config.seed ?? "—"}</span>
        </div>
        <div className="topbar__stat">
          <span className="topbar__label">Difficulty</span>
          <span className="topbar__value">
            {summary ? formatLabel(summary.config.difficulty) : "—"}
          </span>
        </div>
        <div className="topbar__clock-note">
          <DataBadge source="placeholder" />
          <span>Clock paused · time advancement arrives in a later phase</span>
        </div>
      </div>
    </header>
  );
}
