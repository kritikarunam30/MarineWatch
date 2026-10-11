from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from pipeline.config import get_settings
from pipeline.db.session import get_engine
from pipeline.schemas import Health

VERSION = "0.1.0"

# Resources not built yet, with the phase that adds them. Each phase replaces its entry
# with a real router in `api/routers/<resource>.py`.
PLANNED_ROUTES = {
    "basins": 2, "platforms": 2, "scenes": 3, "tiles": 3, "slicks": 4, "objects": 5,
    "flares": 6, "no2": 6, "events": 6, "drift": 7, "suspects": 7, "impacts": 7,
    "alerts": 8, "watchlists": 8, "reports": 9,
}  # fmt: skip


def database_ok() -> bool:
    try:
        with get_engine().connect() as conn:
            conn.execute(text("SELECT 1"))
    except SQLAlchemyError:
        return False
    return True


def add_planned_route(app: FastAPI, resource: str, phase: int) -> None:
    def not_implemented() -> None:
        raise HTTPException(
            status.HTTP_501_NOT_IMPLEMENTED, f"/{resource} is implemented in phase {phase}"
        )

    app.get(f"/{resource}", tags=[resource], summary=f"Phase {phase}")(not_implemented)


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

    for resource, phase in PLANNED_ROUTES.items():
        add_planned_route(app, resource, phase)
    return app


app = create_app()
