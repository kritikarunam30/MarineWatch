"""Pydantic models shared by the pipeline and the API.

They mirror the tables in `pipeline/db/models.py`. Geometry is GeoJSON in EPSG:4326.
Change these only together with a migration and a note in CLAUDE.md.
"""

from datetime import date, datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

GeometryType = Literal[
    "Point",
    "MultiPoint",
    "LineString",
    "MultiLineString",
    "Polygon",
    "MultiPolygon",
    "GeometryCollection",
]
ObjectClass = Literal["platform", "vessel", "noise"]
EventKind = Literal["slick", "flare_spike", "new_slick_near_platform"]
DriftDirection = Literal["forward", "backward"]


class Geometry(BaseModel):
    """GeoJSON geometry. Coordinates are not validated beyond being present."""

    model_config = ConfigDict(extra="allow")

    type: GeometryType
    coordinates: Any = None
    geometries: list["Geometry"] | None = None


class Feature(BaseModel):
    type: Literal["Feature"] = "Feature"
    id: str | int | None = None
    geometry: Geometry | None
    properties: dict[str, Any] = Field(default_factory=dict)


class FeatureCollection(BaseModel):
    type: Literal["FeatureCollection"] = "FeatureCollection"
    features: list[Feature] = Field(default_factory=list)


class GeoRecord(BaseModel):
    """Base for records that carry a `geom` field."""

    model_config = ConfigDict(from_attributes=True)

    geom: Geometry

    def to_feature(self, id_field: str = "id") -> Feature:
        props = self.model_dump(mode="json", exclude={"geom"})
        return Feature(id=props.get(id_field), geometry=self.geom, properties=props)


def to_feature_collection(records: list[GeoRecord], id_field: str = "id") -> FeatureCollection:
    return FeatureCollection(features=[r.to_feature(id_field) for r in records])


class Record(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# --- table mirrors -------------------------------------------------------------------------


class Basin(GeoRecord):
    id: str
    name: str


class Platform(GeoRecord):
    id: int
    name: str | None = None
    operator: str | None = None
    type: str | None = None
    sources: dict[str, Any] = Field(default_factory=dict)
    first_seen: datetime | None = None
    last_seen: datetime | None = None
    confirmed_by_sar: bool = False


class Scene(GeoRecord):
    id: str
    sensor: str
    acquired_at: datetime
    orbit: str | None = None
    cached_path: str | None = None


class SlickDetection(GeoRecord):
    id: int
    scene_id: str
    area_km2: float
    mean_wind_ms: float | None = None
    lookalike_flags: dict[str, Any] = Field(default_factory=dict)
    confidence: float | None = Field(default=None, ge=0, le=1)


class ObjectDetection(GeoRecord):
    id: int
    scene_id: str
    cls: ObjectClass
    score: float
    length_px: float | None = None


class Flare(GeoRecord):
    id: int
    observed_at: datetime
    temp_k: float
    rh_mw: float
    platform_id: int | None = None
    persistent: bool = False


class No2LaneStat(Record):
    id: int
    period_start: date
    period_end: date
    lane_id: str
    lane_mean: float
    background_mean: float
    enhancement_pct: float


class Event(GeoRecord):
    id: int
    kind: EventKind
    start_at: datetime
    confidence: float | None = Field(default=None, ge=0, le=1)
    status: str = "open"


class EventMember(Record):
    event_id: int
    member_table: str
    member_id: str


class DriftRun(Record):
    id: int
    slick_id: int
    direction: DriftDirection
    params: dict[str, Any] = Field(default_factory=dict)
    tracks_geojson: str | None = None
    beached_geojson: str | None = None


class Suspect(Record):
    id: int
    slick_id: int
    platform_id: int | None = None
    object_detection_id: int | None = None
    score: float
    overlap_score: float
    distance_km: float
    rank: int


class Impact(Record):
    id: int
    slick_id: int
    hours_to_shore: float | None = None
    coastline_km: float = 0.0
    mangrove_ha: float = 0.0
    protected_areas: dict[str, Any] = Field(default_factory=dict)
    fishing_zones: dict[str, Any] = Field(default_factory=dict)


class PlatformBaseline(Record):
    platform_id: int
    metric: str
    median: float
    mad: float
    window_days: int
    updated_at: datetime


class Alert(Record):
    id: int
    kind: str
    platform_id: int | None = None
    event_id: int | None = None
    zscore: float | None = None
    created_at: datetime
    sent_at: datetime | None = None


class WatchlistIn(BaseModel):
    name: str
    email: str
    geom: Geometry
    kinds: list[str] = Field(default_factory=list)


class Watchlist(GeoRecord):
    id: int
    name: str
    email: str
    kinds: list[str] = Field(default_factory=list)


class Report(Record):
    id: int
    slick_id: int
    pdf_path: str
    created_at: datetime


class Health(BaseModel):
    status: Literal["ok", "degraded"]
    data_mode: str
    basin_id: str
    database: Literal["ok", "unreachable"]
    version: str
