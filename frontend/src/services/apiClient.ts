import type { ApiErrorBody, ApiErrorDetail } from "../types/simulation";

/** Base path for the backend. In dev, Vite proxies /api to FastAPI. */
export const API_BASE = import.meta.env.VITE_API_BASE ?? "/api";

export class ApiError extends Error {
  readonly status: number;
  readonly code: string;
  readonly details: ApiErrorDetail[];

  constructor(status: number, code: string, message: string, details: ApiErrorDetail[] = []) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.code = code;
    this.details = details;
  }
}

function isApiErrorBody(value: unknown): value is ApiErrorBody {
  if (typeof value !== "object" || value === null || !("error" in value)) return false;
  const error = (value as { error: unknown }).error;
  return typeof error === "object" && error !== null && "code" in error && "message" in error;
}

/**
 * Fetch JSON from the API and turn every failure into an ApiError,
 * so callers handle one error type whether the server or the network failed.
 */
export async function requestJson<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${API_BASE}${path}`, {
      ...init,
      headers: { "Content-Type": "application/json", ...init?.headers },
    });
  } catch {
    throw new ApiError(0, "network_error", "Could not reach the CyberCity backend. Is it running?");
  }

  const body: unknown = await response.json().catch(() => null);

  if (!response.ok) {
    if (isApiErrorBody(body)) {
      const { code, message, details } = body.error;
      throw new ApiError(response.status, code, message, details ?? []);
    }
    throw new ApiError(response.status, "http_error", `Request failed with status ${response.status}.`);
  }

  return body as T;
}
