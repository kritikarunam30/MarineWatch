"""Data source interface, registry and `DATA_MODE` switch.

Each module in `pipeline.sources` registers a fixture and a live class:

    @register("sentinel1", DataMode.FIXTURE)
    class Sentinel1Fixture: ...

`get_source("sentinel1")` returns an instance for the current `DATA_MODE`. Replay mode
falls back to the fixture class until a source registers its own replay reader.
"""

import importlib
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, ClassVar, Protocol, TypeVar, runtime_checkable

from shapely.geometry import Polygon

from pipeline.config import DataMode, get_settings

SOURCE_NAMES = (
    "sentinel1",
    "sentinel5p",
    "era5",
    "currents",
    "nightfire",
    "gfw",
    "osm",
    "gem",
    "reference_layers",
)


@dataclass
class SourceResult:
    """Paths to cached files (GeoTIFF / NetCDF / CSV / GeoJSON) plus metadata."""

    paths: list[Path] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@runtime_checkable
class Source(Protocol):
    name: str

    def fetch(self, aoi: Polygon, start: datetime, end: datetime, **kw: Any) -> SourceResult: ...


_REGISTRY: dict[str, dict[DataMode, type[Source]]] = {}

S = TypeVar("S", bound=type[Source])


def register(name: str, mode: DataMode) -> Callable[[S], S]:
    def deco(cls: S) -> S:
        _REGISTRY.setdefault(name, {})[mode] = cls
        return cls

    return deco


def get_source(name: str, mode: DataMode | None = None) -> Source:
    if name not in SOURCE_NAMES:
        raise KeyError(f"unknown source {name!r}; expected one of {SOURCE_NAMES}")
    importlib.import_module(f"pipeline.sources.{name}")
    mode = mode or get_settings().data_mode
    classes = _REGISTRY[name]
    cls = classes.get(mode)
    if cls is None and mode is DataMode.REPLAY:
        cls = classes.get(DataMode.FIXTURE)
    if cls is None:
        raise KeyError(f"source {name!r} has no {mode.value} implementation")
    return cls()


class StubSource:
    """Placeholder until the phase that implements the source."""

    name: str
    phase: ClassVar[int]

    def fetch(self, aoi: Polygon, start: datetime, end: datetime, **kw: Any) -> SourceResult:
        raise NotImplementedError(f"{type(self).__name__} is implemented in phase {self.phase}")
