"""Surface currents from Copernicus Marine, with HYCOM in Earth Engine as a fallback."""

from pipeline.config import DataMode
from pipeline.sources.base import StubSource, register


@register("currents", DataMode.FIXTURE)
class CurrentsFixture(StubSource):
    name = "currents"
    phase = 3


@register("currents", DataMode.LIVE)
class CurrentsLive(StubSource):
    name = "currents"
    phase = 3
