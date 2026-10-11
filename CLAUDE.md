# Offshore Monitor
Detects oil slicks, platforms, vessels, flaring and shipping-lane NO2 over one offshore basin;
simulates slick drift to the coast and backward to likely sources.

## Rules
- Python 3.11, FastAPI, SQLAlchemy 2 + GeoAlchemy2, Alembic, PostGIS 16. Frontend: Vite + React + TypeScript.
- Every data source implements the interface in `pipeline/sources/base.py` with `fixture` and `live` versions.
  Tests use fixtures only. Never call Earth Engine, Global Fishing Watch or Copernicus in tests.
- All geometry is EPSG:4326 in the DB; use a local UTM CRS for distances and areas.
- Shared schemas live in `pipeline/schemas.py` (Pydantic). Change them only with a migration and a note in this file.
- Large files (scenes, chips, weights, datasets) go in `data/` or `ml/weights/` and are git-ignored.
- Secrets come from `.env` (see `.env.example`). Never hard-code keys.
- Run `make check` (ruff, mypy, pytest, eslint, vitest) before saying a task is done.

## Layout notes
- The repo root is the `offshore-monitor/` folder from the implementation plan.
- DB models: `pipeline/db/models.py`. Migrations: `pipeline/db/migrations/` (`alembic.ini` at the root).
- API: unbuilt resources are listed in `PLANNED_ROUTES` in `api/main.py` (answer `501`). When a phase builds one,
  remove its entry and add `api/routers/<resource>.py`, included in `create_app()`.
- Tests marked `@pytest.mark.db` need PostGIS at `DATABASE_URL`; they are skipped when it is unreachable.
- Sources: add `pipeline/sources/<name>.py` with classes `Fixture` and `Live` (optional `Replay`). `get_source(name)`
  picks one by `DATA_MODE`; replay falls back to `Fixture`. No registry or stub modules.
- Create a phase's modules when the phase starts; no empty placeholders.

## Status
- Phase: 1 done and simplified (see "Phase 1 simplification" in IMPLEMENTATION_PLAN.md)
- Basin: <Mumbai High | Krishna-Godavari>
- Replay incident: <chosen incident + scene IDs>
- Known issues: none yet
