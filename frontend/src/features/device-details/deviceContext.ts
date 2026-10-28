import type {
  CityService,
  NetworkConnection,
  NetworkDevice,
  NetworkSnapshot,
} from "../../types/simulation";

export interface DeviceLink {
  connection: NetworkConnection;
  peer: NetworkDevice;
}

export interface DeviceContext {
  device: NetworkDevice;
  links: DeviceLink[];
  dependentServices: CityService[];
}

/** Gather a device and everything directly related to it, for the details panel. */
export function getDeviceContext(
  network: NetworkSnapshot,
  services: CityService[],
  deviceId: string,
): DeviceContext | null {
  const byId = new Map(network.devices.map((d) => [d.id, d]));
  const device = byId.get(deviceId);
  if (!device) return null;

  const links: DeviceLink[] = [];
  for (const connection of network.connections) {
    const peerId =
      connection.source_id === deviceId
        ? connection.target_id
        : connection.target_id === deviceId
          ? connection.source_id
          : null;
    const peer = peerId ? byId.get(peerId) : undefined;
    if (peer) links.push({ connection, peer });
  }

  const dependentServices = services.filter((s) => s.dependency_ids.includes(deviceId));
  return { device, links, dependentServices };
}
