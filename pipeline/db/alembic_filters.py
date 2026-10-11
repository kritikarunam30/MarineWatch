"""Autogenerate filter shared by Alembic's env.py and the schema-drift test."""

from typing import Any

from geoalchemy2 import alembic_helpers

# PostGIS ships its own tables; never let autogenerate touch them.
POSTGIS_TABLES = {"spatial_ref_sys", "layer", "topology"}
EXTENSION_SCHEMAS = {"tiger", "tiger_data", "topology"}


def _schema_for_object(obj: Any, type_: str) -> str | None:
    if type_ == "table":
        return getattr(obj, "schema", None)
    table = getattr(obj, "table", None)
    if table is not None:
        return getattr(table, "schema", None)
    return getattr(obj, "schema", None)


def include_object(
    obj: Any, name: str | None, type_: str, reflected: bool, compare_to: Any
) -> bool:
    if type_ == "table" and name in POSTGIS_TABLES:
        return False
    if reflected and _schema_for_object(obj, type_) in EXTENSION_SCHEMAS:
        return False
    return bool(alembic_helpers.include_object(obj, name, type_, reflected, compare_to))  # type: ignore[no-untyped-call]
