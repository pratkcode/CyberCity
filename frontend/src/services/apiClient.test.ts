import { afterEach, describe, expect, it, vi } from "vitest";

import { ApiError, requestJson } from "./apiClient";

function mockFetch(impl: () => Promise<Response>) {
  vi.stubGlobal("fetch", vi.fn(impl));
}

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("requestJson", () => {
  it("returns parsed JSON on success", async () => {
    mockFetch(async () => Response.json({ status: "ok", version: "0.1.0" }));

    await expect(requestJson("/health")).resolves.toEqual({ status: "ok", version: "0.1.0" });
    expect(fetch).toHaveBeenCalledWith("/api/health", expect.any(Object));
  });

  it("converts the backend error envelope into an ApiError", async () => {
    mockFetch(async () =>
      Response.json(
        { error: { code: "not_found", message: "Device 'x' does not exist.", details: [] } },
        { status: 404 },
      ),
    );

    const error = await requestJson("/network/devices/x").catch((e: unknown) => e);
    expect(error).toBeInstanceOf(ApiError);
    expect(error).toMatchObject({ status: 404, code: "not_found", message: "Device 'x' does not exist." });
  });

  it("reports an unreachable backend as a network error", async () => {
    mockFetch(async () => {
      throw new TypeError("fetch failed");
    });

    await expect(requestJson("/health")).rejects.toMatchObject({ status: 0, code: "network_error" });
  });
});
