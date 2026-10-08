"""Settings loaded from the environment and `.env`."""

from enum import StrEnum
from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class DataMode(StrEnum):
    FIXTURE = "fixture"
    LIVE = "live"
    REPLAY = "replay"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    data_mode: DataMode = DataMode.FIXTURE
    basin_id: str = "mumbai_high"
    replay_incident: str = ""
    data_dir: Path = Path("data")
    database_url: str = "postgresql+psycopg://monitor:monitor@localhost:5432/monitor"
    cors_origins: str = "http://localhost:5173"

    ee_project: str = ""
    gfw_api_token: str = ""
    copernicusmarine_service_username: str = ""
    copernicusmarine_service_password: str = ""
    eog_username: str = ""
    eog_password: str = ""

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
