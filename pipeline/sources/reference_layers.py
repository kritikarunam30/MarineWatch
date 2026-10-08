"""Coastline, mangroves, WDPA, fishing zones and shipping density, clipped to the basin buffer."""

from pipeline.config import DataMode
from pipeline.sources.base import StubSource, register


@register("reference_layers", DataMode.FIXTURE)
class ReferenceLayersFixture(StubSource):
    name = "reference_layers"
    phase = 2


@register("reference_layers", DataMode.LIVE)
class ReferenceLayersLive(StubSource):
    name = "reference_layers"
    phase = 2
