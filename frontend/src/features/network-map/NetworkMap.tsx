import cytoscape, { type Core } from "cytoscape";
import { useEffect, useRef } from "react";

import type { NetworkSnapshot } from "../../types/simulation";
import { LAYOUT_ROOT_TYPES, toCytoscapeElements } from "./networkElements";
import { networkStylesheet } from "./networkStyle";

const FIT_PADDING = 24;

interface NetworkMapProps {
  network: NetworkSnapshot;
  selectedId: string | null;
  onSelect: (deviceId: string | null) => void;
}

/**
 * Thin React wrapper around a Cytoscape instance.
 *
 * Cytoscape manages its own DOM and canvas, so React only provides the
 * container. The instance is created once per network snapshot, and
 * selection changes are pushed to it imperatively.
 */
export function NetworkMap({ network, selectedId, onSelect }: NetworkMapProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const cyRef = useRef<Core | null>(null);
  // Keep the latest callback without recreating the graph on every render.
  const onSelectRef = useRef(onSelect);
  useEffect(() => {
    onSelectRef.current = onSelect;
  }, [onSelect]);

  useEffect(() => {
    if (!containerRef.current) return;

    const cy = cytoscape({
      container: containerRef.current,
      elements: toCytoscapeElements(network),
      style: networkStylesheet,
      // Breadthfirst is deterministic, so the same network always draws the same way.
      layout: {
        name: "breadthfirst",
        roots: network.devices
          .filter((d) => (LAYOUT_ROOT_TYPES as readonly string[]).includes(d.device_type))
          .map((d) => d.id),
        spacingFactor: 0.8,
        avoidOverlap: true,
        nodeDimensionsIncludeLabels: true,
        padding: FIT_PADDING,
        animate: false,
      },
      selectionType: "single",
      minZoom: 0.3,
      maxZoom: 2.5,
      wheelSensitivity: 0.3,
    });

    cy.on("tap", "node", (event) => onSelectRef.current(event.target.id()));
    cy.on("tap", (event) => {
      if (event.target === cy) onSelectRef.current(null);
    });

    // Refit whenever the container changes size (window resize, panel layout).
    const fitToContainer = () => {
      cy.resize();
      cy.fit(undefined, FIT_PADDING);
    };
    const observer =
      typeof ResizeObserver === "undefined" ? null : new ResizeObserver(fitToContainer);
    observer?.observe(containerRef.current);
    fitToContainer();

    cyRef.current = cy;
    return () => {
      observer?.disconnect();
      cy.destroy();
      cyRef.current = null;
    };
  }, [network]);

  useEffect(() => {
    const cy = cyRef.current;
    if (!cy) return;
    cy.nodes().unselect();
    if (selectedId) cy.getElementById(selectedId).select();
  }, [selectedId, network]);

  return (
    <div
      ref={containerRef}
      className="network-map"
      role="img"
      aria-label={`Network map with ${network.devices.length} devices and ${network.connections.length} connections`}
    />
  );
}
