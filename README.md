# CyberCity

An interactive cybersecurity strategy simulator. You defend a fictional city
whose hospitals, banks, power grid, government services and cloud
infrastructure share one interconnected network.

> **Simulation only.** CyberCity never scans, connects to, or attacks real
> systems. Every device, organization and event is invented and lives in memory.

**Status: Phase 1 (foundation).** The backend serves a seeded sample network,
and the frontend shows it as an interactive map in a command-center layout.
Incidents, defenses, budgets and campaigns come in later phases.

![Phase 1 command center](docs/screenshot.png)

## Tech stack

| Layer | Tools |
| --- | --- |
| Backend | Python 3.12+, FastAPI, Pydantic v2, NetworkX, pytest |
| Frontend | React 19, TypeScript, Vite, Cytoscape.js, Vitest, Testing Library |
| Storage | In-memory (SQLite planned) |

## Project layout

```
CyberCity/
├── backend/
│   ├── app/
│   │   ├── main.py            # FastAPI app factory + entry point
│   │   ├── api/               # routers, dependencies, error handlers
│   │   ├── models/            # Pydantic models (devices, links, services, events, config)
│   │   ├── simulation/        # NetworkX graph, sample network, seeded initialization
│   │   └── services/          # SimulationService + domain errors
│   ├── tests/                 # pytest suite
│   ├── requirements.txt
│   └── pyproject.toml         # pytest configuration only
├── frontend/
│   ├── src/
│   │   ├── components/        # reusable UI + layout (Sidebar, TopBar, Panel…)
│   │   ├── features/          # network-map, device-details, alerts, city-services, resources
│   │   ├── pages/             # CommandCenterPage
│   │   ├── services/          # typed API client
│   │   ├── hooks/             # data loading
│   │   ├── types/             # TS mirrors of backend models
│   │   ├── styles/            # theme tokens + layout
│   │   └── test/              # test setup + fixtures
│   ├── package.json
│   └── vite.config.ts         # dev proxy /api → :8000, Vitest config
└── docs/
    └── architecture.md        # design decisions in detail
```

See [docs/architecture.md](docs/architecture.md) for the layering,
determinism rules and error format.

## Setup (macOS)

Prerequisites:

- **Python 3.12+** (`python3 --version`). Tested on 3.13.
- **Node.js 22 or 24 LTS** (`node --version`). `frontend/.nvmrc` pins 24.
  Node 25 also works, but npm prints engine warnings because Vitest and jsdom
  officially support only even-numbered (LTS) releases.

If you need them: `brew install python@3.13 node@24`, or use `nvm install 24`.

### Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Frontend

```bash
cd frontend
npm install
```

## Running

Use two terminals.

**Terminal 1: API (http://127.0.0.1:8000, docs at /docs)**

```bash
cd backend
source .venv/bin/activate
uvicorn app.main:app --reload --port 8000
```

**Terminal 2: UI (http://localhost:5173)**

```bash
cd frontend
npm run dev
```

Open **http://localhost:5173**. Use `localhost`, not `127.0.0.1`, because
Vite listens on the IPv6 loopback by default. The dev server proxies `/api`
to the backend, so no CORS setup is needed.

## API (Phase 1)

| Method | Path | Description |
| --- | --- | --- |
| GET | `/api/health` | Liveness check |
| GET | `/api/simulation` | Current config, tick and services |
| POST | `/api/simulation` | Start a new simulation from a `SimulationConfig` body |
| GET | `/api/network` | All devices and connections |
| GET | `/api/network/devices/{device_id}` | One device (404 if unknown, 422 if malformed ID) |
| GET | `/api/services` | City services and their device dependencies |

Example: start a reproducible simulation.

```bash
curl -X POST http://127.0.0.1:8000/api/simulation \
  -H 'Content-Type: application/json' \
  -d '{"seed": 2024, "difficulty": "challenging", "tick_minutes": 30}'
```

`SimulationConfig` fields: `seed` (0–4294967295), `city_name`,
`difficulty` (`training` | `standard` | `challenging`), `starting_budget`
(0–10,000,000), `tick_minutes` (1–240). Unknown fields are rejected.

## Testing

```bash
# Backend (from backend/, venv active)
python -m pytest

# Frontend (from frontend/)
npm test             # Vitest, single run
npm run typecheck    # TypeScript
npm run build        # typecheck + production build
```

Backend tests cover health, model validation, sample-network integrity,
API error responses and seeded determinism. Frontend tests cover the
device details panel, Cytoscape element mapping, the API client's error
handling and the command-center page (with the canvas map mocked).

## Current limitations

- **No gameplay yet.** The clock doesn't advance, no security events are
  generated, and service statuses never change. These panels are clearly
  marked *Placeholder*.
- **In-memory state.** Restarting the API resets the simulation. There is
  one shared simulation per server process, with no users or sessions.
- **Fixed topology.** `POST /api/simulation` reseeds the bundled sample
  network. It can't load custom networks yet.
- **Hand-synced types.** `frontend/src/types` mirrors the Pydantic models
  manually.
- **Bundle size.** Cytoscape makes the production JS bundle about 670 KB
  (about 210 KB gzipped), and Vite warns about it. Code-splitting can wait
  until there are more pages.
- **Desktop only.** The layout targets 1280 px and wider screens.
