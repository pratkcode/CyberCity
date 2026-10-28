# CyberCity Architecture

This document explains how the Phase 1 foundation is organized and why.

## Safety boundary

CyberCity is a simulation. The backend holds an invented network in memory
and never opens sockets to anything except its own HTTP clients. Devices
have no IP addresses or hostnames, so nothing in the model can be pointed
at a real system.

## High-level flow

```
Browser (React + Cytoscape)
   │  fetch /api/...            (Vite dev server proxies /api → :8000)
   ▼
FastAPI routes  (app/api)       thin: validate input, call service, return models
   │
   ▼
SimulationService (app/services) owns the active simulation, maps domain errors
   │
   ▼
Simulation core (app/simulation) pure Python + NetworkX, no HTTP or I/O
   │
   ▼
Pydantic models (app/models)    shared, validated, immutable data types
```

Each layer imports only from the layers below it. The simulation core does
not know about FastAPI, so it can be tested directly and reused later by a
CLI, a batch runner, or persistence code.

## Backend

| Package | Responsibility |
| --- | --- |
| `app/models` | Pydantic models: `NetworkDevice`, `NetworkConnection`, `CityService`, `SecurityEvent`, `SimulationConfig`, and response snapshots. All are frozen and reject unknown fields. |
| `app/simulation/sample_network.py` | The fictional sample city: 14 devices, 14 links, 6 services. |
| `app/simulation/network.py` | Builds the `networkx.Graph`, checks referential integrity (unknown endpoints, duplicate IDs, parallel links), and converts the graph back to a snapshot. |
| `app/simulation/state.py` | `SimulationState` and `initialize_simulation(config)`, the deterministic entry point. |
| `app/services` | `SimulationService` (in-memory state holder) and domain errors (`NotFoundError`, `InvalidTopologyError`). |
| `app/api` | Routers, dependency injection, and the global error handlers. |

### Identifiers

IDs are lowercase slugs (`hosp-ehr-db-01`) matching
`^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$`, 2–48 characters. The same pattern is
enforced on models and on URL path parameters, so a malformed ID is a
422 before any lookup happens.

### Determinism

`initialize_simulation` creates a `random.Random(config.seed)` and stores it
on the state. Rules for all simulation code:

1. Draw randomness only from `state.rng`, never the global `random` module.
2. Never read wall-clock time inside simulation logic. Use `state.tick`.
3. Iterate in sorted order before making a random choice (graph nodes are
   inserted and visited sorted by ID).

Phase 1 uses the RNG to seed each device's `patch_age_days`, bounded by
difficulty. Tests assert that identical configs produce byte-identical
snapshots and that the RNG stream stays in step afterwards.

### Error format

Every error response, whether validation, not-found, or domain, has the
same envelope:

```json
{ "error": { "code": "validation_error", "message": "...", "details": [ { "location": ["path", "device_id"], "message": "...", "type": "..." } ] } }
```

### State and concurrency

One simulation lives on `app.state` per app instance. `create_app()` is a
factory, so each test gets isolated state. Swapping the simulation replaces a
single reference under a lock. SQLite persistence is planned for a later
phase and will sit behind the same service methods.

## Frontend

| Folder | Responsibility |
| --- | --- |
| `src/types` | TypeScript mirrors of backend models. |
| `src/services` | `apiClient.ts` (fetch wrapper → `ApiError`) and `simulationApi.ts` (typed endpoint functions). |
| `src/hooks` | `useSimulationData`: loads summary + network, exposes loading/error/ready. |
| `src/components` | Reusable UI: `Panel`, `DataBadge`, `KeyValueList`, `EmptyState`, layout (`Sidebar`, `TopBar`). |
| `src/features/*` | One folder per feature: network map, device details, alerts, city services, resources. |
| `src/pages` | `CommandCenterPage` composes the layout and owns selection state. |
| `src/styles` | Design tokens (`theme.css`), page grid (`layout.css`), component styles. |

### Cytoscape integration

`NetworkMap` creates one Cytoscape instance per network snapshot and syncs
selection imperatively, so React never re-renders the canvas. Element
conversion (`networkElements.ts`) is a pure function with its own tests. The
`breadthfirst` layout is deterministic, and a `ResizeObserver` refits the
graph when the layout changes size.

### Labelling data honestly

`DataBadge` marks every panel's data source:

- **Sample data**: the bundled fictional network.
- **Config value**: echoed from `SimulationConfig`, not computed.
- **Placeholder**: feature not implemented yet. No numbers are shown.

## Deviations from the suggested structure

- `backend/pyproject.toml` was added only for pytest settings
  (`pythonpath`, `testpaths`). Dependencies stay in `requirements.txt` as
  requested.
- `frontend/src/hooks`, `src/utils`, `src/styles` and `src/test` were added
  alongside the suggested folders to keep data loading, formatting, styles
  and test setup out of components.
- Frontend tests sit next to the code they test (`*.test.tsx`), which is
  the Vitest convention. Backend tests live in `backend/tests`.
