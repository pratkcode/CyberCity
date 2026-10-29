import { KeyValueList } from "../../components/KeyValueList";
import { HealthTag } from "../../components/StatusTag";
import type { ServiceOverview } from "../../types/city";
import { formatLabel } from "../../utils/format";
import type { NameLookup } from "./names";

interface ServiceDetailsProps {
  overview: ServiceOverview;
  names: NameLookup;
  onSelectDevice?: (deviceId: string) => void;
}

export function ServiceDetails({ overview, names, onSelectDevice }: ServiceDetailsProps) {
  const { service, organization, health } = overview;
  const device = (id: string) => (
    <button type="button" className="link-list__peer" onClick={() => onSelectDevice?.(id)}>
      {names.device(id)}
    </button>
  );

  return (
    <div className="details">
      <div className="details__heading">
        <h3>{service.name}</h3>
        <span className="text-muted small">{organization.name}</span>
      </div>
      <KeyValueList
        items={[
          { label: "Health", value: <HealthTag status={health.status} /> },
          { label: "Sector", value: formatLabel(organization.sector) },
          { label: "Criticality", value: <span className={`tag tag--${service.criticality}`}>{formatLabel(service.criticality)}</span> },
          { label: "Entry point", value: device(service.entry_point_id) },
        ]}
      />
      <p className="details__note">{health.summary}</p>

      <h4 className="subheading">Dependencies ({health.dependencies.length})</h4>
      <ul className="dependency-list">
        {health.dependencies.map((dep) => (
          <li key={`${dep.client_id}-${dep.device_id}-${dep.protocol}`} className={dep.ok ? "" : "is-failing"}>
            <div className="dependency-list__row">
              <span className={dep.ok ? "check-ok" : "check-fail"} aria-label={dep.ok ? "Available" : "Unavailable"}>
                {dep.ok ? "✓" : "✕"}
              </span>
              {device(dep.device_id)}
              <span className="chip mono">{dep.protocol}</span>
              {!dep.required && <span className="chip">optional</span>}
            </div>
            <div className="dependency-list__meta">
              {dep.role} · from {names.device(dep.client_id)}
            </div>
            {!dep.ok && <div className="dependency-list__reason">{dep.reason}</div>}
          </li>
        ))}
      </ul>
      <p className="small text-faint">
        Health uses a simplified model: device status, configured services, zone policy and reachability.
      </p>
    </div>
  );
}
