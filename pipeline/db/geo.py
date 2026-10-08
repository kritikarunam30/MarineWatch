"""Convert between PostGIS geometry columns and GeoJSON."""

from typing import Any

from geoalchemy2 import WKBElement
from geoalchemy2.shape import from_shape, to_shape
from shapely.geometry import mapping, shape

from pipeline.db.models import SRID


def wkb_to_geojson(element: WKBElement) -> dict[str, Any]:
    return dict(mapping(to_shape(element)))


def geojson_to_wkb(geometry: dict[str, Any]) -> WKBElement:
    return from_shape(shape(geometry), srid=SRID)
