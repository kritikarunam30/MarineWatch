"""VIIRS Nightfire nightly CSVs from the Earth Observation Group, filtered to the basin."""

from pipeline.config import DataMode
from pipeline.sources.base import StubSource, register


@register("nightfire", DataMode.FIXTURE)
class NightfireFixture(StubSource):
    name = "nightfire"
    phase = 3


@register("nightfire", DataMode.LIVE)
class NightfireLive(StubSource):
    name = "nightfire"
    phase = 3
