import { useCallback, useEffect, useState } from "react";

import { ApiError } from "../services/apiClient";
import { simulationApi } from "../services/simulationApi";
import type { NetworkSnapshot, SimulationSummary } from "../types/simulation";

export type SimulationData =
  | { status: "loading" }
  | { status: "error"; error: ApiError }
  | { status: "ready"; summary: SimulationSummary; network: NetworkSnapshot };

/** Loads the current simulation summary and network map together. */
export function useSimulationData(): SimulationData & { reload: () => void } {
  const [data, setData] = useState<SimulationData>({ status: "loading" });
  const [attempt, setAttempt] = useState(0);

  useEffect(() => {
    let cancelled = false;

    Promise.all([simulationApi.getSimulation(), simulationApi.getNetwork()])
      .then(([summary, network]) => {
        if (!cancelled) setData({ status: "ready", summary, network });
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
