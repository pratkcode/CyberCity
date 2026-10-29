import type { ElementDefinition } from "cytoscape";

import type { NetworkConnection, Topology } from "../../types/network";
import { formatBandwidth } from "../../utils/format";
import { CELL, computeZoneLayout, type Point } from "./zoneLayout";

export const zoneNodeId = (zoneId: string) => `zone:${zoneId}`;

/** Visual state of a device on the map. */
export type DeviceVisualState = "operational" | "degraded" | "isolated" | "unavailable";

export function deviceVisualState(
  status: "online" | "degraded" | "offline",
  isolated: boolean,
): DeviceVisualState {
  if (status === "offline") return "unavailable";
  if (isolated) return "isolated";
  return status === "degraded" ? "degraded" : "operational";
}

export function connectionLabel(connection: NetworkConnection): string {
  return `${formatBandwidth(connection.bandwidth_mbps)} · ${connection.latency_ms} ms`;
}

/**
 * Convert a topology into Cytoscape elements: zones become compound parent
 * nodes, devices are children with preset positions, and links are edges.
 * A pure function, so it can be unit-tested without a canvas.
 */
export function toCytoscapeElements(topology: Topology): ElementDefinition[] {
  const positions = computeZoneLayout(topology);
  const isolated = new Set(topology.isolated_device_ids);

  const zones: ElementDefinition[] = topology.zones.map((zone) => ({
    group: "nodes",
    data: { id: zoneNodeId(zone.id), label: zone.name, kind: zone.kind, isZone: true },
    classes: "zone",
    selectable: false,
  }));

  const devices: ElementDefinition[] = topology.devices.map((device) => ({
    group: "nodes",
    data: {
      id: device.id,
      parent: zoneNodeId(device.zone_id),
      label: device.name,
      deviceType: device.device_type,
      criticality: device.criticality,
    },
    position: positions.get(device.id) ?? { x: 0, y: 0 },
    classes: `device state-${deviceVisualState(device.status, isolated.has(device.id))}`,
  }));

  const edges: ElementDefinition[] = topology.connections.map((conn) => {
    const bend = arcBend(positions.get(conn.source_id), positions.get(conn.target_id));
    return {
      group: "edges",
      data: {
        id: conn.id,
        source: conn.source_id,
        target: conn.target_id,
        linkType: conn.link_type,
        // log10 scale: 100 Mbps → 2, 10 Gbps → 4. Drives edge width.
        capacity: Math.log10(conn.bandwidth_mbps),
        label: connectionLabel(conn),
        bend,
      },
      classes: [
        conn.encrypted ? "encrypted" : "",
        conn.traffic_permitted ? "" : "blocked",
        bend ? "arced" : "",
      ]
        .filter(Boolean)
        .join(" "),
    };
  });

  return [...zones, ...devices, ...edges];
}

/**
 * Long links between devices on the same grid row would be drawn straight
 * through every device in between, which looks like the link passes through
 * them. Those links get an upward arc instead. Returns the Cytoscape
 * control-point distance, or 0 for a straight line.
 */
export function arcBend(a?: Point, b?: Point): number {
  if (!a || !b) return 0;
  const dx = b.x - a.x;
  if (Math.abs(b.y - a.y) > CELL.height / 2 || Math.abs(dx) < CELL.width * 1.5) return 0;
  const magnitude = 30 + Math.abs(dx) * 0.12;
  // Distances are measured perpendicular to source→target, so flip by direction to always arc upward.
  return dx > 0 ? -magnitude : magnitude;
}
