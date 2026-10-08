"""Global Fishing Watch offshore infrastructure (oil and gas class only)."""

from pipeline.config import DataMode
from pipeline.sources.base import StubSource, register


@register("gfw", DataMode.FIXTURE)
class GfwFixture(StubSource):
    name = "gfw"
    phase = 2


@register("gfw", DataMode.LIVE)
class GfwLive(StubSource):
    name = "gfw"
    phase = 2
