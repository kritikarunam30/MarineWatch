"""Runs against a real PostGIS (CI service container or `make up`)."""

from collections.abc import Iterator

import pytest
from alembic import command
from alembic.autogenerate import compare_metadata
from alembic.config import Config
from alembic.migration import MigrationContext
from sqlalchemy import inspect, text

from pipeline.db.alembic_filters import include_object
from pipeline.db.models import Base
from pipeline.db.session import get_engine

pytestmark = pytest.mark.db


@pytest.fixture(scope="module")
def migrated() -> Iterator[Config]:
    cfg = Config("alembic.ini")
    command.downgrade(cfg, "base")
    command.upgrade(cfg, "head")
    yield cfg


def test_all_tables_created(migrated: Config) -> None:
    tables = set(inspect(get_engine()).get_table_names())
    assert set(Base.metadata.tables) <= tables


def test_gist_index_on_every_geom(migrated: Config) -> None:
    with get_engine().connect() as conn:
        rows = conn.execute(
            text("SELECT tablename FROM pg_indexes WHERE indexdef ILIKE '%USING gist (geom)%'")
        ).scalars()
        indexed = set(rows)
    geom_tables = {t.name for t in Base.metadata.tables.values() if "geom" in t.columns}
    assert geom_tables <= indexed


def test_models_match_migration(migrated: Config) -> None:
    with get_engine().connect() as conn:
        ctx = MigrationContext.configure(conn, opts={"include_object": include_object})
        diff = compare_metadata(ctx, Base.metadata)
    assert diff == []


def test_seed_basins_is_idempotent(migrated: Config) -> None:
    from scripts.seed import seed_basins

    seed_basins()
    seed_basins()
    with get_engine().connect() as conn:
        n = conn.execute(text("SELECT count(*) FROM basins")).scalar_one()
        valid = conn.execute(text("SELECT bool_and(ST_IsValid(geom)) FROM basins")).scalar_one()
    assert n == 2
    assert valid
