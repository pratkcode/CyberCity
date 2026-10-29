import type { ServiceHealthStatus } from "../types/city";
import type { OperationalStatus } from "../types/network";
import { formatLabel } from "../utils/format";

export function StatusTag({ status }: { status: OperationalStatus }) {
  return <span className={`tag tag--status-${status}`}>{formatLabel(status)}</span>;
}

export function HealthTag({ status }: { status: ServiceHealthStatus }) {
  return <span className={`tag tag--health-${status}`}>{formatLabel(status)}</span>;
}
