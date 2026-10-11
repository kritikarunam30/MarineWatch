# Offshore Oil and Gas Emissions Monitor: Implementation Plan for Claude Code

**Last completed phase: Phase 1 (Repo, database and contracts)**

Built from the project plan dated 8 October 2026 (14 features, 37.5 person-days). The plan is split into 11 phases. Each phase can be handed to Claude Code as a single session: paste the phase section, let it plan, then build until the "Done when" checks pass.

---

## How to use this plan with Claude Code

1. **One phase per session.** Start each session in plan mode, paste the phase section (plus the "Shared contracts" section the first time), and approve the plan before it writes code.
2. **Tests are the gate.** Every phase ends with commands that must pass. Ask Claude Code to run them and fix failures before you commit.
3. **Fixture mode first, live data second.** Every data source has a `fixture` implementation (small files in `tests/fixtures/`) and a `live` implementation. Claude Code builds and tests against fixtures, so it never needs your Earth Engine login, and the demo still runs if the internet fails.
4. **Humans do what Claude Code can't:** creating accounts and API keys, authenticating Earth Engine, running GPU training on Colab or Kaggle, and judging whether a slick mask looks right. These are marked **[Human]**.
5. **Commit after every phase** with a tag (`phase-3-done`) so you can roll back.
6. **Keep `CLAUDE.md` current.** Update the "Status" block at the end of each phase so the next session starts with context.

### `CLAUDE.md` to put at the repo root (Phase 1 creates it)

```markdown
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

## Status
- Phase: <update each phase>
- Basin: <Mumbai High | Krishna-Godavari>
- Replay incident: <chosen incident + scene IDs>
- Known issues: <list>
```

---

## Phase overview

| Phase | Name | Features | Est. person-days | Can run in parallel with |
|---|---|---|---|---|
| 0 | Access and risk checks | open items | 1.5 | — |
| 1 | Repo, database and contracts | arch 3, 8 | 2.5 | — |
| 2 | Reference data and offshore registry | 16 | 2 | 3, 4, 5 |
| 3 | Ingest layer (live + fixtures + replay cache) | arch 7 | 2.5 | 2, 4, 5 |
| 4 | Model 1: oil slick U-Net | 9, arch 6 | 3.5 | 2, 3, 5 |
| 5 | Model 2: platform and vessel detector | 11, arch 6 | 3.5 | 2, 3, 4 |
| 6 | Rule detectors, confidence and fusion | 12, 15, 21, arch 3 | 5 | 7 |
| 7 | Drift, attribution and coastal impact | 13, 14, 31 | 6.75 | 6 |
| 8 | Platform history, alerts and watchlists | 22, 23, 33 | 5.25 | 9 |
| 9 | API, dashboard and evidence reports | 32, 34 | 4.25 | 8 |
| 10 | Orchestration, live + replay demo, hardening | arch 11, integration, demo prep | 5 | — |
| | **Total** | **14** | **≈ 41** (37.5 + ~3.5 contingency for setup) | |

With 4 people the critical path is roughly Phase 0 → 1 → (2–5 in parallel) → (6, 7) → (8, 9) → 10, which is about 10–12 working days.

---

## Shared contracts (give to Claude Code in Phase 1)

### Repository layout

```
offshore-monitor/
  CLAUDE.md  Makefile  docker-compose.yml  .env.example
  pipeline/                 # Python package: all science and processing
    config.py               # settings from env (DATA_MODE=fixture|live, BASIN_ID, ...)
    schemas.py              # Pydantic models shared by pipeline and API
    db/  models.py  session.py  migrations/ (Alembic)
    sources/                # one module per data source, fixture + live
      base.py  sentinel1.py  sentinel5p.py  era5.py  currents.py  nightfire.py
      gfw.py  osm.py  gem.py  reference_layers.py
    registry/               # feature 16
    detect/
      slick.py              # feature 9 inference
      objects.py            # feature 11 inference (CFAR + CNN)
      flaring.py            # feature 12
      no2_lanes.py          # feature 15
      confidence.py         # feature 21
    fuse/events.py          # rule-based late fusion
    drift/                  # features 13, 14
    impact/coastal.py       # feature 31
    temporal/               # features 22, 23
    alerts/                 # feature 33
    reports/                # feature 34 (templates/ + render.py)
    jobs/                   # APScheduler jobs + replay runner
  api/                      # FastAPI app, routers per resource
  ml/
    slick_unet/             # dataset.py  train.py  eval.py  export.py  colab.ipynb
    object_detector/        # cfar.py  dataset.py  train.py  eval.py  colab.ipynb
    weights/                # git-ignored, *.pt / *.onnx
  frontend/                 # Vite + React + TS, MapLibre, deck.gl
  scripts/                  # one-off checks and seeding
  tests/  fixtures/  unit/  integration/  e2e/
  data/                     # git-ignored cache (scenes, chips, drift runs, replay)
```

### Database tables (PostGIS, EPSG:4326)

| Table | Key columns |
|---|---|
| `basins` | id, name, geom (Polygon) |
| `platforms` | id, name, operator, type, geom (Point), sources (jsonb), first_seen, last_seen, confirmed_by_sar (bool) |
| `scenes` | id (S1 product ID), sensor, acquired_at, geom footprint, orbit, cached_path |
| `slick_detections` | id, scene_id, geom (MultiPolygon), area_km2, mean_wind_ms, lookalike_flags (jsonb), confidence |
| `object_detections` | id, scene_id, geom (Point), cls (platform/vessel/noise), score, length_px |
| `flares` | id, observed_at, geom, temp_k, rh_mw, platform_id (nullable), persistent (bool) |
| `no2_lane_stats` | id, period_start, period_end, lane_id, lane_mean, background_mean, enhancement_pct |
| `events` | id, kind (slick/flare_spike/new_slick_near_platform), geom, start_at, confidence, status |
| `event_members` | event_id, member_table, member_id |
| `drift_runs` | id, slick_id, direction (forward/backward), params (jsonb), tracks_geojson path, beached_geojson path |
| `suspects` | id, slick_id, platform_id or object_detection_id, score, overlap_score, distance_km, rank |
| `impacts` | id, slick_id, hours_to_shore, coastline_km, mangrove_ha, protected_areas (jsonb), fishing_zones (jsonb) |
| `platform_baselines` | platform_id, metric (flare_rh / slick_count), median, mad, window_days, updated_at |
| `alerts` | id, kind, platform_id, event_id, zscore, created_at, sent_at |
| `watchlists` | id, name, email, geom (Polygon), kinds (text[]) |
| `reports` | id, slick_id, pdf_path, created_at |

### Data source interface

```python
class Source(Protocol):
    name: str
    def fetch(self, aoi: Polygon, start: datetime, end: datetime, **kw) -> SourceResult: ...
# SourceResult = paths to cached files (GeoTIFF / NetCDF / CSV / GeoJSON) + metadata dict.
# get_source("sentinel1") returns the fixture or live class based on DATA_MODE.
```

Convention (no registry): each source is one module `pipeline/sources/<name>.py` that defines
classes named `Fixture` and `Live` (and optionally `Replay`). `get_source(name)` imports the
module and picks the class by `DATA_MODE`; replay mode uses `Fixture` until the module defines
`Replay`. A source whose module does not exist yet raises `NotImplementedError` naming the phase
that builds it (`SOURCE_PHASES` in `base.py`).

**Layout note:** the tree above is the target. Each phase creates its own folders and modules
when it fills them in; Phase 1 does not create empty placeholders.

---

## Phase 0: Access and risk checks (≈ 1.5 person-days)

**Goal:** Clear the open items that could sink the project before anyone writes production code.

**[Human]**
- Register a Google Cloud project for non-commercial Earth Engine use; run `earthengine authenticate` on the team machine.
- Get a free Global Fishing Watch API key (attribution required).
- Create a Copernicus Marine account; register with the Earth Observation Group for VIIRS Nightfire downloads.
- Fill in `.env` on one machine (never commit it).

**Claude Code tasks** (scripts in `scripts/`, run by a human with credentials)
1. `check_coverage.py --basin mumbai_high|kg_basin --months 12`: counts Sentinel-1 IW VV passes over each candidate basin per month (`COPERNICUS/S1_GRD`), and prints revisit gaps. Pick the basin with more passes.
2. `find_incident_scenes.py`: for each candidate replay incident (2017 Ennore, 2023 Ennore, 2025 MSC Elsa 3 off Kerala), lists Sentinel-1 scenes within ±5 days and a bounding box; saves quick-look PNGs to `data/quicklooks/`.
3. `probe_sources.py`: one tiny request to every live source (EE S1, S5P NO2, ERA5 winds, HYCOM in EE, Copernicus Marine, Nightfire, GFW) and prints OK / error, so access problems surface now.

**[Human] decision:** choose the basin and replay incident by looking at the quick-looks. Record both in `CLAUDE.md`.

**Done when:** all probes print OK; basin and incident chosen; at least one replay scene shows a visible dark slick.

---

## Phase 1: Repo, database and contracts (≈ 2.5 person-days)

**Goal:** A runnable skeleton where every later phase just fills in modules.

**Claude Code tasks**
1. Create the parts of the repo layout Phase 1 uses (`pipeline/`, `api/`, `scripts/`, `tests/`, `frontend/`, `data/`, `ml/weights/`), `pyproject.toml` (ruff, mypy, pytest), `Makefile` (`make up`, `make check`, `make seed`, `make replay` — the last prints a "phase 10" notice until then), `.env.example`, `CLAUDE.md`.
2. `docker-compose.yml` with `db` (postgis/postgis:16), `api` (FastAPI + uvicorn, runs `alembic upgrade head` on start), `worker` (APScheduler process), `frontend` (stock `node` image running the Vite dev server; no separate Dockerfile). Volume-mount `data/`.
3. SQLAlchemy + GeoAlchemy2 models for every table above; first Alembic migration; spatial indexes on all `geom` columns.
4. `pipeline/schemas.py` Pydantic models mirroring the tables, plus GeoJSON Feature/FeatureCollection helpers.
5. `pipeline/sources/base.py` with the `Source` protocol, `get_source()` and the `DATA_MODE` switch, using the `Fixture`/`Live` naming convention above. No stub source modules: Phases 2 and 3 add each module when they build it.
6. FastAPI app with `/health` and the planned routes `/basins`, `/platforms`, `/scenes`, `/slicks`, `/objects`, `/flares`, `/no2`, `/events`, `/drift`, `/suspects`, `/impacts`, `/alerts`, `/watchlists`, `/reports`, `/tiles`, declared in one `PLANNED_ROUTES` table in `api/main.py` that answers `501` with the phase number. Each phase replaces its entry with a real router in `api/routers/<resource>.py`.
7. Vite + React + TS frontend with a full-screen MapLibre map (free basemap style), calling `/health`.
8. GitHub Actions running `make check` against a PostGIS service container.

**Done when:** `make up` starts all four services; `alembic upgrade head` runs clean; `make check` passes; the map loads in the browser.

### Phase 1 simplification (changes from the first implementation)

The first Phase 1 build was simplified without changing what it does. All checks still pass
(ruff, mypy, pytest, eslint, tsc, vitest, frontend build; the migration renders the same
16 tables and 22 indexes).

| Area | Before | After |
|---|---|---|
| API route stubs | 15 router files + a stub-router helper (`api/routers/`) | One `PLANNED_ROUTES` table in `api/main.py`; same `501` responses naming the phase |
| Data sources | 9 stub modules with 18 stub classes, a decorator registry and a TypeVar | `get_source()` finds `Fixture`/`Live` classes by convention; missing modules raise `NotImplementedError` naming the phase |
| Placeholders | ~20 empty packages and docstring-only files for Phases 2–10 (`detect/`, `fuse/`, `drift/`, `impact/`, `temporal/`, `alerts/`, `reports/`, `registry/`, `ml/` packages, `jobs/replay.py`, `tests/e2e`, `tests/fixtures`) | Removed; each phase creates its own modules. Kept `data/` and `ml/weights/` (Docker mounts) |
| `make replay` | Ran a stub module that exited with an error | Prints a "phase 10" notice |
| Frontend container | Own `Dockerfile` + `.dockerignore` | Stock `node:24-alpine` image in Compose, whole `frontend/` mounted, `node_modules` kept in a container volume |
| Frontend code | `api.ts`, `useHealth.ts`, `StatusBadge.tsx`, `vite-env.d.ts`, `test/setup.ts` | `health.ts` (types, fetch, hook) and `StatusBadge` inside `App.tsx`; jest-dom loaded straight from `vite.config.ts` |
| Frontend dependencies | `eslint-plugin-react-refresh`, `globals` | Removed (typescript-eslint already handles browser globals) |
| Type check | `tsc -b` (wrote and committed `tsconfig.tsbuildinfo`) | `tsc --noEmit`; build artifact removed |
| Python dependencies | `uvicorn[standard]` | `uvicorn` (fewer native extras; `--reload` still works) |

Unchanged: the database models and migration, Pydantic schemas, `/health`, Docker Compose services, the worker,
`make seed`, CI, and the test gate (DB tests skip locally, required in CI).

---

## Phase 2: Reference data and offshore registry, feature 16 (≈ 2 person-days)

**Goal:** One de-duplicated table of offshore platforms for the chosen basin, plus the layers used later for impact.

**Claude Code tasks**
1. Loaders in `pipeline/sources/`:
   - `gfw.py`: Global Fishing Watch offshore infrastructure (oil/gas class only) for the basin AOI.
   - `osm.py`: platforms via Overpass (`man_made=offshore_platform`, `man_made=petroleum_well` offshore); cache the response.
   - `gem.py`: Global Energy Monitor oil and gas field points/polygons from a downloaded file.
   - `reference_layers.py`: coastline (Natural Earth 10m or OSM land polygons), Global Mangrove Watch, WDPA protected areas, fishing zones, World Bank shipping density raster. Each clipped to a basin buffer (e.g. 150 km) and stored as GeoPackage in `data/reference/`.
2. `registry/merge.py`: merge sources by distance in UTM (default 500 m), keep a `sources` jsonb with each origin ID, prefer GFW geometry, take names from OSM/GEM. Deterministic so reruns don't create duplicates.
3. `scripts/seed.py` (`make seed`): basin polygon, registry, reference layers into PostGIS.
4. API: `GET /platforms` (GeoJSON, bbox filter), `GET /platforms/{id}`.
5. Fixtures: 20 fake platforms across the three sources with known duplicates; tests assert the merge result.

**Done when:** live seed produces a plausible platform count for the basin (spot-check 5 on a map); merge unit tests pass; `/platforms` returns GeoJSON.

---

## Phase 3: Ingest layer, live + fixtures + replay cache (≈ 2.5 person-days)

**Goal:** Every detector can ask for data the same way, offline or online.

**Claude Code tasks**
1. `sentinel1.py` (live): list `COPERNICUS/S1_GRD` IW scenes with VV over the basin for a date range; download VV (dB) as 512×512 or 1024×1024 chips at 10–20 m using `ee.data.computePixels` (small synchronous requests, no Drive export). Also store the land mask. Write chips as GeoTIFF + a scene record.
2. `sentinel5p.py`: `COPERNICUS/S5P/OFFL/L3_NO2`, band `tropospheric_NO2_column_number_density`, monthly/quarterly means over the basin as GeoTIFF.
3. `era5.py`: hourly 10 m u/v winds for the AOI and a time window, saved as NetCDF that OpenDrift can read (check the current ERA5 hourly collection ID in the EE catalog; fall back to the Copernicus CDS API if needed).
4. `currents.py`: surface currents from Copernicus Marine (`copernicusmarine` toolbox, global physics analysis/forecast) with HYCOM in EE (`HYCOM/sea_water_velocity`) as a fallback; NetCDF output.
5. `nightfire.py`: download nightly VIIRS Nightfire CSVs for the date range, filter to the basin.
6. Earth Engine tile endpoint: `GET /tiles/s1/{scene_id}` returns a fresh `getMapId` tile URL template (tokens expire, so the API refreshes them); same for S5P NO2 means.
7. **Replay cache:** `scripts/cache_replay.py --incident <id>` stores all S1 chips, winds, currents and Nightfire data for the incident window under `data/replay/<id>/`, and a manifest. `DATA_MODE=replay` reads only from there.
8. Fixtures: tiny real or synthetic files for every source (a 256×256 S1 chip with a dark patch, 2 days of winds and currents on a coarse grid, 30 Nightfire rows, one NO2 GeoTIFF).

**Done when:** `pytest tests/unit/sources` passes with fixtures; a live run fetches one week of S1 chips for the basin; `make cache-replay` produces a complete replay folder; the S1 tile URL renders in the frontend map.

---

## Phase 4: Model 1, oil slick U-Net, feature 9 (≈ 3.5 person-days)

**Goal:** A slick segmentation model that works on Earth Engine Sentinel-1 chips, not just on the public dataset.

**Claude Code tasks**
1. `ml/slick_unet/dataset.py`: loaders for the public Sentinel-1 oil-spill datasets you pick (candidates: the MKLab/Krestenitis oil spill detection dataset, the SOS Deep-SAR dataset; check each licence). Map their classes to `oil` vs `background` (treat look-alikes as background, keep a separate look-alike label for evaluation). Normalise to match EE dB values (EE GRD is calibrated and terrain-corrected differently from SNAP; standardise per chip and clip dB range).
2. Augmentations (flips, rotations, speckle-like noise, dB shifts) with albumentations.
3. `train.py`: segmentation-models-pytorch U-Net (ResNet34 encoder, 1 input channel), Dice + BCE loss, mixed precision, checkpointing, IoU/F1 logging. `colab.ipynb` that clones the repo, downloads data, trains, and saves `slick_unet.pt` + ONNX export.
4. `eval.py`: IoU, F1, precision/recall on the test split and on a **hand-labelled set of 20–40 EE chips** from your basin and replay incident (label in QGIS or CVAT as polygons; a script rasterises them).
5. `pipeline/detect/slick.py`: tiled inference with overlap, CPU-friendly (ONNX Runtime), threshold → polygons (rasterio.features.shapes), drop tiny areas and land, compute area_km2 and mean ERA5 wind under the slick, write `slick_detections`.
6. Look-alike flags: wind < 2–3 m/s (calm-water look-alike), wind > 10–12 m/s (slicks unlikely to be visible), touching coast, very low contrast. Stored in `lookalike_flags` for feature 21.

**[Human]** run training on Colab/Kaggle; label the EE validation chips; eyeball 10 predictions.

**Done when:** EE validation IoU is reported in `ml/slick_unet/RESULTS.md`; if it drops sharply vs the public test set, fine-tune on the labelled EE chips (the plan's open item); inference on the replay scene produces a sensible mask; unit tests pass with a tiny stub model.

---

## Phase 5: Model 2, platform and vessel detector, feature 11 (≈ 3.5 person-days)

**Goal:** Point detections classed as platform, vessel or noise, with platforms confirmed by persistence.

**Claude Code tasks**
1. `ml/object_detector/cfar.py`: two-parameter CFAR on linear sigma0 (guard + background windows, configurable false-alarm rate), land-masked, connected components → candidate points with size features.
2. `dataset.py`: build 64×64 chips around xView3-SAR labels for a **regional subset** of scenes (the full dataset is very large). Labels: vessel, fixed infrastructure (platform), and noise from CFAR hits that match no label. Add GFW infrastructure points over your basin as extra platform positives.
3. `train.py`: small CNN (or ResNet18 with 1–2 channels, VV and VH if available) for 3 classes; class weighting; `colab.ipynb`; export ONNX.
4. `pipeline/detect/objects.py`: CFAR → classify → write `object_detections`.
5. `registry/persistence.py`: a "platform" detection that appears at the same spot (≤ 200 m) in ≥ N of the last M scenes is persistent; match to `platforms` and set `confirmed_by_sar`; unmatched persistent objects become candidate new platforms.
6. Evaluation: precision/recall per class on held-out xView3 chips; match rate of persistent detections vs registry for the basin.

**Done when:** `RESULTS.md` has per-class metrics; at least most registered platforms in the basin are confirmed by persistence over a month of scenes; tests pass with a stub model.

---

## Phase 6: Rule detectors, confidence and fusion, features 12, 15, 21 (≈ 5 person-days)

**Goal:** Gas-side detections plus one merged, scored event table.

**Claude Code tasks**
1. `detect/flaring.py` (12): filter Nightfire rows by temperature (gas flares typically burn far hotter than biomass fires; make the threshold configurable, start around 1,400–1,600 K) and persistence (seen on ≥ k nights in a rolling window); match to the nearest platform within ~1 km; write `flares`.
2. `detect/no2_lanes.py` (15): build lane polygons from the World Bank shipping density raster (threshold high-traffic cells, buffer, minus platform buffers); background = nearby open-sea cells with low traffic; compute lane mean vs background per month/quarter from S5P means; store `enhancement_pct`. Keep this module self-contained so it can be dropped (optional trim).
3. `detect/confidence.py` (21): weighted score 0–1 from wind-speed window, look-alike flags, scene quality (incidence angle, edge of swath, land proximity), and number of overpasses that confirm the slick. Weights in config, documented in the module docstring.
4. `fuse/events.py`: rule-based late fusion. Group slicks, flares, platforms and vessel detections that are close in space (e.g. ≤ 5 km) and time (e.g. ≤ 24 h) into one `event`; event confidence from members; idempotent reruns.
5. Tests with fixtures covering: a flare matched to a platform, a non-persistent flare ignored, a slick near a vessel and a platform merged into one event, a low-wind slick getting low confidence.

**Done when:** running the pipeline on the replay folder fills `flares`, `events` and confidence values; all rule tests pass; `/events`, `/flares`, `/no2` return data.

---

## Phase 7: Drift, attribution and coastal impact, features 13, 14, 31 (≈ 6.75 person-days)

**Goal:** For any slick: where it goes, when it hits the coast, what it hits, and who probably caused it.

**Claude Code tasks**
1. `drift/forward.py` (13): OpenDrift **OpenOil** seeded inside the slick polygon (e.g. 2,000 particles), readers for the cached ERA5 winds and currents NetCDF, 72–120 h run, hourly output. Save particle tracks (thinned) as GeoJSON for deck.gl TripsLayer (`[lon, lat, timestamp]` paths) and stranded particles as GeoJSON.
2. `drift/backward.py` (13): backward run with OpenDrift **OceanDrift** (passive particles; oil weathering isn't meaningful backward) using a negative time step, 24–72 h, wind drift factor around 2–3%. Save tracks the same way.
3. Run drift in a worker process with a timeout; cache by (slick_id, direction, params hash).
4. `drift/suspects.py` (14): for each platform and radar-detected vessel (vessels from scenes before the slick), score = overlap of the object with the backward-track density (KDE or hex-bin) weighted by time, plus a distance-to-slick-head term; normalise and rank; store top N in `suspects` with component scores so the report can explain them. No AIS.
5. `impact/coastal.py` (31): intersect stranded particles and forward-track hulls with coastline, mangroves, WDPA and fishing zones; earliest stranding time → `hours_to_shore`; affected coastline km, mangrove ha, names of protected areas and fishing zones.
6. Tests: synthetic uniform eastward current must move particles east; backward run reverses direction; a platform sitting on the backward track outranks one 50 km away; a slick far offshore with offshore winds gives no stranding.

**Done when:** on the replay slick, forward drift reaches (or credibly approaches) the coast in the documented direction, suspects are ranked with explanations, impacts are stored; tests pass; `/drift/{slick_id}`, `/suspects/{slick_id}`, `/impacts/{slick_id}` return data.

---

## Phase 8: Platform history, alerts and watchlists, features 22, 23, 33 (≈ 5.25 person-days)

**Goal:** Turn one-off detections into monitoring.

**Claude Code tasks**
1. `temporal/baseline.py` (22): per platform, daily series of flare radiant heat and slick count within a buffer (e.g. 5 km); robust z-score `0.6745 × (x − median) / MAD` over a rolling window (e.g. 90 days); handle MAD = 0 and short series (minimum history rule). Store in `platform_baselines`. Backfill script for 6–12 months of Nightfire.
2. `temporal/alerts.py` (23): alert when flaring z-score > 3.5, or a new slick appears inside a platform buffer; de-duplicate alerts per platform per day.
3. `alerts/watchlists.py` (33): CRUD for watchlists (polygon, email, kinds); when an event, forward-drift hull or flare spike intersects a watchlist geometry, queue an alert. Optional trim: keep the code separate so the dashboard event list can stand in.
4. `alerts/email.py`: SMTP sender with Jinja2 HTML email (event summary, map thumbnail, link to the dashboard); MailHog in docker-compose for local testing.
5. API: `/platforms/{id}/history`, `/alerts`, `/watchlists` CRUD.

**Done when:** a synthetic flaring spike in fixtures triggers exactly one alert; a watchlist on the replay coastline receives an email in MailHog during replay; tests pass.

---

## Phase 9: API, dashboard and evidence reports, features 32, 34 (≈ 4.25 person-days)

**Goal:** Everything the judges see.

**Claude Code tasks: dashboard (32)**
1. Map page: MapLibre basemap, `@deck.gl/mapbox` `MapboxOverlay` for deck.gl layers. Layers with toggles: basin outline, platforms (colour by confirmed/unconfirmed, flaring now), vessels, tonight's flares, S1 radar tiles (EE), slick masks, NO2 lane enhancement, mangroves/WDPA/fishing zones.
2. Drift playback: `TripsLayer` for forward and backward tracks, time slider with play/pause, stranded particles, hours-to-shore badge.
3. Slick panel: radar chip vs U-Net mask side by side, confidence breakdown, suspects table with component scores, impact summary, "Generate report" button.
4. Platform page: flaring time series (Recharts) with baseline band and flagged spikes, nearby slicks, alerts.
5. Event list sidebar with filters; replay vs live banner; watchlist drawing tool (polygon draw → `POST /watchlists`).
6. Vitest tests for data hooks and components; one Playwright e2e test that loads the map in replay mode and opens the replay slick.

**Claude Code tasks: evidence report (34)**
7. `reports/render.py`: Jinja2 + WeasyPrint PDF per slick: scene ID and time, radar chip and mask PNGs, confidence and look-alike checks, drift map (static PNG from matplotlib/cartopy or contextily), suspects with reasoning, coastal risk, data sources and attribution (GFW, Copernicus, EOG), method notes and limits. `POST /reports/{slick_id}` → PDF path; `GET` downloads it.

**Done when:** the full demo storyline (section 6 of the project plan) can be clicked through in replay mode; the PDF renders with every section filled; Playwright test passes.

---

## Phase 10: Orchestration, live + replay demo, hardening (≈ 5 person-days)

**Goal:** A demo that works live, and still works if the venue Wi-Fi doesn't.

**Claude Code tasks**
1. `jobs/scheduler.py` (APScheduler in the `worker` service): new S1 passes every few hours → slicks + objects → fusion → drift for new slicks → impact → suspects → alerts; Nightfire nightly → flares → baselines → alerts; S5P monthly → lane stats. Each job logs to a `job_runs` table and is idempotent.
2. `jobs/replay.py` (`make replay`): runs the full pipeline on `data/replay/<incident>/` with a time cursor, so events appear in order during the demo.
3. End-to-end integration test: fresh DB → seed → replay → assert slick, drift, suspects, impacts, alert and report exist.
4. Hardening: retries and timeouts for live sources; fall back to the last cached result with a "stale" flag in the UI; structured logging; `/health` reports per-source status.
5. Deployment: one VM with Docker Compose, Caddy or nginx for HTTPS, `.env` on the VM, a nightly DB dump.
6. Offline pack: `make offline-pack` bundles the replay data, a DB dump and built frontend so the demo runs on a laptop without internet.

**[Human]** demo script, screen recording of the full storyline as a backup, slides.

**Done when:** the end-to-end test passes in CI; the live dashboard shows tonight's flares and the latest S1 pass for the basin; the offline pack runs on a second laptop.

---

## Risks and fallbacks

| Risk | Early signal | Fallback |
|---|---|---|
| U-Net trained on public data fails on EE scenes | Phase 4 EE validation IoU low | Fine-tune on 30–50 labelled EE chips; tune normalisation |
| Replay incident not captured by Sentinel-1 | Phase 0 quick-looks show nothing | Use another documented spill with clear S1 coverage (any region) for the replay only |
| xView3 too big or slow to prepare | Phase 5 day 1 | Fewer scenes; train only platform vs vessel vs noise on CFAR chips |
| OpenDrift data readers fail on cached NetCDF | Phase 7 day 1 | Constant wind + current from cached means as a simple reader; flag "simplified" in UI |
| EE quota or token expiry during demo | Phase 10 live test | Replay mode with cached tiles (save PNG tiles for the demo bbox) |
| Time runs short | Behind after Phase 7 | Drop feature 15 (NO2 lanes) then feature 33 (watchlists), as the project plan allows |

## Suggested team split (4 people)

- **Data and platform:** Phases 1, 3, 10 (owns docker, ingest, scheduler, deployment).
- **ML:** Phases 4 and 5 (owns datasets, Colab training, evaluation).
- **Geo and physics:** Phases 2, 6, 7 (owns registry, rules, fusion, OpenDrift, attribution, impact).
- **Product:** Phases 8 and 9 (owns baselines, alerts, dashboard, reports), starting the dashboard against fixture API responses from Phase 1 onwards.
