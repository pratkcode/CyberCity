import { useCallback, useEffect, useState } from "react";

import { ApiError } from "../services/apiClient";
import { simulationApi } from "../services/simulationApi";
import type { ServiceOverview } from "../types/city";
import type { Topology, ValidationReport } from "../types/network";
import type { SimulationSummary } from "../types/simulation";

export interface SimulationSnapshot {
  summary: SimulationSummary;
  topology: Topology;
  services: ServiceOverview[];
  validation: ValidationReport;
}

export type SimulationData =
  | { status: "loading" }
  | { status: "error"; error: ApiError }
  | ({ status: "ready" } & SimulationSnapshot);

/** Loads everything the command center needs in parallel. */
export function useSimulationData(): SimulationData & { reload: () => void } {
  const [data, setData] = useState<SimulationData>({ status: "loading" });
  const [attempt, setAttempt] = useState(0);

  useEffect(() => {
    let cancelled = false;

    Promise.all([
      simulationApi.getSimulation(),
      simulationApi.getTopology(),
      simulationApi.getServices(),
      simulationApi.getValidation(),
    ])
      .then(([summary, topology, services, validation]) => {
        if (!cancelled) setData({ status: "ready", summary, topology, services, validation });
      })
      .catch((error: unknown) => {
        if (cancelled) return;
        const apiError =
          error instanceof ApiError ? error : new ApiError(0, "unknown_error", String(error));
        setData({ status: "error", error: apiError });
      });

    return () => {
      cancelled = true;
    };
  }, [attempt]);

  const reload = useCallback(() => {
    setData({ status: "loading" });
    setAttempt((n) => n + 1);
  }, []);

  return { ...data, reload };
}
