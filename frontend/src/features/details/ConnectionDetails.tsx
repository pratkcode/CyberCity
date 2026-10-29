import { KeyValueList } from "../../components/KeyValueList";
import type { NetworkConnection } from "../../types/network";
import { formatBandwidth, formatLabel } from "../../utils/format";
import type { NameLookup } from "./names";

interface ConnectionDetailsProps {
  connection: NetworkConnection;
  names: NameLookup;
  onSelectDevice?: (deviceId: string) => void;
}

export function ConnectionDetails({ connection, names, onSelectDevice }: ConnectionDetailsProps) {
  const endpoint = (id: string) => (
    <button type="button" className="link-list__peer" onClick={() => onSelectDevice?.(id)}>
      {names.device(id)}
    </button>
  );

  return (
    <div className="details">
      <div className="details__heading">
        <h3>
          {names.device(connection.source_id)} ↔ {names.device(connection.target_id)}
        </h3>
        <code className="mono">{connection.id}</code>
      </div>
      <KeyValueList
        items={[
          { label: "Endpoint A", value: endpoint(connection.source_id) },
          { label: "Endpoint B", value: endpoint(connection.target_id) },
          { label: "Link type", value: formatLabel(connection.link_type) },
          { label: "Bandwidth", value: formatBandwidth(connection.bandwidth_mbps) },
          { label: "Latency", value: `${connection.latency_ms} ms` },
          { label: "Encrypted", value: connection.encrypted ? "Yes" : "No" },
          {
            label: "Traffic",
            value: connection.traffic_permitted ? (
              <span className="text-ok">Permitted</span>
            ) : (
              <span className="text-danger">Not permitted</span>
            ),
          },
        ]}
      />
      {connection.description && <p className="details__note">{connection.description}</p>}
      <p className="small text-faint">
        Configured link properties only. No traffic is measured or generated.
      </p>
    </div>
  );
}
