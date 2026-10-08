from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from pipeline import schemas


def platform(pid: int) -> schemas.Platform:
    return schemas.Platform(
        id=pid,
        name=f"P{pid}",
        geom=schemas.Geometry(type="Point", coordinates=[71.3, 19.4]),
        sources={"osm": "node/1"},
        first_seen=datetime(2026, 1, 1, tzinfo=UTC),
    )


def test_to_feature_moves_geom_out_of_properties() -> None:
    f = platform(7).to_feature()
    assert f.id == 7
    assert f.geometry is not None and f.geometry.type == "Point"
    assert "geom" not in f.properties
    assert f.properties["first_seen"] == "2026-01-01T00:00:00Z"


def test_feature_collection_is_valid_geojson_shape() -> None:
    fc = schemas.to_feature_collection([platform(1), platform(2)])
    data = fc.model_dump(mode="json")
    assert data["type"] == "FeatureCollection"
    assert [f["id"] for f in data["features"]] == [1, 2]
    assert data["features"][0]["geometry"]["coordinates"] == [71.3, 19.4]


def test_rejects_bad_geometry_type_and_class() -> None:
    with pytest.raises(ValidationError):
        schemas.Geometry(type="Circle", coordinates=[0, 0])  # type: ignore[arg-type]
    with pytest.raises(ValidationError):
        schemas.ObjectDetection(
            id=1,
            scene_id="S1",
            cls="buoy",  # type: ignore[arg-type]
            score=0.5,
            geom=schemas.Geometry(type="Point", coordinates=[0, 0]),
        )


def test_confidence_bounded() -> None:
    with pytest.raises(ValidationError):
        schemas.SlickDetection(
            id=1,
            scene_id="S1",
            area_km2=1.0,
            confidence=1.5,
            geom=schemas.Geometry(type="MultiPolygon", coordinates=[]),
        )
