import { useEffect, useState } from "react";

import { ApiError } from "../services/apiClient";

export type AsyncState<T> =
  | { status: "idle" }
  | { status: "loading" }
  | { status: "error"; error: ApiError }
  | { status: "ready"; data: T };

/**
 * Run `load` whenever `key` changes, ignoring stale responses.
 * A null key means "nothing to load" and resets to idle.
 */
export function useAsync<T>(key: string | null, load: () => Promise<T>): AsyncState<T> {
  const [state, setState] = useState<AsyncState<T>>({ status: "idle" });

  useEffect(() => {
    if (key === null) {
      setState({ status: "idle" });
      return;
    }
    let cancelled = false;
    setState({ status: "loading" });
    load()
      .then((data) => {
        if (!cancelled) setState({ status: "ready", data });
      })
      .catch((error: unknown) => {
        if (cancelled) return;
        setState({
          status: "error",
          error: error instanceof ApiError ? error : new ApiError(0, "unknown_error", String(error)),
        });
      });
    return () => {
      cancelled = true;
    };
    // `load` is derived from `key`, so re-running only on key changes is intended.
  }, [key]);

  return state;
}
