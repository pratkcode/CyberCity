import { KeyValueList } from "../../components/KeyValueList";
import { StatusTag } from "../../components/StatusTag";
import type { DeviceDetail } from "../../types/network";
import { formatBandwidth, formatLabel } from "../../utils/format";
import type { NameLookup } from "./names";
import { categoryProperties } from "./deviceProperties";

export type PathEndpoint = "source" | "target";

interface DeviceDetailsProps {
  detail: DeviceDetail;
  names: NameLookup;
  onSelectDevice?: (deviceId: string) => void;
  onSelectService?: (serviceId: string) => void;
  onSetEndpoint?: (endpoint: PathEndpoint, deviceId: string) => void;
}

export function DeviceDetails({ detail, names, onSelectDevice, onSelectService, onSetEndpoint }: DeviceDetailsProps) {
  const { device, zone, links, reachable_device_ids, isolated, dependent_service_ids } = detail;
  const openVulns = device.vulnerabilities.filter((v) => !v.remediated);

  return (
    <div className="details">
      <div className="details__heading">
        <h3>{device.name}</h3>
        <code className="mono">{device.id}</code>
      </div>

      {onSetEndpoint && (
        <div className="details__actions">
          <button type="button" className="ghost-button" onClick={() => onSetEndpoint("source", device.id)}>
            Set as source
          </button>
          <button type="button" className="ghost-button" onClick={() => onSetEndpoint("target", device.id)}>
            Set as target
          </button>
        </div>
      )}

      <KeyValueList
        items={[
          { label: "Category", value: formatLabel(device.device_type) },
          { label: "Zone", value: zone.name },
          {
            label: "Status",
            value: (
              <span className="inline-tags">
                <StatusTag status={device.status} />
                {isolated && <span className="tag tag--isolated">Isolated</span>}
              </span>
            ),
          },
          { label: "Criticality", value: <span className={`tag tag--${device.criticality}`}>{formatLabel(device.criticality)}</span> },
          {
            label: "Patch",
            value: `${formatLabel(device.patch.level)} · ${device.patch.days_since_patch} days (seeded)`,
          },
          ...categoryProperties(device, names.zone),
          {
            label: "Reachable",
            value: isolated || device.status === "offline"
              ? `${reachable_device_ids.length} devices`
              : `${reachable_device_ids.length} devices over usable links`,
          },
        ]}
      />

      <h4 className="subheading">Configured services</h4>
      {device.configured_services.length === 0 ? (
        <p className="text-muted small">None configured.</p>
      ) : (
        <div className="chip-row">
          {device.configured_services.map((s) => (
            <span key={s.port} className="chip mono">
              {s.protocol}:{s.port}
            </span>
          ))}
        </div>
      )}

      <h4 className="subheading">Modeled vulnerabilities ({openVulns.length} open)</h4>
      {device.vulnerabilities.length === 0 ? (
        <p className="text-muted small">None modeled.</p>
      ) : (
        <ul className="plain-list">
          {device.vulnerabilities.map((v) => (
            <li key={v.id} className={v.remediated ? "text-muted" : undefined}>
              <span className={`tag tag--${v.severity}`}>{formatLabel(v.severity)}</span> {v.title}{" "}
              <span className="small text-muted mono">
                {v.id}
                {v.remediated ? " · remediated" : ""}
              </span>
            </li>
          ))}
        </ul>
      )}
      <p className="small text-faint">Fictional records for the simulation. Not real CVEs.</p>

      <h4 className="subheading">Links ({links.length})</h4>
      <ul className="link-list">
        {links.map(({ connection, neighbor_id }) => (
          <li key={connection.id}>
            <button type="button" className="link-list__peer" onClick={() => onSelectDevice?.(neighbor_id)}>
              {names.device(neighbor_id)}
            </button>
            <span className="link-list__meta">
              {formatLabel(connection.link_type)} · {formatBandwidth(connection.bandwidth_mbps)} ·{" "}
              {connection.latency_ms} ms
              {connection.encrypted ? " · encrypted" : ""}
              {connection.traffic_permitted ? "" : " · traffic not permitted"}
            </span>
          </li>
        ))}
      </ul>

      <h4 className="subheading">Supports city services</h4>
      {dependent_service_ids.length === 0 ? (
        <p className="text-muted small">No city service depends on this device.</p>
      ) : (
        <ul className="plain-list">
          {dependent_service_ids.map((id) => (
            <li key={id}>
              <button type="button" className="link-list__peer" onClick={() => onSelectService?.(id)}>
                {names.service(id)}
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
