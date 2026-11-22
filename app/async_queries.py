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
