# CyberCity Architecture

This document explains how CyberCity is organized and why. It covers Phase 1
(foundation) and Phase 2 (network modeling engine).

## Safety boundary

CyberCity is a simulation. The backend holds an invented city in memory and
never opens network connections. Devices have no IP addresses or hostnames.
Protocols are labels only, vulnerabilities use invented `ccv-…` IDs (not
CVEs), and "connection checks" evaluate a model; nothing is transmitted.

## High-level flow

```
Browser (React + Cytoscape)
   │  fetch /api/...             (Vite dev server proxies /api → :8000)
   ▼
FastAPI routes (app/api)          thin: validate input, call service, return models
   │
   ▼
SimulationService (app/services)  owns the active SimulationState on app.state
   │
   ▼
Simulation core (app/simulation)  pure Python + NetworkX, no HTTP, no I/O
   ├── network_manager.py         topology graph (NetworkX)
   ├── policy.py                  zone access-policy evaluator (no graph)
   ├── connectivity.py            combines status + service + policy + path
   ├── service_health.py          city-service health from connection checks
   ├── validation.py              pre-simulation checks
   └── sample_city/               the fictional city definition
   │
   ▼
Pydantic models (app/models)      validated, immutable data types
```

Each layer imports only from layers below it. The graph code does not know
about policies, and the policy evaluator does not know about the graph.
`connectivity.py` is the one place that combines them.

## Models (`app/models`)

| Module | Contents |
| --- | --- |
| `devices.py` | `DeviceBase` plus one subclass per category (router, firewall, switch, workstation, application server, database server, cloud service, security sensor, hospital system, power controller, banking system). `NetworkDevice` is a discriminated union on `device_type`. Also `PatchStatus`, `ConfiguredService`, `Vulnerability`. |
| `network.py` | `NetworkZone`, `ZoneKind`, `NetworkConnection` (bandwidth, latency, encrypted, `traffic_permitted`), `Protocol`. |
| `policy.py` | `PolicyRule`, `AccessPolicy`, `PolicyDecision`. |
| `city.py` | `Organization`, `CityService`, `ServiceDependency`, `ServiceHealth`. |
| `analysis.py` | `PathResult`, `ConnectionCheck`, `ValidationReport`. |
| `simulation.py` | `SimulationConfig`, `CityDefinition`, and API view models (`Topology`, `DeviceDetail`, `ZoneSummary`, `ServiceOverview`). |

Why a discriminated union instead of one device model: each category has
a few fields that only make sense for it (`monitored_zone_ids` on a sensor,
`control_protocol` on a power controller). Separate models keep those fields
required where they apply and rejected where they don't, and FastAPI's
OpenAPI schema documents each variant.

Common rules: models are frozen and reject unknown fields. IDs are lowercase
slugs (`^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$`, 2–48 characters), and the same
pattern is enforced on URL path and query parameters.

**Configuration vs. activity:** a connection's `bandwidth_mbps`, `latency_ms`
and `traffic_permitted` describe how a link is *configured*. Nothing records
throughput or packets. Activity, if modeled later, will live in separate types.

## Topology engine (`NetworkManager`)

A wrapper around one undirected `networkx.Graph`. Nodes store the device
model and edges store the connection model.

| Operation | Notes |
| --- | --- |
| `add_device` / `remove_device` / `update_device` | Rejects duplicate IDs and unknown zones. Removing a device removes its links. |
| `add_connection` / `remove_connection` | Rejects unknown endpoints, duplicate IDs and parallel links. |
| `get_device`, `devices`, `devices_in_zone`, `connections_of` | Lookups raise `UnknownDeviceError` / `UnknownZoneError`. |
| `neighbors(id, usable_only=False)` | Direct links, optionally only usable ones. |
| `reachable_from(id)` | Everything in the device's usable component. |
| `find_path(src, dst, metric)` | `hops` (BFS) or `latency` (Dijkstra on `latency_ms`). |
| `segments()` / `isolated_device_ids()` | Connected groups of usable devices, and devices outside the largest one. |

**Usable** means traffic could flow: the device is operational (`online` or
`degraded`) and the link has `traffic_permitted`. Offline devices are
*unavailable*. Operational devices cut off from the primary (largest) segment
are *isolated*.

**Determinism:** every result is sorted by ID. Among equally short paths, the
lexicographically smallest device sequence wins
(`min(nx.all_shortest_paths(...))`), so results don't depend on insertion order.

## Access policy (`policy.py`)

Rules are zone-to-zone with an optional protocol list. `None` zones and an
empty protocol list mean "any".

1. Order: `priority` ascending, then **deny before allow** at equal priority,
   then rule `id`. That is a total order, so evaluation is deterministic.
2. The first matching rule decides the outcome.
3. No match means **deny by default**.

Every decision carries `matched_rule_id`, `default_applied` and a plain-English
`reason`, such as *"Denied by rule 'deny-into-grid' (priority 40) for
corp-internal → grid-ot over modbus (Only grid-internal traffic may reach OT
devices)."*

## Connection checks (`connectivity.py`)

`check_connection(network, policy, src, dst, protocol)` runs five independent
checks and reports each one:

1. source operational
2. destination operational
3. destination offers the protocol (`configured_services`)
4. policy allows source zone → destination zone for the protocol
5. a usable network path exists

The connection is permitted only if all five pass. All checks always run, so
the explanation is complete even when several fail.

## City services and health (`service_health.py`)

A `CityService` belongs to an `Organization`, has an `entry_point_id` (where
users reach it), and lists `dependencies`. Each dependency names a device, a
protocol, a role, `required`, and an optional `client_id` (the device that
calls it; defaults to the entry point). That's how chains such as web → app
→ database are written.

Health per service:

- **down**: the entry point is offline, or any required dependency fails its connection check.
- **degraded**: an optional dependency fails, or the entry point or a dependency is in `degraded` status.
- **operational**: otherwise.

### Simplifications (read before trusting the numbers)

This is a teaching model, not a reproduction of real infrastructure:

- Policy is evaluated once, end to end, between the two endpoint zones (like a
  single central firewall). It is not evaluated hop by hop at each firewall on the path.
- Links are undirected and either usable or not. There is no capacity,
  congestion, packet loss, or routing protocol behavior.
- Latency is a static per-link number summed along the path.
- Health is a three-level rule. It ignores failover timing, load, data
  consistency, and human workarounds.
- Firewall `protected_zone_ids` and sensor `monitored_zone_ids` are
  descriptive. Enforcement comes only from the `AccessPolicy`.

## Validation (`validation.py`)

`validate_city(definition)` returns a `ValidationReport` with issues sorted by
severity:

- **errors** (block a simulation from starting): duplicate IDs, devices in
  unknown zones, links to unknown devices, parallel links, policy rules naming
  unknown zones, services referencing unknown organizations or devices, and
  dependencies on protocols the device doesn't offer.
- **warnings / info**: multiple segments, isolated devices, offline devices
  (a warning when high or critical), and empty zones.

`initialize_simulation` validates first and raises `CityValidationError` on
errors. The API surfaces these as `422 invalid_topology` with the issues in
`details`.

## The sample city

`app/simulation/sample_city/` has 36 devices, 37 links and 7 zones (public
DMZ, corporate & civic LAN, clinical network, restricted data, security
operations, grid OT, hosted cloud), 16 policy rules, and 7 services across
6 organizations (healthcare, finance, energy, government, education,
business). It deliberately contains:

- an **isolated** device: Substation 7's link is administratively disabled,
  so `svc-grid-control` is *degraded* (that dependency is optional);
- an **unavailable** device (`univ-ws-01`, offline) and a **degraded** one (`gov-ws-01`);
- **passive IDS taps**: links that exist but carry no routed traffic;
- policy cases worth checking: DMZ → data denied, grid ingress denied,
  grid → SOC syslog allowed by a higher-priority exception.

Seeded randomness only sets patch age (bounded by difficulty), which
determines `current` or `behind`. `unsupported` devices stay unsupported.

## State and concurrency

One `SimulationService` lives on `app.state` per app instance. There is no
module-level mutable state; sample definitions are immutable tuples of
frozen models. `create_app(config, city_definition)` lets tests inject small
cities. Resetting builds a new state and swaps a single reference under a lock.

## Frontend

| Folder | Responsibility |
| --- | --- |
| `src/types` | Hand-written TS mirrors of the backend models (`network.ts`, `city.ts`, `simulation.ts`). |
| `src/services` | `apiClient.ts` (fetch → `ApiError`) and `simulationApi.ts` (typed endpoint functions). |
| `src/hooks` | `useSimulationData` (summary, topology, services, validation) and `useAsync` (keyed fetch for device details). |
| `src/features/network-map` | Cytoscape wrapper, deterministic zone layout, element conversion, stylesheet, legend. |
| `src/features/details` | Device / link / service detail views and the panel that switches between them. |
| `src/features/path-tools` | Path finder and access checker. |
| `src/features/city-services`, `src/features/validation` | Service health list and validation report. |
| `src/pages` | `CommandCenterPage`: owns selection, path endpoints and highlight state. |

### Map design

- **Layout:** `zoneLayout.ts` places zones as boxes in two rows (perimeter and
  specialized zones on top, internal and restricted below) and devices in a
  grid inside each zone, gateways first. It is a pure function with tests, so
  the same topology always draws the same way. Long same-row links arc
  upward so they don't appear to pass through unrelated devices.
- **Encoding:** category is shown by shape and color. State is shown by
  border: degraded is an amber ring, isolated a red dashed ring, unavailable
  a grey dotted ring and faded. Links show encryption (teal), VPN/wireless
  (dashed), traffic not permitted (red dotted), and bandwidth (width, log scale).
- **Interaction:** click a device (details from `GET /api/network/devices/{id}`),
  a link (properties), or a service (its devices are highlighted). The path
  tool highlights the returned path. The map refits on resize, and a Fit
  button resets zoom.

## Changes from the suggested structure

- `backend/pyproject.toml` holds pytest settings only. Dependencies stay in
  `requirements.txt`.
- The sample city is a package (`sample_city/`) split into devices, topology,
  policy and services, so no single data file grows huge.
- Frontend tests sit next to the code they test, which is the Vitest
  convention. Backend tests live in `backend/tests` with shared builders in
  `tests/factories.py`.
