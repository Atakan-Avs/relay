import json
from datetime import UTC, datetime
from uuid import UUID

import pytest
from pydantic import ValidationError

from app.schemas import EventCreate


@pytest.fixture
def event_data() -> dict[str, object]:
    return {
        "event_id": "00000000-0000-4000-8000-000000000001",
        "event_type": "purchase",
        "occurred_at": "2026-11-21T12:00:00Z",
        "payload": {
            "amount_minor": 12990,
            "currency": "TRY",
            "items": [{"sku": "ABC", "quantity": 1}],
            "coupon": None,
        },
    }


def test_event_accepts_valid_json(event_data: dict[str, object]) -> None:
    event = EventCreate.model_validate_json(json.dumps(event_data))

    assert event.event_id == UUID("00000000-0000-4000-8000-000000000001")
    assert event.event_type == "purchase"
    assert event.occurred_at == datetime(2026, 11, 21, 12, tzinfo=UTC)
    assert event.payload == event_data["payload"]


@pytest.mark.parametrize(
    ("field", "value", "expected_error"),
    [
        ("event_id", "invalid", "uuid_parsing"),
        ("event_type", "", "string_too_short"),
        ("event_type", "   ", "string_pattern_mismatch"),
        ("event_type", "Purchase", "string_pattern_mismatch"),
        ("event_type", "a" * 101, "string_too_long"),
        ("occurred_at", "2026-11-21T12:00:00", "timezone_aware"),
        ("payload", [], "dict_type"),
        ("payload", None, "dict_type"),
        ("payload", {"value": float("nan")}, "value_error"),
        ("payload", {"nested": [float("inf")]}, "value_error"),
        ("received_at", "2026-11-21T12:00:00Z", "extra_forbidden"),
    ],
)
def test_event_rejects_invalid_input(
    event_data: dict[str, object],
    field: str,
    value: object,
    expected_error: str,
) -> None:
    event_data[field] = value

    with pytest.raises(ValidationError) as exc_info:
        EventCreate.model_validate_json(json.dumps(event_data))

    first_error = exc_info.value.errors()[0]
    assert first_error["loc"][0] == field
    assert first_error["type"] == expected_error


@pytest.mark.parametrize(
    "field",
    ["event_id", "event_type", "occurred_at", "payload"],
)
def test_event_requires_each_field(
    event_data: dict[str, object],
    field: str,
) -> None:
    del event_data[field]

    with pytest.raises(ValidationError) as exc_info:
        EventCreate.model_validate_json(json.dumps(event_data))

    first_error = exc_info.value.errors()[0]
    assert first_error["loc"] == (field,)
    assert first_error["type"] == "missing"
