from types import SimpleNamespace

from pipeline.db.alembic_filters import include_object


def test_filters_postgis_tables_by_name() -> None:
    table = SimpleNamespace(schema="public")
    assert not include_object(table, "spatial_ref_sys", "table", reflected=True, compare_to=None)


def test_filters_extension_schema_tables() -> None:
    table = SimpleNamespace(schema="tiger")
    assert not include_object(table, "addr", "table", reflected=True, compare_to=None)


def test_filters_extension_schema_indexes() -> None:
    index = SimpleNamespace(table=SimpleNamespace(schema="tiger_data"))
    assert not include_object(index, "idx_addr", "index", reflected=True, compare_to=None)


def test_keeps_public_schema_table() -> None:
    table = SimpleNamespace(schema="public")
    assert include_object(table, "basins", "table", reflected=True, compare_to=None)
