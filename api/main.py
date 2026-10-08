from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from api.routers import (
    alerts,
    basins,
    drift,
    events,
    flares,
    impacts,
    no2,
    objects,
    platforms,
    reports,
    scenes,
    slicks,
    suspects,
    tiles,
    watchlists,
)
from pipeline.config import get_settings
from pipeline.db.session import get_engine
from pipeline.schemas import Health

VERSION = "0.1.0"
ROUTERS = [
    basins, platforms, scenes, slicks, objects, flares, no2, events,
    drift, suspects, impacts, alerts, watchlists, reports, tiles,
]  # fmt: skip


def database_ok() -> bool:
    try:
        with get_engine().connect() as conn:
            conn.execute(text("SELECT 1"))
    except SQLAlchemyError:
        return False
    return True


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="Offshore Monitor API", version=VERSION)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health", response_model=Health, tags=["health"])
    def health() -> Health:
        db = database_ok()
        return Health(
            status="ok" if db else "degraded",
            data_mode=settings.data_mode.value,
            basin_id=settings.basin_id,
            database="ok" if db else "unreachable",
            version=VERSION,
        )

    for module in ROUTERS:
        app.include_router(module.router)
    return app


app = create_app()
