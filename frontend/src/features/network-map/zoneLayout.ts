import type { DeviceType, Topology, ZoneKind } from "../../types/network";

/**
 * Deterministic "zones as boxes" layout.
 *
 * Zones are placed in two rows: perimeter and specialized zones on top
 * (public, cloud, monitoring, critical infrastructure), and core business
 * zones below (internal, restricted). Inside a zone, devices sit in a small
 * grid with gateways (routers, firewalls, switches) first.
 *
 * A hand-rolled layout is used instead of a force-directed one so the same
 * topology always draws the same way, and the map stays readable as a city
 * map rather than a hairball.
 */

export interface Point {
  x: number;
  y: number;
}

export const CELL = { width: 120, height: 72 };
const ZONE_GAP = { x: 50, y: 58 };

const ROW_OF_KIND: Record<ZoneKind, number> = {
  public: 0,
  cloud: 0,
  monitoring: 0,
  critical_infrastructure: 0,
  internal: 1,
  restricted: 1,
};

const KIND_ORDER: ZoneKind[] = ["public", "cloud", "monitoring", "critical_infrastructure", "internal", "restricted"];

const DEVICE_ORDER: DeviceType[] = ["router", "firewall", "switch"];

function deviceRank(type: DeviceType): number {
  const index = DEVICE_ORDER.indexOf(type);
  return index === -1 ? DEVICE_ORDER.length : index;
}

/** Rows per zone grid: 1 row for up to 3 devices, 2 for up to 8, else 3. */
export function gridShape(count: number): { columns: number; rows: number } {
  const rows = count <= 3 ? 1 : count <= 8 ? 2 : 3;
  return { columns: Math.max(1, Math.ceil(count / rows)), rows };
}

export function computeZoneLayout(topology: Topology): Map<string, Point> {
  const devicesByZone = new Map<string, Topology["devices"]>();
  for (const device of topology.devices) {
    const list = devicesByZone.get(device.zone_id) ?? [];
    list.push(device);
    devicesByZone.set(device.zone_id, list);
  }

  const zones = [...topology.zones].sort((a, b) => {
    const kind = KIND_ORDER.indexOf(a.kind) - KIND_ORDER.indexOf(b.kind);
    const size = (devicesByZone.get(b.id)?.length ?? 0) - (devicesByZone.get(a.id)?.length ?? 0);
    return kind || size || a.id.localeCompare(b.id);
  });

  type Box = { zoneId: string; columns: number; rows: number; width: number; height: number };
  const rows: Box[][] = [[], []];
  for (const zone of zones) {
    const count = devicesByZone.get(zone.id)?.length ?? 0;
    const { columns, rows: gridRows } = gridShape(count);
    rows[ROW_OF_KIND[zone.kind]]!.push({
      zoneId: zone.id,
      columns,
      rows: gridRows,
      width: columns * CELL.width,
      height: gridRows * CELL.height,
    });
  }

  const rowWidth = (row: Box[]) =>
    row.reduce((sum, box) => sum + box.width, 0) + Math.max(0, row.length - 1) * ZONE_GAP.x;
  const widest = Math.max(...rows.map(rowWidth));

  const positions = new Map<string, Point>();
  let y = 0;
  for (const row of rows) {
    if (row.length === 0) continue;
    let x = (widest - rowWidth(row)) / 2; // center each row
    const rowHeight = Math.max(...row.map((b) => b.height));
    for (const box of row) {
      const devices = [...(devicesByZone.get(box.zoneId) ?? [])].sort(
        (a, b) => deviceRank(a.device_type) - deviceRank(b.device_type) || a.id.localeCompare(b.id),
      );
      devices.forEach((device, index) => {
        const column = index % box.columns;
        const gridRow = Math.floor(index / box.columns);
        positions.set(device.id, {
          x: x + column * CELL.width + CELL.width / 2,
          y: y + gridRow * CELL.height + CELL.height / 2,
        });
      });
      x += box.width + ZONE_GAP.x;
    }
    y += rowHeight + ZONE_GAP.y;
  }
  return positions;
}
