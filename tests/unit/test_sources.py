from datetime import UTC, datetime

import pytest
from shapely.geometry import box

from pipeline.config import DataMode
from pipeline.sources.base import SOURCE_NAMES, Source, get_source


@pytest.mark.parametrize("name", SOURCE_NAMES)
@pytest.mark.parametrize("mode", [DataMode.FIXTURE, DataMode.LIVE])
def test_every_source_has_fixture_and_live(name: str, mode: DataMode) -> None:
    src = get_source(name, mode)
    assert isinstance(src, Source)
    assert src.name == name
    assert type(src).__name__.endswith(mode.value.capitalize())


def test_replay_falls_back_to_fixture() -> None:
    assert type(get_source("sentinel1", DataMode.REPLAY)).__name__ == "Sentinel1Fixture"


def test_mode_defaults_to_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    from pipeline.config import get_settings

    monkeypatch.setenv("DATA_MODE", "live")
    get_settings.cache_clear()
    try:
        assert type(get_source("era5")).__name__ == "Era5Live"
    finally:
        get_settings.cache_clear()


def test_unknown_source() -> None:
    with pytest.raises(KeyError):
        get_source("modis")


def test_stub_fetch_names_its_phase() -> None:
    src = get_source("gfw", DataMode.FIXTURE)
    t = datetime(2026, 1, 1, tzinfo=UTC)
    with pytest.raises(NotImplementedError, match="phase 2"):
        src.fetch(box(70, 18, 71, 19), t, t)
