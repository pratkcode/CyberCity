import cytoscape, { type Core } from "cytoscape";
import { useEffect, useRef } from "react";

import type { Topology } from "../../types/network";
import { toCytoscapeElements, zoneNodeId } from "./networkElements";
import { networkStylesheet } from "./networkStyle";

const FIT_PADDING = 16;

/** Devices and links to emphasize, e.g. a found path or a service's dependencies. */
export interface MapHighlight {
  deviceIds: string[];
  connectionIds: string[];
}

interface NetworkMapProps {
  topology: Topology;
  selectedDeviceId: string | null;
  selectedConnectionId: string | null;
  highlight: MapHighlight | null;
  onSelectDevice: (deviceId: string | null) => void;
  onSelectConnection: (connectionId: string) => void;
}

/**
 * Thin React wrapper around a Cytoscape instance.
 *
 * Cytoscape owns its canvas, so React only provides the container. The graph
 * is built once per topology, and selection and highlight changes are applied
 * imperatively so the layout never re-runs.
 */
export function NetworkMap({
  topology,
  selectedDeviceId,
  selectedConnectionId,
  highlight,
  onSelectDevice,
  onSelectConnection,
}: NetworkMapProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const cyRef = useRef<Core | null>(null);
  const handlers = useRef({ onSelectDevice, onSelectConnection });
  useEffect(() => {
    handlers.current = { onSelectDevice, onSelectConnection };
  }, [onSelectDevice, onSelectConnection]);

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    const cy = cytoscape({
      container,
      elements: toCytoscapeElements(topology),
      style: networkStylesheet,
      layout: { name: "preset", fit: true, padding: FIT_PADDING },
      selectionType: "single",
      autoungrabify: true, // positions come from the deterministic layout
      minZoom: 0.25,
      maxZoom: 3,
      wheelSensitivity: 0.3,
    });

    cy.on("tap", "node.device", (event) => handlers.current.onSelectDevice(event.target.id()));
    cy.on("tap", "edge", (event) => handlers.current.onSelectConnection(event.target.id()));
    cy.on("tap", (event) => {
      if (event.target === cy) handlers.current.onSelectDevice(null);
    });

    const fit = () => {
      cy.resize();
      cy.fit(undefined, FIT_PADDING);
    };
    const observer = typeof ResizeObserver === "undefined" ? null : new ResizeObserver(fit);
    observer?.observe(container);
    fit();

    cyRef.current = cy;
    return () => {
      observer?.disconnect();
      cy.destroy();
      cyRef.current = null;
    };
  }, [topology]);

  // Selection
  useEffect(() => {
    const cy = cyRef.current;
    if (!cy) return;
    cy.elements().unselect();
    const id = selectedDeviceId ?? selectedConnectionId;
    if (id) cy.getElementById(id).select();
  }, [selectedDeviceId, selectedConnectionId, topology]);

  // Highlight
  useEffect(() => {
    const cy = cyRef.current;
    if (!cy) return;
    cy.batch(() => {
      cy.elements().removeClass("dimmed highlighted");
      if (!highlight) return;
      const ids = new Set([...highlight.deviceIds, ...highlight.connectionIds]);
      const zones = new Set(
        topology.devices.filter((d) => ids.has(d.id)).map((d) => zoneNodeId(d.zone_id)),
      );
      cy.elements().forEach((el) => {
        if (ids.has(el.id())) el.addClass("highlighted");
        else if (!zones.has(el.id())) el.addClass("dimmed");
      });
    });
  }, [highlight, topology]);

  return (
    <div className="network-map-wrapper">
      <div
        ref={containerRef}
        className="network-map"
        role="img"
        aria-label={`Network map: ${topology.devices.length} devices in ${topology.zones.length} zones with ${topology.connections.length} links`}
      />
      <button
        type="button"
        className="ghost-button map-fit-button"
        onClick={() => cyRef.current?.fit(undefined, FIT_PADDING)}
      >
        Fit
      </button>
    </div>
  );
}
