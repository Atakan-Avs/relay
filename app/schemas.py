from math import isfinite
from uuid import UUID

from pydantic import (
    AwareDatetime,
    BaseModel,
    ConfigDict,
    Field,
    JsonValue,
    field_validator,
)


def _contains_non_finite_number(value: JsonValue) -> bool:
    if isinstance(value, float):
        return not isfinite(value)
    if isinstance(value, list):
        return any(_contains_non_finite_number(item) for item in value)
    if isinstance(value, dict):
        return any(_contains_non_finite_number(item) for item in value.values())
    return False


class EventCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    event_id: UUID
    event_type: str = Field(
        min_length=1,
        max_length=100,
        pattern=r"^[a-z][a-z0-9_]*$",
    )
    occurred_at: AwareDatetime
    payload: dict[str, JsonValue]

    @field_validator("payload")
    @classmethod
    def validate_payload(cls, payload: dict[str, JsonValue]) -> dict[str, JsonValue]:
        if _contains_non_finite_number(payload):
            raise ValueError("Payload numbers must be finite")
        return payload
