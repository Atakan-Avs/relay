from json import dumps
from typing import Annotated

from fastapi import APIRouter, Query, Request, Response, status

from app.async_queries import insert_event, list_recent_events
from app.database import get_database_engine
from app.schemas import EventCreate, EventSummary

router = APIRouter(prefix="/v1")


@router.post(
    "/collect", status_code=status.HTTP_204_NO_CONTENT, response_class=Response
)
async def collect(event: EventCreate, request: Request) -> Response:
    engine = get_database_engine(request.app)
    async with engine.begin() as connection:
        await insert_event(
            connection,
            event_id=event.event_id,
            event_type=event.event_type,
            occurred_at=event.occurred_at,
            payload=dumps(event.payload, allow_nan=False),
        )

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/events")
async def list_events(
    request: Request,
    limit: Annotated[int, Query(ge=1, le=100)] = 25,
) -> list[EventSummary]:
    engine = get_database_engine(request.app)
    async with engine.connect() as connection:
        result = await list_recent_events(connection, limit=limit)
        return [
            EventSummary.model_validate(row, from_attributes=True)
            for row in result.all()
        ]
