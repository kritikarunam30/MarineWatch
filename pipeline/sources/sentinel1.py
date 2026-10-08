"""Sentinel-1 IW GRD VV chips from Earth Engine (COPERNICUS/S1_GRD)."""

from pipeline.config import DataMode
from pipeline.sources.base import StubSource, register


@register("sentinel1", DataMode.FIXTURE)
class Sentinel1Fixture(StubSource):
    name = "sentinel1"
    phase = 3


@register("sentinel1", DataMode.LIVE)
class Sentinel1Live(StubSource):
    name = "sentinel1"
    phase = 3
