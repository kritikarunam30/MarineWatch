"""Autogenerate filter shared by Alembic's env.py and the schema-drift test."""

from typing import Any

from geoalchemy2 import alembic_helpers

# PostGIS ships its own tables; never let autogenerate touch them.
POSTGIS_TABLES = {"spatial_ref_sys", "layer", "topology"}


def include_object(
    obj: Any, name: str | None, type_: str, reflected: bool, compare_to: Any
) -> bool:
    if type_ == "table" and name in POSTGIS_TABLES:
        return False
    return bool(alembic_helpers.include_object(obj, name, type_, reflected, compare_to))  # type: ignore[no-untyped-call]
