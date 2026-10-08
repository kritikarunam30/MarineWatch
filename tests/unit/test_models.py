from geoalchemy2 import Geometry
from shapely.geometry import Point

from pipeline.db.geo import geojson_to_wkb, wkb_to_geojson
from pipeline.db.models import Base

CONTRACT_TABLES = {
    "basins", "platforms", "scenes", "slick_detections", "object_detections", "flares",
    "no2_lane_stats", "events", "event_members", "drift_runs", "suspects", "impacts",
    "platform_baselines", "alerts", "watchlists", "reports",
}  # fmt: skip


def test_every_contract_table_is_modelled() -> None:
    assert set(Base.metadata.tables) == CONTRACT_TABLES


def test_geometry_columns_are_4326_and_indexed() -> None:
    for table in Base.metadata.tables.values():
        for col in table.columns:
            if isinstance(col.type, Geometry):
                assert col.type.srid == 4326, table.name
                assert col.type.spatial_index, table.name


def test_geojson_roundtrip() -> None:
    gj = {"type": "Point", "coordinates": (71.3, 19.4)}
    el = geojson_to_wkb(gj)
    assert el.srid == 4326
    assert wkb_to_geojson(el) == dict(Point(71.3, 19.4).__geo_interface__)
