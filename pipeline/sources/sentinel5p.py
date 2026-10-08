"""Sentinel-5P tropospheric NO2 means from Earth Engine (COPERNICUS/S5P/OFFL/L3_NO2)."""

from pipeline.config import DataMode
from pipeline.sources.base import StubSource, register


@register("sentinel5p", DataMode.FIXTURE)
class Sentinel5pFixture(StubSource):
    name = "sentinel5p"
    phase = 3


@register("sentinel5p", DataMode.LIVE)
class Sentinel5pLive(StubSource):
    name = "sentinel5p"
    phase = 3
