# MarineWatch (Offshore Monitor)

[![CI](https://github.com/kritikarunam30/MarineWatch/actions/workflows/ci.yml/badge.svg)](https://github.com/kritikarunam30/MarineWatch/actions/workflows/ci.yml)
[![Python 3.11](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg)](https://fastapi.tiangolo.com)
[![PostGIS 16](https://img.shields.io/badge/PostGIS-16--3.4-336791.svg)](https://postgis.net/)
[![React 19](https://img.shields.io/badge/React-19-61DAFB.svg)](https://react.dev/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**MarineWatch** is an automated offshore environmental monitoring platform. It detects oil slicks, offshore platforms, dark vessels, flaring spikes, and shipping-lane NO₂ emissions across offshore oil and gas basins, while simulating slick drift toward coastlines and backward to pinpoint likely sources.

---

## Features

- **Satellite & Sensor Ingestion**: Standardized source interfaces with pluggable `fixture`, `live`, and `replay` modes for Copernicus Sentinel-1 SAR, Sentinel-5P NO₂, VIIRS Nightfire flaring, ERA5 atmospheric winds, Copernicus ocean currents, Global Fishing Watch (GFW) AIS, and OpenStreetMap/GEM infrastructure.
- **Deep Learning & Spatial Detection**:
  - Oil slick segmentation from Sentinel-1 SAR imagery.
  - Platform and vessel detection via CFAR screening and CNN classification.
  - Gas flaring spike detection from VIIRS Nightfire shortwave/MWIR observations.
  - Shipping-lane NO₂ enhancement calculations against tropospheric baselines.
- **Drift Simulation & Origin Attribution**:
  - Forward trajectory modeling predicting coastal arrival times, impacted shoreline, and sensitive marine habitats (mangroves, coral reefs, fisheries).
  - Backward drift backtracking to rank suspect platforms and vessels.
- **Anomaly Detection & Geo-Fenced Alerts**:
  - Rolling median absolute deviation (MAD) baselines per offshore platform.
  - Polygon-based watchlists sending alerts upon slick or flaring exceedance.
- **Interactive Geospatial Dashboard**:
  - Fast, responsive MapLibre GL vector basemap with live layer toggles, incident playback, and health status indicators.
  - RESTful API with automated OpenAPI / Swagger documentation.

---

## Project Structure

```
MarineWatch/
├── .github/
│   └── workflows/
│       └── ci.yml               # GitHub Actions CI pipeline (lint, types, tests, build)
├── api/
│   ├── routers/                 # Modular API routers per domain resource
│   ├── __init__.py
│   └── main.py                  # FastAPI application entrypoint and route table
├── pipeline/
│   ├── db/
│   │   ├── migrations/          # Alembic database migrations with PostGIS GiST indexes
│   │   ├── alembic_filters.py   # Alembic autogenerate filters for PostGIS system objects
│   │   ├── geo.py               # PostGIS WKB <-> GeoJSON conversion helpers
│   │   ├── models.py            # SQLAlchemy 2 declarative models for all contract tables
│   │   └── session.py           # Database engine and session dependency
│   ├── jobs/
│   │   ├── __init__.py
│   │   └── worker.py            # APScheduler worker process for scheduled tasks
│   ├── sources/
│   │   ├── __init__.py
│   │   └── base.py              # Source protocol, get_source() factory, and DATA_MODE switch
│   ├── basins.py                # Candidate basin AOI polygons (Mumbai High, Krishna-Godavari)
│   ├── config.py                # Pydantic Settings loaded from .env
│   └── schemas.py               # Shared Pydantic contracts & GeoJSON Feature converters
├── frontend/
│   ├── src/
│   │   ├── App.tsx              # Root React component with status badge overlay
│   │   ├── MapView.tsx          # Fullscreen MapLibre GL map container
│   │   ├── health.ts            # API health polling hook and contracts
│   │   ├── index.css            # Map and HUD styling
│   │   └── main.tsx             # Application bootstrap
│   ├── eslint.config.js         # ESLint configuration
│   ├── package.json             # Frontend dependencies and scripts
│   ├── tsconfig.json            # TypeScript configuration
│   └── vite.config.ts           # Vite bundler configuration
├── scripts/
│   ├── __init__.py
│   └── seed.py                  # Database seed script for basins and reference data
├── tests/
│   ├── conftest.py              # Pytest fixtures and conditional PostGIS test markers
│   ├── integration/
│   │   └── test_migrations.py   # Migration and PostGIS spatial index validation
│   └── unit/
│       ├── test_api.py          # API route and health status unit tests
│       ├── test_models.py       # SQLAlchemy model and GeoJSON roundtrip tests
│       ├── test_schemas.py      # Pydantic schema validation tests
│       └── test_sources.py      # Source protocol and data mode switch tests
├── data/                        # Local scene/raster cache (git-ignored)
├── ml/weights/                  # Model weights (git-ignored)
├── .dockerignore                # Docker build exclusions
├── .env.example                 # Template for environment variables and secrets
├── .gitignore                   # Comprehensive gitignore rules
├── Dockerfile                   # Multi-service container image for API and worker
├── Makefile                     # Developer automation commands
├── docker-compose.yml           # Local multi-container orchestration
├── pyproject.toml               # Python dependencies, Ruff, Mypy, and Pytest configuration
├── IMPLEMENTATION_PLAN.md       # Phased roadmap and engineering specifications
└── README.md                    # Project documentation
```

---

## Quick Start (Docker Compose)

The easiest way to run the entire stack (PostGIS database, FastAPI backend, worker, and Vite frontend) is with Docker Compose:

1. **Clone the repository and prepare environment variables**:
   ```sh
   git clone https://github.com/kritikarunam30/MarineWatch.git
   cd MarineWatch
   cp .env.example .env
   ```
   *(Default credentials in `.env.example` work out of the box in fixture mode without external API keys).*

2. **Start all services**:
   ```sh
   make up
   ```
   This launches:
   - **PostGIS 16**: `localhost:5432`
   - **FastAPI API**: http://localhost:8000 (Interactive docs at http://localhost:8000/docs)
   - **Worker Process**: Background scheduler running in container
   - **Web Dashboard**: http://localhost:5173

3. **Seed initial basin geometries**:
   ```sh
   make seed
   ```

4. **Stop services**:
   ```sh
   make down
   ```

---

## Local Development (Without Docker)

### Prerequisites

- **Python**: 3.11+
- **Node.js**: 20+ (with `npm`)
- **PostGIS**: PostgreSQL 16 with PostGIS extension (optional for unit tests; required for migrations)

### 1. Python Backend Setup

```sh
# Create and activate virtual environment
python -m venv .venv

# On Linux/macOS:
source .venv/bin/activate
# On Windows (PowerShell):
.venv\Scripts\Activate.ps1

# Install editable package with dev dependencies
make install
```

### 2. Frontend Setup

```sh
cd frontend
npm ci
cd ..
```

### 3. Run Automated Quality Checks

Run all linters, type checks, and tests across Python and TypeScript in one command:

```sh
make check
```

Or run individual checks:

```sh
make lint            # Ruff linting & formatting checks
make typecheck       # Mypy strict type checking
make test            # Pytest test suite
make frontend-check  # Frontend ESLint, TypeScript check & Vitest suite
```

---

## Configuration & Data Modes

All runtime configuration is managed through environment variables or a `.env` file (see [`.env.example`](.env.example)).

### Data Modes (`DATA_MODE`)

| Mode | Description | External Keys Required? |
|---|---|---|
| `fixture` *(default)* | Uses pre-recorded GeoTIFFs, NetCDFs, and GeoJSON in `tests/fixtures/`. | **No** — Runs entirely offline. |
| `live` | Fetches live observations from Earth Engine, Copernicus Marine, VIIRS, and GFW APIs. | **Yes** — Requires API tokens in `.env`. |
| `replay` | Replays historical incidents (e.g., 2017/2023 Ennore, 2025 MSC Elsa 3) for deterministic validation. | Uses local replay cache. |

### Key Environment Variables

- `BASIN_ID`: Active basin (`mumbai_high` or `kg_basin`).
- `DATABASE_URL`: Connection string for PostgreSQL/PostGIS.
- `EE_PROJECT`: Google Earth Engine project ID.
- `GFW_API_TOKEN`: Global Fishing Watch API token.
- `COPERNICUSMARINE_SERVICE_USERNAME` / `PASSWORD`: Copernicus Marine credentials.
- `EOG_USERNAME` / `PASSWORD`: Earth Observation Group credentials for VIIRS Nightfire.

---

## Makefile Command Reference

| Target | Description |
|---|---|
| `make install` | Installs Python package in editable mode with `[dev]` and frontend npm dependencies. |
| `make up` | Starts PostGIS, API, worker, and frontend via Docker Compose. |
| `make down` | Stops and removes Docker Compose containers. |
| `make logs` | Streams logs from all Docker Compose services. |
| `make migrate` | Applies pending Alembic database migrations. |
| `make seed` | Seeds initial basin polygons into PostGIS. |
| `make check` | Runs the full verification pipeline (`lint`, `typecheck`, `test`, `frontend-check`). |
| `make lint` | Runs Ruff linter and formatting validation. |
| `make typecheck` | Runs Mypy strict type checking. |
| `make test` | Executes Pytest test suite (unit and integration tests). |
| `make frontend-check` | Runs ESLint, TypeScript `tsc --noEmit`, and Vitest tests on the frontend. |

---

## Implementation Roadmap

Project implementation is organized into sequential phases documented in [`IMPLEMENTATION_PLAN.md`](IMPLEMENTATION_PLAN.md):

- [x] **Phase 1: Repository Architecture, Database Schema & Contracts**
  - PostGIS 16 schema with 16 contract tables and GiST spatial indexes
  - Alembic migrations with spatial filter helpers
  - Shared Pydantic schemas with GeoJSON Feature / FeatureCollection converters
  - Extensible source protocol with `fixture` / `live` dispatch
  - FastAPI application with `/health` and planned route registry
  - React + MapLibre GL vector map with health status HUD
  - GitHub Actions CI pipeline
- [ ] **Phase 2**: Reference Data & Offshore Infrastructure Registry (OSM, GEM, GFW)
- [ ] **Phase 3**: Ingest Layer (Sentinel-1, Sentinel-5P, ERA5, Currents, VIIRS Nightfire)
- [ ] **Phase 4**: Oil Slick Detection Model (SAR U-Net segmentation)
- [ ] **Phase 5**: Offshore Platform & Vessel Detector (CFAR + CNN)
- [ ] **Phase 6**: Rule Detectors, Statistical Confidence & Event Fusion
- [ ] **Phase 7**: Slick Drift Modeling, Origin Attribution & Coastal Impact
- [ ] **Phase 8**: Historical Baselines, Platform Alerts & Geo-Fenced Watchlists
- [ ] **Phase 9**: REST API Endpoints & PDF Evidence Report Generation
- [ ] **Phase 10**: Pipeline Orchestration, Live Demo & Historical Incident Replay

---

## License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
