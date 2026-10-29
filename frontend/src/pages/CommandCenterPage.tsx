import { useCallback, useMemo, useState } from "react";

import { DataBadge } from "../components/DataBadge";
import { EmptyState } from "../components/EmptyState";
import { Sidebar } from "../components/layout/Sidebar";
import { TopBar } from "../components/layout/TopBar";
import { CityServicesPanel } from "../features/city-services/CityServicesPanel";
import type { PathEndpoint } from "../features/details/DeviceDetails";
import { buildNameLookup } from "../features/details/names";
import { SelectionPanel, type Selection } from "../features/details/SelectionPanel";
import { MapLegend } from "../features/network-map/MapLegend";
import { NetworkMap, type MapHighlight } from "../features/network-map/NetworkMap";
import { PathAccessPanel, type PathEndpoints } from "../features/path-tools/PathAccessPanel";
import { ValidationPanel } from "../features/validation/ValidationPanel";
import { useSimulationData } from "../hooks/useSimulationData";
import { serviceDeviceIds } from "../types/city";

export function CommandCenterPage() {
  const data = useSimulationData();
  const [selection, setSelection] = useState<Selection | null>(null);
  const [endpoints, setEndpoints] = useState<PathEndpoints>({ source: "", target: "" });
  const [pathHighlight, setPathHighlight] = useState<MapHighlight | null>(null);

  const ready = data.status === "ready" ? data : null;
  const names = useMemo(() => (ready ? buildNameLookup(ready.topology, ready.services) : null), [ready]);

  // A selected service highlights its devices; otherwise show the last path result.
  const highlight = useMemo<MapHighlight | null>(() => {
    if (selection?.kind === "service" && ready) {
      const overview = ready.services.find((s) => s.service.id === selection.id);
      if (overview) return { deviceIds: serviceDeviceIds(overview.service), connectionIds: [] };
    }
    return pathHighlight;
  }, [selection, ready, pathHighlight]);

  const selectDevice = useCallback(
    (id: string | null) => setSelection(id ? { kind: "device", id } : null),
    [],
  );
  const selectConnection = useCallback((id: string) => setSelection({ kind: "connection", id }), []);
  const setEndpoint = useCallback(
    (endpoint: PathEndpoint, deviceId: string) => setEndpoints((prev) => ({ ...prev, [endpoint]: deviceId })),
    [],
  );

  return (
    <div className="app-shell">
      <Sidebar />

      <main className="main-column">
        <TopBar summary={ready?.summary ?? null} />

        <section className="map-area" aria-label="Network map">
          <div className="map-area__header">
            <h2 className="panel__title">City Network</h2>
            <div className="map-area__header-actions">
              {highlight && (
                <button
                  type="button"
                  className="ghost-button"
                  onClick={() => {
                    setPathHighlight(null);
                    if (selection?.kind === "service") setSelection(null);
                  }}
                >
                  Clear highlight
                </button>
              )}
              <DataBadge source="sample" />
            </div>
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
              <NetworkMap
                topology={ready.topology}
                selectedDeviceId={selection?.kind === "device" ? selection.id : null}
                selectedConnectionId={selection?.kind === "connection" ? selection.id : null}
                highlight={highlight}
                onSelectDevice={selectDevice}
                onSelectConnection={selectConnection}
              />
            )}
          </div>
          <MapLegend />
        </section>

        {ready && names && (
          <div className="bottom-row">
            <CityServicesPanel
              services={ready.services}
              selectedId={selection?.kind === "service" ? selection.id : null}
              onSelectService={(id) => setSelection({ kind: "service", id })}
            />
            <PathAccessPanel
              topology={ready.topology}
              names={names}
              endpoints={endpoints}
              onEndpointsChange={setEndpoints}
              onHighlight={setPathHighlight}
            />
          </div>
        )}
      </main>

      <aside className="detail-column" aria-label="Details">
        {ready && names && (
          <>
            <SelectionPanel
              selection={selection}
              topology={ready.topology}
              services={ready.services}
              names={names}
              onSelect={setSelection}
              onSetEndpoint={setEndpoint}
            />
            <ValidationPanel
              report={ready.validation}
              isDevice={(id) => ready.topology.devices.some((d) => d.id === id)}
              onSelectDevice={selectDevice}
            />
          </>
        )}
      </aside>
    </div>
  );
}
