import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.mark.parametrize("limit", [0, 101])
def test_list_events_rejects_limit_outside_range(limit: int) -> None:
    with TestClient(app) as client:
        response = client.get("/v1/events", params={"limit": limit})

    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"] == ["query", "limit"]
