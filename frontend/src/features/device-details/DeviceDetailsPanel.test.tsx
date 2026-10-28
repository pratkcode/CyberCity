import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { networkFixture, summaryFixture } from "../../test/fixtures";
import { DeviceDetailsPanel } from "./DeviceDetailsPanel";
import { getDeviceContext } from "./deviceContext";

const contextFor = (id: string) => getDeviceContext(networkFixture, summaryFixture.services, id);

describe("DeviceDetailsPanel", () => {
  it("prompts the user to select a device when nothing is selected", () => {
    render(<DeviceDetailsPanel context={null} />);

    expect(screen.getByText("No device selected")).toBeInTheDocument();
    expect(screen.queryByText("Sample data")).not.toBeInTheDocument();
  });

  it("shows the selected device's properties and labels them as sample data", () => {
    render(<DeviceDetailsPanel context={contextFor("hosp-ehr-db-01")} />);

    expect(screen.getByRole("heading", { name: "St. Aurelia Patient Records DB" })).toBeInTheDocument();
    expect(screen.getByText("hosp-ehr-db-01")).toBeInTheDocument();
    expect(screen.getByText("Database")).toBeInTheDocument();
    expect(screen.getByText("Critical")).toBeInTheDocument();
    expect(screen.getByText("47 days (seeded)")).toBeInTheDocument();
    expect(screen.getByText("Sample data")).toBeInTheDocument();
    expect(screen.getByText("Hospital Patient Records")).toBeInTheDocument();
  });

  it("lists connections in both directions and lets the user jump to a peer", async () => {
    const onSelectDevice = vi.fn();
    render(<DeviceDetailsPanel context={contextFor("edge-router-01")} onSelectDevice={onSelectDevice} />);

    expect(screen.getByText("Connections (2)")).toBeInTheDocument();
    expect(screen.getByText("Fiber · 10 Gbps · encrypted")).toBeInTheDocument();
    expect(screen.getByText("Wireless · 300 Mbps")).toBeInTheDocument();

    await userEvent.click(screen.getByRole("button", { name: "Market Street Retail Terminal" }));
    expect(onSelectDevice).toHaveBeenCalledWith("biz-pos-01");
  });

  it("reports offline devices", () => {
    render(<DeviceDetailsPanel context={contextFor("biz-pos-01")} />);

    expect(screen.getByText("Offline")).toBeInTheDocument();
    expect(screen.getByText("No city service depends directly on this device.")).toBeInTheDocument();
  });
});

describe("getDeviceContext", () => {
  it("returns null for an unknown device", () => {
    expect(contextFor("ghost-01")).toBeNull();
  });
});
