import { useMemo, useState } from "react";

import { EmptyState } from "../components/EmptyState";
import { Sidebar } from "../components/layout/Sidebar";
import { TopBar } from "../components/layout/TopBar";
import { DataBadge } from "../components/DataBadge";
import { AlertsPanel } from "../features/alerts/AlertsPanel";
import { CityServicesPanel } from "../features/city-services/CityServicesPanel";
import { DeviceDetailsPanel } from "../features/device-details/DeviceDetailsPanel";
import { getDeviceContext } from "../features/device-details/deviceContext";
import { MapLegend } from "../features/network-map/MapLegend";
import { NetworkMap } from "../features/network-map/NetworkMap";
import { ResourcesPanel } from "../features/resources/ResourcesPanel";
import { useSimulationData } from "../hooks/useSimulationData";

export function CommandCenterPage() {
  const data = useSimulationData();
  const [selectedId, setSelectedId] = useState<string | null>(null);

  const ready = data.status === "ready" ? data : null;
  const deviceContext = useMemo(
    () =>
      ready && selectedId
        ? getDeviceContext(ready.network, ready.summary.services, selectedId)
        : null,
    [ready, selectedId],
  );

  return (
    <div className="app-shell">
      <Sidebar />

      <main className="main-column">
        <TopBar summary={ready?.summary ?? null} />

        <section className="map-area" aria-label="Network map">
          <div className="map-area__header">
            <h2 className="panel__title">City Network</h2>
            <DataBadge source="sample" />
          </div>
          <div className="map-area__canvas">
            {data.status === "loading" && <EmptyState title="Loading simulation…" />}
            {data.status === "error" && (
              <EmptyState title="Couldn't load the simulation">
                {data.error.message}{" "}
                <button type="button" className="ghost-button" onClick={data.reload}>
                  Retry
                </button>
              </EmptyState>
            )}
            {ready && (
              <NetworkMap network={ready.network} selectedId={selectedId} onSelect={setSelectedId} />
            )}
          </div>
          <MapLegend />
        </section>

        <div className="bottom-row">
          <AlertsPanel />
          {ready && (
            <CityServicesPanel services={ready.summary.services} onSelectDevice={setSelectedId} />
          )}
        </div>
      </main>

      <aside className="detail-column" aria-label="Details">
        <DeviceDetailsPanel context={deviceContext} onSelectDevice={setSelectedId} />
        {ready && <ResourcesPanel config={ready.summary.config} />}
      </aside>
    </div>
  );
}
