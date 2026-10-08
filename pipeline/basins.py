"""Candidate basin AOIs (EPSG:4326). Rough offshore boxes; refine after Phase 0."""

from shapely.geometry import Polygon, box

BASINS: dict[str, tuple[str, Polygon]] = {
    "mumbai_high": ("Mumbai High", box(70.5, 18.5, 72.8, 20.5)),
    "kg_basin": ("Krishna-Godavari", box(81.3, 15.3, 83.3, 17.0)),
}


def basin_aoi(basin_id: str) -> Polygon:
    try:
        return BASINS[basin_id][1]
    except KeyError:
        raise KeyError(f"unknown basin {basin_id!r}; expected one of {list(BASINS)}") from None
