"""Initial schema: all shared-contract tables with GiST indexes on geometry.

Revision ID: 0001
Revises:
Create Date: 2026-10-08
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from geoalchemy2 import Geometry
from sqlalchemy.dialects import postgresql

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

TZ = sa.DateTime(timezone=True)


def g(kind: str) -> Geometry:
    # Indexes are created explicitly below so the names are stable.
    return Geometry(geometry_type=kind, srid=4326, spatial_index=False)


GEOM_TABLES = [
    "basins",
    "platforms",
    "scenes",
    "slick_detections",
    "object_detections",
    "flares",
    "events",
    "watchlists",
]


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis")

    op.create_table(
        "basins",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("geom", g("POLYGON"), nullable=False),
    )
    op.create_table(
        "platforms",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String(200)),
        sa.Column("operator", sa.String(200)),
        sa.Column("type", sa.String(64)),
        sa.Column("geom", g("POINT"), nullable=False),
        sa.Column("sources", postgresql.JSONB, nullable=False),
        sa.Column("first_seen", TZ),
        sa.Column("last_seen", TZ),
        sa.Column("confirmed_by_sar", sa.Boolean, nullable=False),
    )
    op.create_table(
        "scenes",
        sa.Column("id", sa.String(128), primary_key=True),
        sa.Column("sensor", sa.String(32), nullable=False),
        sa.Column("acquired_at", TZ, nullable=False),
        sa.Column("geom", g("POLYGON"), nullable=False),
        sa.Column("orbit", sa.String(32)),
        sa.Column("cached_path", sa.Text),
    )
    op.create_index("ix_scenes_acquired_at", "scenes", ["acquired_at"])

    op.create_table(
        "slick_detections",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column(
            "scene_id",
            sa.String(128),
            sa.ForeignKey("scenes.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("geom", g("MULTIPOLYGON"), nullable=False),
        sa.Column("area_km2", sa.Float, nullable=False),
        sa.Column("mean_wind_ms", sa.Float),
        sa.Column("lookalike_flags", postgresql.JSONB, nullable=False),
        sa.Column("confidence", sa.Float),
    )
    op.create_index("ix_slick_detections_scene_id", "slick_detections", ["scene_id"])

    op.create_table(
        "object_detections",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column(
            "scene_id",
            sa.String(128),
            sa.ForeignKey("scenes.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("geom", g("POINT"), nullable=False),
        sa.Column("cls", sa.String(16), nullable=False),
        sa.Column("score", sa.Float, nullable=False),
        sa.Column("length_px", sa.Float),
        sa.CheckConstraint("cls IN ('platform', 'vessel', 'noise')", name="ck_object_cls"),
    )
    op.create_index("ix_object_detections_scene_id", "object_detections", ["scene_id"])

    op.create_table(
        "flares",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("observed_at", TZ, nullable=False),
        sa.Column("geom", g("POINT"), nullable=False),
        sa.Column("temp_k", sa.Float, nullable=False),
        sa.Column("rh_mw", sa.Float, nullable=False),
        sa.Column("platform_id", sa.Integer, sa.ForeignKey("platforms.id", ondelete="SET NULL")),
        sa.Column("persistent", sa.Boolean, nullable=False),
    )
    op.create_index("ix_flares_observed_at", "flares", ["observed_at"])
    op.create_index("ix_flares_platform_id", "flares", ["platform_id"])

    op.create_table(
        "no2_lane_stats",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("period_start", sa.Date, nullable=False),
        sa.Column("period_end", sa.Date, nullable=False),
        sa.Column("lane_id", sa.String(64), nullable=False),
        sa.Column("lane_mean", sa.Float, nullable=False),
        sa.Column("background_mean", sa.Float, nullable=False),
        sa.Column("enhancement_pct", sa.Float, nullable=False),
    )
    op.create_index("ix_no2_lane_stats_lane_id", "no2_lane_stats", ["lane_id"])

    op.create_table(
        "events",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("kind", sa.String(32), nullable=False),
        sa.Column("geom", g("GEOMETRY"), nullable=False),
        sa.Column("start_at", TZ, nullable=False),
        sa.Column("confidence", sa.Float),
        sa.Column("status", sa.String(32), nullable=False),
        sa.CheckConstraint(
            "kind IN ('slick', 'flare_spike', 'new_slick_near_platform')", name="ck_event_kind"
        ),
    )
    op.create_index("ix_events_start_at", "events", ["start_at"])

    op.create_table(
        "event_members",
        sa.Column(
            "event_id",
            sa.Integer,
            sa.ForeignKey("events.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("member_table", sa.String(64), primary_key=True),
        sa.Column("member_id", sa.String(128), primary_key=True),
    )

    op.create_table(
        "drift_runs",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column(
            "slick_id",
            sa.Integer,
            sa.ForeignKey("slick_detections.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("direction", sa.String(16), nullable=False),
        sa.Column("params", postgresql.JSONB, nullable=False),
        sa.Column("tracks_geojson", sa.Text),
        sa.Column("beached_geojson", sa.Text),
        sa.CheckConstraint("direction IN ('forward', 'backward')", name="ck_drift_direction"),
    )
    op.create_index("ix_drift_runs_slick_id", "drift_runs", ["slick_id"])

    op.create_table(
        "suspects",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column(
            "slick_id",
            sa.Integer,
            sa.ForeignKey("slick_detections.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("platform_id", sa.Integer, sa.ForeignKey("platforms.id", ondelete="CASCADE")),
        sa.Column(
            "object_detection_id",
            sa.Integer,
            sa.ForeignKey("object_detections.id", ondelete="CASCADE"),
        ),
        sa.Column("score", sa.Float, nullable=False),
        sa.Column("overlap_score", sa.Float, nullable=False),
        sa.Column("distance_km", sa.Float, nullable=False),
        sa.Column("rank", sa.Integer, nullable=False),
        sa.CheckConstraint(
            "(platform_id IS NULL) <> (object_detection_id IS NULL)",
            name="ck_suspect_one_target",
        ),
    )
    op.create_index("ix_suspects_slick_id", "suspects", ["slick_id"])

    op.create_table(
        "impacts",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column(
            "slick_id",
            sa.Integer,
            sa.ForeignKey("slick_detections.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("hours_to_shore", sa.Float),
        sa.Column("coastline_km", sa.Float, nullable=False),
        sa.Column("mangrove_ha", sa.Float, nullable=False),
        sa.Column("protected_areas", postgresql.JSONB, nullable=False),
        sa.Column("fishing_zones", postgresql.JSONB, nullable=False),
    )
    op.create_index("ix_impacts_slick_id", "impacts", ["slick_id"])

    op.create_table(
        "platform_baselines",
        sa.Column(
            "platform_id",
            sa.Integer,
            sa.ForeignKey("platforms.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("metric", sa.String(32), primary_key=True),
        sa.Column("median", sa.Float, nullable=False),
        sa.Column("mad", sa.Float, nullable=False),
        sa.Column("window_days", sa.Integer, nullable=False),
        sa.Column("updated_at", TZ, server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "alerts",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("kind", sa.String(32), nullable=False),
        sa.Column("platform_id", sa.Integer, sa.ForeignKey("platforms.id", ondelete="SET NULL")),
        sa.Column("event_id", sa.Integer, sa.ForeignKey("events.id", ondelete="SET NULL")),
        sa.Column("zscore", sa.Float),
        sa.Column("created_at", TZ, server_default=sa.func.now(), nullable=False),
        sa.Column("sent_at", TZ),
    )
    op.create_index("ix_alerts_platform_id", "alerts", ["platform_id"])
    op.create_index("ix_alerts_event_id", "alerts", ["event_id"])

    op.create_table(
        "watchlists",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("email", sa.String(320), nullable=False),
        sa.Column("geom", g("POLYGON"), nullable=False),
        sa.Column("kinds", postgresql.ARRAY(sa.Text), nullable=False),
    )

    op.create_table(
        "reports",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column(
            "slick_id",
            sa.Integer,
            sa.ForeignKey("slick_detections.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("pdf_path", sa.Text, nullable=False),
        sa.Column("created_at", TZ, server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_reports_slick_id", "reports", ["slick_id"])

    for table in GEOM_TABLES:
        op.create_index(f"idx_{table}_geom", table, ["geom"], postgresql_using="gist")


def downgrade() -> None:
    for table in [
        "reports",
        "watchlists",
        "alerts",
        "platform_baselines",
        "impacts",
        "suspects",
        "drift_runs",
        "event_members",
        "events",
        "no2_lane_stats",
        "flares",
        "object_detections",
        "slick_detections",
        "scenes",
        "platforms",
        "basins",
    ]:
        op.drop_table(table)
