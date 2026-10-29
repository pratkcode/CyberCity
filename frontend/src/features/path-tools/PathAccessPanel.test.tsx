import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { useState } from "react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { simulationApi } from "../../services/simulationApi";
import { servicesFixture, topologyFixture } from "../../test/fixtures";
import type { ConnectionCheck, PathResult } from "../../types/network";
import { buildNameLookup } from "../details/names";
import type { MapHighlight } from "../network-map/NetworkMap";
import { PathAccessPanel, type PathEndpoints } from "./PathAccessPanel";

const names = buildNameLookup(topologyFixture, servicesFixture);

function Harness({ onHighlight }: { onHighlight: (h: MapHighlight | null) => void }) {
  const [endpoints, setEndpoints] = useState<PathEndpoints>({ source: "", target: "" });
  return (
    <PathAccessPanel
      topology={topologyFixture}
      names={names}
      endpoints={endpoints}
      onEndpointsChange={setEndpoints}
      onHighlight={onHighlight}
    />
  );
}

const pathResult: PathResult = {
  source_id: "web-01", target_id: "db-01", metric: "hops", found: true, reason: "ok",
  path: {
    device_ids: ["web-01", "rtr-01", "sw-01", "db-01"],
    connection_ids: ["link-rtr-web", "link-rtr-sw", "link-sw-db"],
    hop_count: 3, total_latency_ms: 1.5, bottleneck_bandwidth_mbps: 1000,
  },
};

async function chooseEndpoints() {
  await userEvent.selectOptions(screen.getByLabelText("Source"), "web-01");
  await userEvent.selectOptions(screen.getByLabelText("Target"), "db-01");
}

afterEach(() => vi.restoreAllMocks());

describe("PathAccessPanel", () => {
  it("disables actions until both endpoints are chosen", async () => {
    render(<Harness onHighlight={vi.fn()} />);
    expect(screen.getByRole("button", { name: "Find path" })).toBeDisabled();
    await chooseEndpoints();
    expect(screen.getByRole("button", { name: "Find path" })).toBeEnabled();
  });

  it("defaults the protocol to a service the target offers", async () => {
    render(<Harness onHighlight={vi.fn()} />);
    await chooseEndpoints();
    expect(screen.getByLabelText("Protocol")).toHaveValue("sql");
  });

  it("finds a path, lists it, and highlights it on the map", async () => {
    const findPath = vi.spyOn(simulationApi, "findPath").mockResolvedValue(pathResult);
    const onHighlight = vi.fn();
    render(<Harness onHighlight={onHighlight} />);
    await chooseEndpoints();
    await userEvent.selectOptions(screen.getByLabelText("Route by"), "latency");

    await userEvent.click(screen.getByRole("button", { name: "Find path" }));

    expect(findPath).toHaveBeenCalledWith("web-01", "db-01", "latency");
    expect(await screen.findByText(/3 hops · 1.5 ms · bottleneck 1 Gbps/)).toBeInTheDocument();
    expect(screen.getAllByRole("listitem").map((li) => li.textContent)).toEqual([
      "Public Portal", "Edge Router", "Core Switch", "Records Database",
    ]);
    expect(onHighlight).toHaveBeenCalledWith({
      deviceIds: pathResult.path!.device_ids,
      connectionIds: pathResult.path!.connection_ids,
    });
  });

  it("explains a denied access check step by step", async () => {
    const denied: ConnectionCheck = {
      source_id: "web-01", destination_id: "db-01", protocol: "sql", permitted: false, path: pathResult.path,
      summary: "Not permitted",
      policy: {
        allowed: false, source_zone_id: "dmz", destination_zone_id: "data", protocol: "sql",
        matched_rule_id: null, default_applied: true, reason: "Denied by default: no rule matches dmz → data over sql.",
      },
      steps: [
        { check: "source_operational", passed: true, detail: "'web-01' is online." },
        { check: "policy", passed: false, detail: "Denied by default: no rule matches dmz → data over sql." },
      ],
    };
    const checkAccess = vi.spyOn(simulationApi, "checkAccess").mockResolvedValue(denied);
    render(<Harness onHighlight={vi.fn()} />);
    await chooseEndpoints();

    await userEvent.click(screen.getByRole("button", { name: "Check access" }));

    expect(checkAccess).toHaveBeenCalledWith("web-01", "db-01", "sql");
    expect(await screen.findByText("Not permitted")).toBeInTheDocument();
    expect(screen.getByText(/no rule matches dmz → data over sql/)).toBeInTheDocument();
    expect(screen.getByLabelText("Failed")).toBeInTheDocument();
  });

  it("reports when no path exists and clears the highlight", async () => {
    vi.spyOn(simulationApi, "findPath").mockResolvedValue({ ...pathResult, found: false, path: null, reason: "No route." });
    const onHighlight = vi.fn();
    render(<Harness onHighlight={onHighlight} />);
    await chooseEndpoints();

    await userEvent.click(screen.getByRole("button", { name: "Find path" }));

    expect(await screen.findByText("No path. No route.")).toBeInTheDocument();
    expect(onHighlight).toHaveBeenLastCalledWith(null);
  });
});
