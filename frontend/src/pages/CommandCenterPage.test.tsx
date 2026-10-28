import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { ApiError } from "../services/apiClient";
import { simulationApi } from "../services/simulationApi";
import { networkFixture, summaryFixture } from "../test/fixtures";
import { CommandCenterPage } from "./CommandCenterPage";

// Cytoscape needs a real canvas, which jsdom lacks. Replace the map with a
// simple list of buttons that calls onSelect the same way a node tap would.
vi.mock("../features/network-map/NetworkMap", () => ({
  NetworkMap: ({ network, onSelect }: { network: typeof networkFixture; onSelect: (id: string) => void }) => (
    <div data-testid="network-map">
      {network.devices.map((d) => (
        <button key={d.id} type="button" onClick={() => onSelect(d.id)}>
          node:{d.id}
        </button>
      ))}
    </div>
  ),
}));

describe("CommandCenterPage", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("loads the simulation and shows device details after selecting a node", async () => {
    vi.spyOn(simulationApi, "getSimulation").mockResolvedValue(summaryFixture);
    vi.spyOn(simulationApi, "getNetwork").mockResolvedValue(networkFixture);

    render(<CommandCenterPage />);

    expect(await screen.findByTestId("network-map")).toBeInTheDocument();
    expect(screen.getByText("Day 1 · 00:00")).toBeInTheDocument();
    expect(screen.getByText("No device selected")).toBeInTheDocument();
    expect(screen.getByText("Alert feed not active")).toBeInTheDocument();

    await userEvent.click(screen.getByRole("button", { name: "node:hosp-ehr-db-01" }));

    expect(screen.getByRole("heading", { name: "St. Aurelia Patient Records DB" })).toBeInTheDocument();
  });

  it("shows a retryable error when the backend is unreachable", async () => {
    vi.spyOn(simulationApi, "getSimulation").mockRejectedValue(
      new ApiError(0, "network_error", "Could not reach the CyberCity backend. Is it running?"),
    );
    vi.spyOn(simulationApi, "getNetwork").mockResolvedValue(networkFixture);

    render(<CommandCenterPage />);

    expect(await screen.findByText("Couldn't load the simulation")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Retry" })).toBeInTheDocument();
  });
});
