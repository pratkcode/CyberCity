import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import type { MapHighlight } from "../features/network-map/NetworkMap";
import { ApiError } from "../services/apiClient";
import { simulationApi } from "../services/simulationApi";
import {
  deviceDetailFixture,
  servicesFixture,
  summaryFixture,
  topologyFixture,
  validationFixture,
} from "../test/fixtures";
import type { Topology } from "../types/network";
import { CommandCenterPage } from "./CommandCenterPage";

// Cytoscape needs a real canvas, which jsdom lacks. The stand-in renders the
// same callbacks as buttons and exposes the current highlight as text.
vi.mock("../features/network-map/NetworkMap", () => ({
  NetworkMap: ({
    topology,
    highlight,
    onSelectDevice,
    onSelectConnection,
  }: {
    topology: Topology;
    highlight: MapHighlight | null;
    onSelectDevice: (id: string) => void;
    onSelectConnection: (id: string) => void;
  }) => (
    <div data-testid="network-map">
      <span data-testid="highlight">{highlight ? highlight.deviceIds.join(",") : "none"}</span>
      {topology.devices.map((d) => (
        <button key={d.id} type="button" onClick={() => onSelectDevice(d.id)}>
          node:{d.id}
        </button>
      ))}
      {topology.connections.map((c) => (
        <button key={c.id} type="button" onClick={() => onSelectConnection(c.id)}>
          edge:{c.id}
        </button>
      ))}
    </div>
  ),
}));

function mockApi() {
  vi.spyOn(simulationApi, "getSimulation").mockResolvedValue(summaryFixture);
  vi.spyOn(simulationApi, "getTopology").mockResolvedValue(topologyFixture);
  vi.spyOn(simulationApi, "getServices").mockResolvedValue(servicesFixture);
  vi.spyOn(simulationApi, "getValidation").mockResolvedValue(validationFixture);
  return vi.spyOn(simulationApi, "getDeviceDetail").mockResolvedValue(deviceDetailFixture);
}

afterEach(() => vi.restoreAllMocks());

describe("CommandCenterPage", () => {
  it("loads the topology, services and validation", async () => {
    mockApi();
    render(<CommandCenterPage />);

    expect(await screen.findByTestId("network-map")).toBeInTheDocument();
    expect(screen.getByText("6 devices · 3 zones")).toBeInTheDocument();
    expect(screen.getByText("Citizen Portal")).toBeInTheDocument();
    expect(screen.getByText(/Valid · 0 errors · 1 warnings/)).toBeInTheDocument();
    expect(screen.getByText("Nothing selected")).toBeInTheDocument();
  });

  it("fetches device details from the backend when a node is selected", async () => {
    const getDeviceDetail = mockApi();
    render(<CommandCenterPage />);

    await userEvent.click(await screen.findByRole("button", { name: "node:db-01" }));

    expect(getDeviceDetail).toHaveBeenCalledWith("db-01");
    expect(await screen.findByRole("heading", { name: "Records Database" })).toBeInTheDocument();
  });

  it("shows link details when an edge is selected", async () => {
    mockApi();
    render(<CommandCenterPage />);

    await userEvent.click(await screen.findByRole("button", { name: "edge:link-sw-ids" }));

    expect(screen.getByRole("heading", { name: "Core Switch ↔ IDS Sensor" })).toBeInTheDocument();
  });

  it("highlights a service's devices and shows its health", async () => {
    mockApi();
    render(<CommandCenterPage />);

    const services = await screen.findByRole("region", { name: "City Services" });
    await userEvent.click(within(services).getByRole("button", { name: /Citizen Portal/ }));

    expect(screen.getByTestId("highlight")).toHaveTextContent("db-01,web-01");
    expect(screen.getByRole("heading", { name: "Service Health" })).toBeInTheDocument();
  });

  it("shows a retryable error when the backend is unreachable", async () => {
    mockApi();
    vi.spyOn(simulationApi, "getSimulation").mockRejectedValue(
      new ApiError(0, "network_error", "Could not reach the CyberCity backend. Is it running?"),
    );
    render(<CommandCenterPage />);

    expect(await screen.findByText("Couldn't load the simulation")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Retry" })).toBeInTheDocument();
  });
});
