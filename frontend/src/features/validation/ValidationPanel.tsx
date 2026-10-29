import { Panel } from "../../components/Panel";
import type { ValidationReport } from "../../types/network";

interface ValidationPanelProps {
  report: ValidationReport;
  isDevice: (id: string) => boolean;
  onSelectDevice: (deviceId: string) => void;
}

export function ValidationPanel({ report, isDevice, onSelectDevice }: ValidationPanelProps) {
  return (
    <Panel title="Network Validation" className="validation-panel">
      <p className={`validation-summary ${report.valid ? "text-ok" : "text-danger"}`}>
        {report.valid ? "Valid" : "Invalid"} · {report.error_count} errors · {report.warning_count} warnings
      </p>
      {report.issues.length > 0 && (
        <ul className="issue-list">
          {report.issues.map((issue) => {
            const deviceId = issue.subject_ids.find(isDevice);
            return (
              <li key={`${issue.code}-${issue.subject_ids.join(",")}`}>
                <span className={`tag tag--issue-${issue.severity}`}>{issue.severity}</span>
                {deviceId ? (
                  <button type="button" className="link-list__peer" onClick={() => onSelectDevice(deviceId)}>
                    {issue.message}
                  </button>
                ) : (
                  <span>{issue.message}</span>
                )}
              </li>
            );
          })}
        </ul>
      )}
    </Panel>
  );
}
