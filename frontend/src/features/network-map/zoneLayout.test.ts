import { describe, expect, it } from "vitest";

import { topologyFixture } from "../../test/fixtures";
import { CELL, computeZoneLayout, gridShape } from "./zoneLayout";

describe("computeZoneLayout", () => {
  const positions = computeZoneLayout(topologyFixture);

  it("positions every device", () => {
    expect([...positions.keys()].sort()).toEqual(topologyFixture.devices.map((d) => d.id).sort());
  });

  it("is deterministic regardless of input order", () => {
    const shuffled = {
      ...topologyFixture,
      zones: [...topologyFixture.zones].reverse(),
      devices: [...topologyFixture.devices].reverse(),
    };
    expect(computeZoneLayout(shuffled)).toEqual(positions);
  });

  it("puts public zones in the top row and internal/restricted zones below", () => {
    const y = (id: string) => positions.get(id)!.y;
    expect(y("rtr-01")).toBeLessThan(y("sw-01"));
    expect(y("rtr-01")).toBeLessThan(y("db-01"));
  });

  it("places gateways first within a zone", () => {
    // Switch sorts before the workstation and sensor in the LAN grid.
    const lan = ["sw-01", "ids-01", "ws-01"].map((id) => positions.get(id)!);
    expect(lan[0]!.x).toBeLessThan(lan[1]!.x);
  });

  it("never stacks two devices on the same spot", () => {
    const keys = [...positions.values()].map((p) => `${p.x},${p.y}`);
    expect(new Set(keys).size).toBe(keys.length);
  });

  it("keeps devices of different zones at least a cell apart", () => {
    const dx = Math.abs(positions.get("sw-01")!.x - positions.get("db-01")!.x);
    expect(dx).toBeGreaterThanOrEqual(CELL.width);
  });
});

describe("gridShape", () => {
  it.each([
    [1, 1, 1],
    [3, 3, 1],
    [4, 2, 2],
    [8, 4, 2],
    [11, 4, 3],
  ])("%i devices → %i columns × %i rows", (count, columns, rows) => {
    expect(gridShape(count)).toEqual({ columns, rows });
  });
});
