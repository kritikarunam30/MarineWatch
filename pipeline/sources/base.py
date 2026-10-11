"""Data source interface and `DATA_MODE` switch.

Each source is a module `pipeline/sources/<name>.py` with two classes, `Fixture` and `Live`
(optionally `Replay`), that implement `Source`. `get_source(name)` picks the class for the
current `DATA_MODE`; replay mode uses `Fixture` until a module defines `Replay`.
"""

import importlib
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Protocol

from shapely.geometry import Polygon

from pipeline.config import DataMode, get_settings

# Every source in the plan, with the phase that builds it.
SOURCE_PHASES = {
    "gfw": 2,
    "osm": 2,
    "gem": 2,
    "reference_layers": 2,
    "sentinel1": 3,
    "sentinel5p": 3,
    "era5": 3,
    "currents": 3,
    "nightfire": 3,
}


@dataclass
class SourceResult:
    """Paths to cached files (GeoTIFF / NetCDF / CSV / GeoJSON) plus metadata."""

    paths: list[Path] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


class Source(Protocol):
    name: str

    def fetch(self, aoi: Polygon, start: datetime, end: datetime, **kw: Any) -> SourceResult: ...


def get_source(name: str, mode: DataMode | None = None) -> Source:
    if name not in SOURCE_PHASES:
        raise KeyError(f"unknown source {name!r}; expected one of {list(SOURCE_PHASES)}")
    try:
        module = importlib.import_module(f"pipeline.sources.{name}")
    except ModuleNotFoundError:
        raise NotImplementedError(
            f"source {name!r} is implemented in phase {SOURCE_PHASES[name]}"
        ) from None
    mode = mode or get_settings().data_mode
    if mode is DataMode.REPLAY and not hasattr(module, "Replay"):
        mode = DataMode.FIXTURE
    cls: type[Source] = getattr(module, mode.value.capitalize())
    return cls()
