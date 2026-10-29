import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { deviceDetailFixture, servicesFixture, topologyFixture } from "../../test/fixtures";
import { ConnectionDetails } from "./ConnectionDetails";
import { DeviceDetails } from "./DeviceDetails";
import { buildNameLookup } from "./names";
import { ServiceDetails } from "./ServiceDetails";

const names = buildNameLookup(topologyFixture, servicesFixture);

describe("DeviceDetails", () => {
  it("shows common and category-specific properties from the backend detail", () => {
    render(<DeviceDetails detail={deviceDetailFixture} names={names} />);

    expect(screen.getByRole("heading", { name: "Records Database" })).toBeInTheDocument();
    expect(screen.getByText("Database server")).toBeInTheDocument();
    expect(screen.getByText("Data Zone")).toBeInTheDocument();
    expect(screen.getByText("Behind · 47 days (seeded)")).toBeInTheDocument();
    expect(screen.getByText("Regulated")).toBeInTheDocument(); // data classification
    expect(screen.getByText("sql:5432")).toBeInTheDocument();
    expect(screen.getByText("3 devices over usable links")).toBeInTheDocument();
  });

  it("lists modeled vulnerabilities and counts only open ones", () => {
    render(<DeviceDetails detail={deviceDetailFixture} names={names} />);

    expect(screen.getByText("Modeled vulnerabilities (1 open)")).toBeInTheDocument();
    expect(screen.getByText(/ccv-2026-0002 · remediated/)).toBeInTheDocument();
    expect(screen.getByText(/Not real CVEs/)).toBeInTheDocument();
  });

  it("navigates to linked devices and dependent services", async () => {
    const onSelectDevice = vi.fn();
    const onSelectService = vi.fn();
    render(
      <DeviceDetails detail={deviceDetailFixture} names={names} onSelectDevice={onSelectDevice} onSelectService={onSelectService} />,
    );

    await userEvent.click(screen.getByRole("button", { name: "Core Switch" }));
    await userEvent.click(screen.getByRole("button", { name: "Citizen Portal" }));
    expect(onSelectDevice).toHaveBeenCalledWith("sw-01");
    expect(onSelectService).toHaveBeenCalledWith("svc-portal");
  });

  it("can set the device as a path endpoint", async () => {
    const onSetEndpoint = vi.fn();
    render(<DeviceDetails detail={deviceDetailFixture} names={names} onSetEndpoint={onSetEndpoint} />);

    await userEvent.click(screen.getByRole("button", { name: "Set as target" }));
    expect(onSetEndpoint).toHaveBeenCalledWith("target", "db-01");
  });

  it("flags isolated devices", () => {
    render(<DeviceDetails detail={{ ...deviceDetailFixture, isolated: true }} names={names} />);
    expect(screen.getByText("Isolated")).toBeInTheDocument();
  });
});

describe("ConnectionDetails", () => {
  it("shows link properties and whether traffic is permitted", () => {
    render(<ConnectionDetails connection={topologyFixture.connections[4]!} names={names} />);

    expect(screen.getByRole("heading", { name: "Core Switch ↔ IDS Sensor" })).toBeInTheDocument();
    expect(screen.getByText("1 Gbps")).toBeInTheDocument();
    expect(screen.getByText("0.5 ms")).toBeInTheDocument();
    expect(screen.getByText("Not permitted")).toBeInTheDocument();
    expect(screen.getByText("Passive tap.")).toBeInTheDocument();
  });
});

describe("ServiceDetails", () => {
  it("explains why a dependency fails", () => {
    render(<ServiceDetails overview={servicesFixture[0]!} names={names} />);

    expect(screen.getByText("Down")).toBeInTheDocument();
    expect(screen.getByLabelText("Unavailable")).toBeInTheDocument();
    expect(screen.getByText(/Denied by default/)).toBeInTheDocument();
    expect(screen.getByText("records database · from Public Portal")).toBeInTheDocument();
  });
});
