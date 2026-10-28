import { describe, expect, it } from "vitest";

import { networkFixture } from "../../test/fixtures";
import { toCytoscapeElements } from "./networkElements";

describe("toCytoscapeElements", () => {
  const elements = toCytoscapeElements(networkFixture);
  const nodes = elements.filter((e) => e.group === "nodes");
  const edges = elements.filter((e) => e.group === "edges");

  it("creates one node per device and one edge per connection", () => {
    expect(nodes).toHaveLength(networkFixture.devices.length);
    expect(edges).toHaveLength(networkFixture.connections.length);
  });

  it("maps device fields used by the stylesheet", () => {
    expect(nodes[0]?.data).toMatchObject({
      id: "edge-router-01",
      label: "City Edge Router",
      deviceType: "router",
      criticality: "critical",
    });
  });

  it("marks offline devices and encrypted links with classes", () => {
    expect(nodes.find((n) => n.data.id === "biz-pos-01")?.classes).toBe("offline");
    expect(edges.find((e) => e.data.id === "link-edge-hosp")?.classes).toBe("encrypted");
    expect(edges.find((e) => e.data.id === "link-edge-biz")?.classes).toBe("");
  });
});
