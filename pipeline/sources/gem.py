"""Global Energy Monitor oil and gas fields from a downloaded file."""

from pipeline.config import DataMode
from pipeline.sources.base import StubSource, register


@register("gem", DataMode.FIXTURE)
class GemFixture(StubSource):
    name = "gem"
    phase = 2


@register("gem", DataMode.LIVE)
class GemLive(StubSource):
    name = "gem"
    phase = 2
