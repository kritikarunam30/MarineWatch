"""OpenStreetMap offshore platforms and wells via Overpass."""

from pipeline.config import DataMode
from pipeline.sources.base import StubSource, register


@register("osm", DataMode.FIXTURE)
class OsmFixture(StubSource):
    name = "osm"
    phase = 2


@register("osm", DataMode.LIVE)
class OsmLive(StubSource):
    name = "osm"
    phase = 2
