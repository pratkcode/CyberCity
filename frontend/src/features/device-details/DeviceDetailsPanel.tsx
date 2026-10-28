import { EmptyState } from "../../components/EmptyState";
import { KeyValueList } from "../../components/KeyValueList";
import { Panel } from "../../components/Panel";
import { formatBandwidth, formatLabel } from "../../utils/format";
import type { DeviceContext } from "./deviceContext";

interface DeviceDetailsPanelProps {
  context: DeviceContext | null;
  onSelectDevice?: (deviceId: string) => void;
}

export function DeviceDetailsPanel({ context, onSelectDevice }: DeviceDetailsPanelProps) {
  if (!context) {
    return (
      <Panel title="Device Details" className="device-details">
        <EmptyState title="No device selected">
          Select a node on the network map to inspect its properties.
        </EmptyState>
      </Panel>
    );
  }

  const { device, links, dependentServices } = context;

  return (
    <Panel title="Device Details" source="sample" className="device-details">
      <div className="device-details__heading">
        <h3>{device.name}</h3>
        <code className="mono">{device.id}</code>
      </div>

      <KeyValueList
        items={[
          { label: "Type", value: formatLabel(device.device_type) },
          { label: "Zone", value: <code className="mono">{device.zone}</code> },
          {
            label: "Criticality",
            value: (
              <span className={`tag tag--${device.criticality}`}>
                {formatLabel(device.criticality)}
              </span>
            ),
          },
          {
            label: "State",
            value: (
              <span className={device.online ? "text-ok" : "text-muted"}>
                {device.online ? "Online" : "Offline"}
              </span>
            ),
          },
          {
            label: "Patch age",
            value: `${device.patch_age_days} days (seeded)`,
          },
        ]}
      />

      <h4 className="subheading">Connections ({links.length})</h4>
      <ul className="link-list">
        {links.map(({ connection, peer }) => (
          <li key={connection.id}>
            <button
              type="button"
              className="link-list__peer"
              onClick={() => onSelectDevice?.(peer.id)}
            >
              {peer.name}
            </button>
            <span className="link-list__meta">
              {formatLabel(connection.link_type)} · {formatBandwidth(connection.bandwidth_mbps)}
              {connection.encrypted ? " · encrypted" : ""}
            </span>
          </li>
        ))}
      </ul>

      <h4 className="subheading">Supports city services</h4>
      {dependentServices.length === 0 ? (
        <p className="text-muted small">No city service depends directly on this device.</p>
      ) : (
        <ul className="plain-list">
          {dependentServices.map((service) => (
            <li key={service.id}>{service.name}</li>
          ))}
        </ul>
      )}
    </Panel>
  );
}
