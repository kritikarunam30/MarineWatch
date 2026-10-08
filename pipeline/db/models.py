"""SQLAlchemy models for every table in the shared contract.

All geometry is EPSG:4326. GeoAlchemy2 adds a GiST index (`idx_<table>_geom`) to every
geometry column; the first migration creates the same indexes explicitly.
"""

from datetime import date, datetime
from typing import Any

from geoalchemy2 import Geometry, WKBElement
from sqlalchemy import (
    ARRAY,
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

SRID = 4326


def geom(kind: str) -> Geometry:
    return Geometry(geometry_type=kind, srid=SRID)


class Base(DeclarativeBase):
    type_annotation_map = {dict[str, Any]: JSONB, list[str]: ARRAY(Text)}


class Basin(Base):
    __tablename__ = "basins"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    geom: Mapped[WKBElement] = mapped_column(geom("POLYGON"))


class Platform(Base):
    __tablename__ = "platforms"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str | None] = mapped_column(String(200))
    operator: Mapped[str | None] = mapped_column(String(200))
    type: Mapped[str | None] = mapped_column(String(64))
    geom: Mapped[WKBElement] = mapped_column(geom("POINT"))
    sources: Mapped[dict[str, Any]] = mapped_column(default=dict)
    first_seen: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_seen: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    confirmed_by_sar: Mapped[bool] = mapped_column(Boolean, default=False)


class Scene(Base):
    __tablename__ = "scenes"

    id: Mapped[str] = mapped_column(String(128), primary_key=True)  # S1 product ID
    sensor: Mapped[str] = mapped_column(String(32))
    acquired_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    geom: Mapped[WKBElement] = mapped_column(geom("POLYGON"))
    orbit: Mapped[str | None] = mapped_column(String(32))
    cached_path: Mapped[str | None] = mapped_column(Text)


class SlickDetection(Base):
    __tablename__ = "slick_detections"

    id: Mapped[int] = mapped_column(primary_key=True)
    scene_id: Mapped[str] = mapped_column(ForeignKey("scenes.id", ondelete="CASCADE"), index=True)
    geom: Mapped[WKBElement] = mapped_column(geom("MULTIPOLYGON"))
    area_km2: Mapped[float] = mapped_column(Float)
    mean_wind_ms: Mapped[float | None] = mapped_column(Float)
    lookalike_flags: Mapped[dict[str, Any]] = mapped_column(default=dict)
    confidence: Mapped[float | None] = mapped_column(Float)


class ObjectDetection(Base):
    __tablename__ = "object_detections"
    __table_args__ = (
        CheckConstraint("cls IN ('platform', 'vessel', 'noise')", name="ck_object_cls"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    scene_id: Mapped[str] = mapped_column(ForeignKey("scenes.id", ondelete="CASCADE"), index=True)
    geom: Mapped[WKBElement] = mapped_column(geom("POINT"))
    cls: Mapped[str] = mapped_column(String(16))
    score: Mapped[float] = mapped_column(Float)
    length_px: Mapped[float | None] = mapped_column(Float)


class Flare(Base):
    __tablename__ = "flares"

    id: Mapped[int] = mapped_column(primary_key=True)
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    geom: Mapped[WKBElement] = mapped_column(geom("POINT"))
    temp_k: Mapped[float] = mapped_column(Float)
    rh_mw: Mapped[float] = mapped_column(Float)
    platform_id: Mapped[int | None] = mapped_column(
        ForeignKey("platforms.id", ondelete="SET NULL"), index=True
    )
    persistent: Mapped[bool] = mapped_column(Boolean, default=False)


class No2LaneStat(Base):
    __tablename__ = "no2_lane_stats"

    id: Mapped[int] = mapped_column(primary_key=True)
    period_start: Mapped[date] = mapped_column(Date)
    period_end: Mapped[date] = mapped_column(Date)
    lane_id: Mapped[str] = mapped_column(String(64), index=True)
    lane_mean: Mapped[float] = mapped_column(Float)
    background_mean: Mapped[float] = mapped_column(Float)
    enhancement_pct: Mapped[float] = mapped_column(Float)


class Event(Base):
    __tablename__ = "events"
    __table_args__ = (
        CheckConstraint(
            "kind IN ('slick', 'flare_spike', 'new_slick_near_platform')", name="ck_event_kind"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    kind: Mapped[str] = mapped_column(String(32))
    geom: Mapped[WKBElement] = mapped_column(geom("GEOMETRY"))
    start_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    confidence: Mapped[float | None] = mapped_column(Float)
    status: Mapped[str] = mapped_column(String(32), default="open")


class EventMember(Base):
    __tablename__ = "event_members"

    event_id: Mapped[int] = mapped_column(
        ForeignKey("events.id", ondelete="CASCADE"), primary_key=True
    )
    member_table: Mapped[str] = mapped_column(String(64), primary_key=True)
    member_id: Mapped[str] = mapped_column(String(128), primary_key=True)


class DriftRun(Base):
    __tablename__ = "drift_runs"
    __table_args__ = (
        CheckConstraint("direction IN ('forward', 'backward')", name="ck_drift_direction"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    slick_id: Mapped[int] = mapped_column(
        ForeignKey("slick_detections.id", ondelete="CASCADE"), index=True
    )
    direction: Mapped[str] = mapped_column(String(16))
    params: Mapped[dict[str, Any]] = mapped_column(default=dict)
    tracks_geojson: Mapped[str | None] = mapped_column(Text)
    beached_geojson: Mapped[str | None] = mapped_column(Text)


class Suspect(Base):
    __tablename__ = "suspects"
    __table_args__ = (
        CheckConstraint(
            "(platform_id IS NULL) <> (object_detection_id IS NULL)", name="ck_suspect_one_target"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    slick_id: Mapped[int] = mapped_column(
        ForeignKey("slick_detections.id", ondelete="CASCADE"), index=True
    )
    platform_id: Mapped[int | None] = mapped_column(ForeignKey("platforms.id", ondelete="CASCADE"))
    object_detection_id: Mapped[int | None] = mapped_column(
        ForeignKey("object_detections.id", ondelete="CASCADE")
    )
    score: Mapped[float] = mapped_column(Float)
    overlap_score: Mapped[float] = mapped_column(Float)
    distance_km: Mapped[float] = mapped_column(Float)
    rank: Mapped[int] = mapped_column(Integer)


class Impact(Base):
    __tablename__ = "impacts"

    id: Mapped[int] = mapped_column(primary_key=True)
    slick_id: Mapped[int] = mapped_column(
        ForeignKey("slick_detections.id", ondelete="CASCADE"), index=True
    )
    hours_to_shore: Mapped[float | None] = mapped_column(Float)
    coastline_km: Mapped[float] = mapped_column(Float, default=0.0)
    mangrove_ha: Mapped[float] = mapped_column(Float, default=0.0)
    protected_areas: Mapped[dict[str, Any]] = mapped_column(default=dict)
    fishing_zones: Mapped[dict[str, Any]] = mapped_column(default=dict)


class PlatformBaseline(Base):
    __tablename__ = "platform_baselines"

    platform_id: Mapped[int] = mapped_column(
        ForeignKey("platforms.id", ondelete="CASCADE"), primary_key=True
    )
    metric: Mapped[str] = mapped_column(String(32), primary_key=True)
    median: Mapped[float] = mapped_column(Float)
    mad: Mapped[float] = mapped_column(Float)
    window_days: Mapped[int] = mapped_column(Integer)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Alert(Base):
    __tablename__ = "alerts"

    id: Mapped[int] = mapped_column(primary_key=True)
    kind: Mapped[str] = mapped_column(String(32))
    platform_id: Mapped[int | None] = mapped_column(
        ForeignKey("platforms.id", ondelete="SET NULL"), index=True
    )
    event_id: Mapped[int | None] = mapped_column(
        ForeignKey("events.id", ondelete="SET NULL"), index=True
    )
    zscore: Mapped[float | None] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Watchlist(Base):
    __tablename__ = "watchlists"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    email: Mapped[str] = mapped_column(String(320))
    geom: Mapped[WKBElement] = mapped_column(geom("POLYGON"))
    kinds: Mapped[list[str]] = mapped_column(default=list)


class Report(Base):
    __tablename__ = "reports"

    id: Mapped[int] = mapped_column(primary_key=True)
    slick_id: Mapped[int] = mapped_column(
        ForeignKey("slick_detections.id", ondelete="CASCADE"), index=True
    )
    pdf_path: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
