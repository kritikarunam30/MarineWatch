# Offshore Monitor

Detects oil slicks, platforms, vessels, flaring and shipping-lane NO2 over one offshore basin,
and simulates slick drift to the coast and backward to likely sources.
See `offshore-monitor-implementation-plan.md` for the phased plan.

## Quick start

```sh
cp .env.example .env      # fill in keys later; fixture mode needs none
make up                   # db (PostGIS 16), api, worker, frontend
make seed                 # candidate basin polygons
```

- API docs: http://localhost:8000/docs (`/health` reports data mode and DB status)
- Map: http://localhost:5173

## Development without Docker

```sh
python -m venv .venv && . .venv/bin/activate   # Windows: .venv\Scripts\activate
make install
make check        # ruff, mypy, pytest, eslint, tsc, vitest
```

Tests marked `db` need PostGIS at `DATABASE_URL` and are skipped when it is unreachable
(CI sets `REQUIRE_DB=1` so they always run there).

## Data modes

`DATA_MODE=fixture|live|replay`. Every source in `pipeline/sources/` has a fixture and a live
implementation, chosen by `get_source(name)`. Tests only use fixtures.
