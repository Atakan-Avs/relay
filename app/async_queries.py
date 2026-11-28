from __future__ import annotations

from collections.abc import Generator
from dataclasses import dataclass
from typing import TYPE_CHECKING

from sqlalchemy import text

if TYPE_CHECKING:
    from datetime import datetime
    from typing import Any

    from sqlalchemy.ext.asyncio import AsyncConnection

type Json = str | bool | int | float | dict[str, Json] | list[Json] | None


@dataclass
class DbOutput[T]:
    inner: Generator[T]

    def first(self) -> T | None:
        """Get the first result if available."""
        try:
            return self.inner.__next__()
        except BaseException:
            return None

    def all(self) -> Generator[T]:
        return self.inner


@dataclass
class ClaimWebhookDeliveryOutput:
    status: str | None
    event_id: Any | None
    attempt_count: int | None
    event_type: str | None
    occurred_at: datetime | None
    payload: Json | None


async def claim_webhook_delivery(
    conn: AsyncConnection, *, max_attempts: int | None
) -> DbOutput[ClaimWebhookDeliveryOutput]:
    result = await conn.execute(
        text("""WITH candidate AS (
    SELECT event_id, destination, attempt_count >= :max_attempts AS exhausted
    FROM event_deliveries
    WHERE destination = 'webhook'
        AND status = 'pending'
        AND next_attempt_at <= CURRENT_TIMESTAMP
    ORDER BY next_attempt_at, event_id
    LIMIT 1
    FOR UPDATE SKIP LOCKED
)
UPDATE event_deliveries AS delivery
SET
    status = CASE WHEN candidate.exhausted THEN 'failed' ELSE 'pending' END,
    attempt_count = delivery.attempt_count + CASE WHEN candidate.exhausted THEN 0 ELSE 1 END,
    next_attempt_at = CASE
        WHEN candidate.exhausted THEN NULL
        ELSE CURRENT_TIMESTAMP + INTERVAL '30 seconds'
    END
FROM candidate
JOIN events AS event USING (event_id)
WHERE delivery.event_id = candidate.event_id
    AND delivery.destination = candidate.destination
RETURNING
    delivery.status,
    delivery.event_id,
    delivery.attempt_count,
    event.event_type,
    event.occurred_at,
    event.payload;
"""),
        {"max_attempts": max_attempts},
    )
    return DbOutput(ClaimWebhookDeliveryOutput(*row) for row in result)  # type: ignore


async def insert_event(
    conn: AsyncConnection,
    *,
    event_id: Any | None,
    event_type: str | None,
    occurred_at: datetime | None,
    payload: str | None,
) -> None:
    await conn.execute(
        text("""WITH new_event AS (
    INSERT INTO events (event_id, event_type, occurred_at, payload)
    VALUES (:event_id, :event_type, :occurred_at, :payload)
    ON CONFLICT (event_id) DO NOTHING
    RETURNING event_id
)
INSERT INTO event_deliveries (event_id, destination)
SELECT event_id, 'webhook'
FROM new_event;
"""),
        {
            "event_id": event_id,
            "event_type": event_type,
            "occurred_at": occurred_at,
            "payload": payload,
        },
    )


@dataclass
class ListRecentEventsOutput:
    event_id: Any | None
    event_type: str | None
    occurred_at: datetime | None
    received_at: datetime | None
    delivery_status: str | None
    attempt_count: int | None
    next_attempt_at: datetime | None


async def list_recent_events(
    conn: AsyncConnection, *, limit: int | None
) -> DbOutput[ListRecentEventsOutput]:
    result = await conn.execute(
        text("""SELECT
    event.event_id,
    event.event_type,
    event.occurred_at,
    event.received_at,
    delivery.status AS delivery_status,
    delivery.attempt_count,
    delivery.next_attempt_at
FROM events AS event
LEFT JOIN event_deliveries AS delivery
    ON delivery.event_id = event.event_id
    AND delivery.destination = 'webhook'
ORDER BY event.received_at DESC, event.event_id DESC
LIMIT :limit;
"""),
        {"limit": limit},
    )
    return DbOutput(ListRecentEventsOutput(*row) for row in result)  # type: ignore


@dataclass
class MarkWebhookDeliveredOutput:
    event_id: Any | None


async def mark_webhook_delivered(
    conn: AsyncConnection, *, event_id: Any | None, attempt_count: int | None
) -> DbOutput[MarkWebhookDeliveredOutput]:
    result = await conn.execute(
        text("""UPDATE event_deliveries
SET status = 'delivered', next_attempt_at = NULL
WHERE event_id = :event_id
    AND destination = 'webhook'
    AND status = 'pending'
    AND attempt_count = :attempt_count
RETURNING event_id;
"""),
        {"event_id": event_id, "attempt_count": attempt_count},
    )
    return DbOutput(MarkWebhookDeliveredOutput(*row) for row in result)  # type: ignore


@dataclass
class RecordWebhookFailureOutput:
    status: str | None


async def record_webhook_failure(
    conn: AsyncConnection,
    *,
    retry_seconds: int | None,
    event_id: Any | None,
    attempt_count: int | None,
) -> DbOutput[RecordWebhookFailureOutput]:
    result = await conn.execute(
        text("""UPDATE event_deliveries
SET
    status = CASE WHEN CAST(:retry_seconds AS integer) IS NULL THEN 'failed' ELSE 'pending' END,
    next_attempt_at = CURRENT_TIMESTAMP + CAST(:retry_seconds AS integer) * INTERVAL '1 second'
WHERE event_id = :event_id
    AND destination = 'webhook'
    AND status = 'pending'
    AND attempt_count = :attempt_count
RETURNING status;
"""),
        {
            "retry_seconds": retry_seconds,
            "event_id": event_id,
            "attempt_count": attempt_count,
        },
    )
    return DbOutput(RecordWebhookFailureOutput(*row) for row in result)  # type: ignore
