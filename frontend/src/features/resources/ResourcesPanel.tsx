import { DataBadge } from "../../components/DataBadge";
import { KeyValueList } from "../../components/KeyValueList";
import { Panel } from "../../components/Panel";
import type { SimulationConfig } from "../../types/simulation";
import { formatCredits } from "../../utils/format";

/** Security resources. Only the starting budget exists so far, and it comes straight from config. */
export function ResourcesPanel({ config }: { config: SimulationConfig }) {
  const notYet = <span className="text-muted">Not tracked yet</span>;

  return (
    <Panel title="Security Resources" className="resources-panel">
      <KeyValueList
        items={[
          {
            label: "Starting budget",
            value: (
              <span className="kv-with-badge">
                <span className="mono">{formatCredits(config.starting_budget)}</span>
                <DataBadge source="config" />
              </span>
            ),
          },
          { label: "Analysts", value: notYet },
          { label: "Defense tools", value: notYet },
        ]}
      />
      <p className="panel__note">
        <DataBadge source="placeholder" /> Staffing, tooling and spending arrive in a later phase.
      </p>
    </Panel>
  );
}
