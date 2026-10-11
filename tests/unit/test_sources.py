import sys
from datetime import datetime
from types import ModuleType
from typing import Any

import pytest
from shapely.geometry import Polygon

from pipeline.config import DataMode, get_settings
from pipeline.sources.base import SourceResult, get_source


@pytest.fixture
def fake_source(monkeypatch: pytest.MonkeyPatch) -> None:
    """Register a throwaway `pipeline.sources.gfw` module with Fixture and Live classes."""

    class Fixture:
        name = "gfw"

        def fetch(self, aoi: Polygon, start: datetime, end: datetime, **kw: Any) -> SourceResult:
            return SourceResult(metadata={"mode": "fixture"})

    class Live(Fixture):
        pass

    module = ModuleType("pipeline.sources.gfw")
    module.Fixture = Fixture  # type: ignore[attr-defined]
    module.Live = Live  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "pipeline.sources.gfw", module)


@pytest.mark.usefixtures("fake_source")
@pytest.mark.parametrize(
    ("mode", "cls"),
    [(DataMode.FIXTURE, "Fixture"), (DataMode.LIVE, "Live"), (DataMode.REPLAY, "Fixture")],
)
def test_mode_picks_class(mode: DataMode, cls: str) -> None:
    assert type(get_source("gfw", mode)).__name__ == cls


@pytest.mark.usefixtures("fake_source")
def test_mode_defaults_to_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DATA_MODE", "live")
    get_settings.cache_clear()
    try:
        assert type(get_source("gfw")).__name__ == "Live"
    finally:
        get_settings.cache_clear()


def test_unbuilt_source_names_its_phase() -> None:
    with pytest.raises(NotImplementedError, match="phase 3"):
        get_source("sentinel1")


def test_unknown_source() -> None:
    with pytest.raises(KeyError):
        get_source("modis")
