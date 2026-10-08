import os

import pytest

# Tests never touch live services.
os.environ.setdefault("DATA_MODE", "fixture")


def _database_reachable() -> bool:
    from api.main import database_ok

    return database_ok()


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    if not any(item.get_closest_marker("db") for item in items):
        return
    if _database_reachable():
        return
    if os.environ.get("REQUIRE_DB"):
        raise pytest.UsageError("REQUIRE_DB is set but PostGIS is not reachable at DATABASE_URL")
    skip = pytest.mark.skip(reason="PostGIS not reachable at DATABASE_URL")
    for item in items:
        if item.get_closest_marker("db"):
            item.add_marker(skip)
