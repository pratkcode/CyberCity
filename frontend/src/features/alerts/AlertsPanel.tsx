import { EmptyState } from "../../components/EmptyState";
import { Panel } from "../../components/Panel";

/**
 * Placeholder for the security alert feed. The backend has a SecurityEvent
 * model, but no events are generated in Phase 1, so no alerts are shown.
 */
export function AlertsPanel() {
  return (
    <Panel title="Security Alerts" source="placeholder" className="alerts-panel">
      <EmptyState title="Alert feed not active">
        Simulated incidents and investigations arrive in a later phase. No alerts are shown until
        the simulation generates them.
      </EmptyState>
    </Panel>
  );
}
