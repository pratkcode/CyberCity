import { EmptyState } from "../../components/EmptyState";
import { Panel } from "../../components/Panel";
import { useAsync } from "../../hooks/useAsync";
import { simulationApi } from "../../services/simulationApi";
import type { ServiceOverview } from "../../types/city";
import type { Topology } from "../../types/network";
import { ConnectionDetails } from "./ConnectionDetails";
import { DeviceDetails, type PathEndpoint } from "./DeviceDetails";
import type { NameLookup } from "./names";
import { ServiceDetails } from "./ServiceDetails";

export type Selection =
  | { kind: "device"; id: string }
  | { kind: "connection"; id: string }
  | { kind: "service"; id: string };

interface SelectionPanelProps {
  selection: Selection | null;
  topology: Topology;
  services: ServiceOverview[];
  names: NameLookup;
  onSelect: (selection: Selection) => void;
  onSetEndpoint: (endpoint: PathEndpoint, deviceId: string) => void;
}

const TITLES = { device: "Device Details", connection: "Link Details", service: "Service Health" };

export function SelectionPanel({ selection, topology, services, names, onSelect, onSetEndpoint }: SelectionPanelProps) {
  // Device details come from the backend (reachability, dependent services).
  const deviceId = selection?.kind === "device" ? selection.id : null;
  const device = useAsync(deviceId, () => simulationApi.getDeviceDetail(deviceId!));

  const selectDevice = (id: string) => onSelect({ kind: "device", id });
  const selectService = (id: string) => onSelect({ kind: "service", id });

  let body;
  if (!selection) {
    body = (
      <EmptyState title="Nothing selected">
        Select a device or link on the map, or a service from the list.
      </EmptyState>
    );
  } else if (selection.kind === "device") {
    body =
      device.status === "ready" ? (
        <DeviceDetails
          detail={device.data}
          names={names}
          onSelectDevice={selectDevice}
          onSelectService={selectService}
          onSetEndpoint={onSetEndpoint}
        />
      ) : device.status === "error" ? (
        <EmptyState title="Couldn't load device">{device.error.message}</EmptyState>
      ) : (
        <EmptyState title="Loading device…" />
      );
  } else if (selection.kind === "connection") {
    const connection = topology.connections.find((c) => c.id === selection.id);
    body = connection ? (
      <ConnectionDetails connection={connection} names={names} onSelectDevice={selectDevice} />
    ) : (
      <EmptyState title="Link not found" />
    );
  } else {
    const overview = services.find((s) => s.service.id === selection.id);
    body = overview ? (
      <ServiceDetails overview={overview} names={names} onSelectDevice={selectDevice} />
    ) : (
      <EmptyState title="Service not found" />
    );
  }

  return (
    <Panel title={selection ? TITLES[selection.kind] : "Details"} source={selection ? "sample" : undefined} className="selection-panel">
      {body}
    </Panel>
  );
}
