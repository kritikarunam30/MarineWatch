"""Autogenerate filter shared by Alembic's env.py and the schema-drift test."""

from typing import Any

from geoalchemy2 import alembic_helpers

# PostGIS ships its own tables; never let autogenerate touch them.
POSTGIS_TABLES = {"spatial_ref_sys", "layer", "topology"}
EXTENSION_SCHEMAS = {"tiger", "tiger_data", "topology"}
POSTGIS_TIGER_TABLES = {
    "addr",
    "addrfeat",
    "bg",
    "county",
    "county_lookup",
    "countysub_lookup",
    "cousub",
    "direction_lookup",
    "edges",
    "faces",
    "featnames",
    "geocode_settings",
    "geocode_settings_default",
    "loader_lookuptables",
    "loader_platform",
    "loader_variables",
    "pagc_gaz",
    "pagc_lex",
    "pagc_rules",
    "place",
    "place_lookup",
    "secondary_unit_lookup",
    "state",
    "state_lookup",
    "street_type_lookup",
    "tabblock",
    "tabblock20",
    "tract",
    "zcta5",
    "zip_lookup",
    "zip_lookup_all",
    "zip_lookup_base",
    "zip_state",
    "zip_state_loc",
}


def _schema_for_object(obj: Any, type_: str) -> str | None:
    if type_ == "table":
        return getattr(obj, "schema", None)
    table = getattr(obj, "table", None)
    if table is not None:
        return getattr(table, "schema", None)
    return getattr(obj, "schema", None)


def _table_name_for_object(obj: Any, type_: str) -> str | None:
    if type_ == "table":
        return getattr(obj, "name", None)
    table = getattr(obj, "table", None)
    if table is not None:
        return getattr(table, "name", None)
    return None


def include_object(
    obj: Any, name: str | None, type_: str, reflected: bool, compare_to: Any
) -> bool:
    if type_ == "table" and name in POSTGIS_TABLES:
        return False
    if reflected and _schema_for_object(obj, type_) in EXTENSION_SCHEMAS:
        return False
    if reflected and _table_name_for_object(obj, type_) in POSTGIS_TIGER_TABLES:
        return False
    return bool(alembic_helpers.include_object(obj, name, type_, reflected, compare_to))  # type: ignore[no-untyped-call]
