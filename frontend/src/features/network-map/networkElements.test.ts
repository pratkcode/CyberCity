import { describe, expect, it } from "vitest";

import { topologyFixture } from "../../test/fixtures";
import { arcBend, deviceVisualState, toCytoscapeElements, zoneNodeId } from "./networkElements";

describe("toCytoscapeElements", () => {
  const elements = toCytoscapeElements(topologyFixture);
  const byId = (id: string) => elements.find((e) => e.data.id === id)!;

  it("creates a compound node per zone, a node per device and an edge per link", () => {
    expect(elements.filter((e) => e.classes === "zone")).toHaveLength(3);
    expect(elements.filter((e) => String(e.classes).includes("device"))).toHaveLength(6);
    expect(elements.filter((e) => e.group === "edges")).toHaveLength(5);
  });

  it("nests devices inside their zone and gives them preset positions", () => {
    const db = byId("db-01");
    expect(db.data.parent).toBe(zoneNodeId("data"));
    expect(db.position).toEqual(expect.objectContaining({ x: expect.any(Number), y: expect.any(Number) }));
  });

  it("marks each device's visual state", () => {
    expect(byId("rtr-01").classes).toBe("device state-operational");
    expect(byId("sw-01").classes).toBe("device state-degraded");
    expect(byId("ws-01").classes).toBe("device state-unavailable");
    expect(byId("ids-01").classes).toBe("device state-isolated");
  });

  it("marks encrypted and traffic-blocked links and labels their properties", () => {
    expect(byId("link-rtr-sw").classes).toBe("encrypted");
    expect(byId("link-sw-ids").classes).toBe("blocked");
    expect(byId("link-rtr-sw").data.label).toBe("10 Gbps · 0.5 ms");
    expect(byId("link-rtr-sw").data.capacity).toBe(4);
  });
});

describe("arcBend", () => {
  it("keeps short or diagonal links straight", () => {
    expect(arcBend({ x: 0, y: 0 }, { x: 120, y: 0 })).toBe(0);
    expect(arcBend({ x: 0, y: 0 }, { x: 600, y: 200 })).toBe(0);
  });

  it("arcs long same-row links upward regardless of direction", () => {
    const rightward = arcBend({ x: 0, y: 0 }, { x: 600, y: 0 });
    const leftward = arcBend({ x: 600, y: 0 }, { x: 0, y: 0 });
    expect(rightward).toBeLessThan(0);
    expect(leftward).toBe(-rightward);
  });
});

describe("deviceVisualState", () => {
  it("treats offline as unavailable even when isolated", () => {
    expect(deviceVisualState("offline", true)).toBe("unavailable");
  });
  it("prefers isolated over degraded", () => {
    expect(deviceVisualState("degraded", true)).toBe("isolated");
  });
});
