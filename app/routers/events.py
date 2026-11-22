from json import dumps

from fastapi import APIRouter, Request, Response, status

from app.async_queries import insert_event
from app.database import get_database_engine
from app.schemas import EventCreate

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
