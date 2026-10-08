import pytest
from fastapi.testclient import TestClient

import api.main
from api.main import create_app

RESOURCES = [
    "basins", "platforms", "scenes", "slicks", "objects", "flares", "no2", "events",
    "drift", "suspects", "impacts", "alerts", "watchlists", "reports", "tiles",
]  # fmt: skip


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setattr(api.main, "database_ok", lambda: False)
    return TestClient(create_app())


def test_health_reports_degraded_without_db(client: TestClient) -> None:
    r = client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "degraded"
    assert body["database"] == "unreachable"
    assert body["data_mode"] == "fixture"


def test_health_ok_with_db(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(api.main, "database_ok", lambda: True)
    assert client.get("/health").json()["status"] == "ok"


@pytest.mark.parametrize("resource", RESOURCES)
def test_stub_routers_answer_501(client: TestClient, resource: str) -> None:
    r = client.get(f"/{resource}")
    assert r.status_code == 501
    assert "phase" in r.json()["detail"]


def test_cors_allows_frontend(client: TestClient) -> None:
    r = client.get("/health", headers={"Origin": "http://localhost:5173"})
    assert r.headers["access-control-allow-origin"] == "http://localhost:5173"
