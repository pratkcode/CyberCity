import type { ElementDefinition } from "cytoscape";

import type { NetworkSnapshot } from "../../types/simulation";

/**
 * Convert the API snapshot into Cytoscape elements.
 * Kept as a pure function so it can be unit-tested without a canvas.
 */
export function toCytoscapeElements(network: NetworkSnapshot): ElementDefinition[] {
  const nodes: ElementDefinition[] = network.devices.map((device) => ({
    group: "nodes",
    data: {
      id: device.id,
      label: device.name,
      deviceType: device.device_type,
      criticality: device.criticality,
      zone: device.zone,
    },
    classes: device.online ? "" : "offline",
  }));

  const edges: ElementDefinition[] = network.connections.map((conn) => ({
    group: "edges",
    data: {
      id: conn.id,
      source: conn.source_id,
      target: conn.target_id,
      linkType: conn.link_type,
    },
    classes: conn.encrypted ? "encrypted" : "",
  }));

  return [...nodes, ...edges];
}

/** Routers sit at the internet edge, so the layout grows the tree downward from them. */
export const LAYOUT_ROOT_TYPES = ["router"] as const;
