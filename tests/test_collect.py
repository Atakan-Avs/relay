from fastapi.testclient import TestClient

from app.main import app


def test_collect_rejects_non_finite_payload_over_http() -> None:
    body = """
    {
        "event_id": "00000000-0000-4000-8000-000000000001",
        "event_type": "purchase",
        "occurred_at": "2026-11-21T12:00:00Z",
        "payload": {"amount_minor": NaN}
    }
    """

    with TestClient(app) as client:
        response = client.post(
            "/v1/collect",
            content=body,
            headers={"Content-Type": "application/json"},
        )

    assert response.status_code == 422
    error = response.json()["detail"][0]
    assert error["loc"] == ["body", "payload"]
    assert error["type"] == "value_error"
