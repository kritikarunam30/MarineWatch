"""ERA5 hourly 10 m u/v winds as NetCDF for OpenDrift."""

from pipeline.config import DataMode
from pipeline.sources.base import StubSource, register


@register("era5", DataMode.FIXTURE)
class Era5Fixture(StubSource):
    name = "era5"
    phase = 3


@register("era5", DataMode.LIVE)
class Era5Live(StubSource):
    name = "era5"
    phase = 3
