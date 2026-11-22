import asyncio
from argparse import ArgumentParser
from sys import stderr

from httpx2 import URL, AsyncClient, HTTPError, InvalidURL
from sqlalchemy.ext.asyncio import AsyncEngine

from app.async_queries import (
    claim_webhook_delivery,
    mark_webhook_delivered,
    record_webhook_failure,
)
from app.database import create_database_engine
from app.schemas import EventCreate

MAX_ATTEMPTS = 3
INITIAL_RETRY_SECONDS = 5


async def deliver_one(engine: AsyncEngine, client: AsyncClient, url: URL) -> int | None:
    async with engine.begin() as connection:
        result = await claim_webhook_delivery(connection, max_attempts=MAX_ATTEMPTS)
        delivery = next(result.all(), None)

    if delivery is None:
        return None

    if delivery.status == "failed":
        print("Webhook delivery exhausted its attempts.", file=stderr)
        return 1

    attempt_count = delivery.attempt_count
    if attempt_count is None:
        raise RuntimeError("Claimed delivery has no attempt count.")

    event = EventCreate.model_validate(
        {
            "event_id": delivery.event_id,
            "event_type": delivery.event_type,
            "occurred_at": delivery.occurred_at,
            "payload": delivery.payload,
        }
    )

    try:
        async with (
            asyncio.timeout(10),
            client.stream(
                "POST",
                url,
                json=event.model_dump(mode="json"),
                headers={"Idempotency-Key": str(event.event_id)},
            ) as response,
        ):
            response.raise_for_status()
    except (HTTPError, TimeoutError) as error:
        retry_seconds = (
            INITIAL_RETRY_SECONDS * 2 ** (attempt_count - 1)
            if attempt_count < MAX_ATTEMPTS
            else None
        )
        async with engine.begin() as connection:
            result = await record_webhook_failure(
                connection,
                event_id=event.event_id,
                attempt_count=attempt_count,
                retry_seconds=retry_seconds,
            )
            failure = next(result.all(), None)
        status = failure.status if failure is not None else "claim changed"
        print(
            f"Webhook attempt failed ({type(error).__name__}). Status: {status}.",
            file=stderr,
        )
        return 1

    async with engine.begin() as connection:
        result = await mark_webhook_delivered(
            connection, event_id=event.event_id, attempt_count=attempt_count
        )
        updated = next(result.all(), None) is not None

    if not updated:
        print("Webhook delivery was claimed again before completion.", file=stderr)
        return 1

    print(f"Delivered webhook event {event.event_id}.")
    return 0


async def run_worker(url: URL, *, watch: bool) -> int:
    engine = create_database_engine()
    try:
        async with AsyncClient(trust_env=False) as client:
            while True:
                result = await deliver_one(engine, client, url)
                if not watch:
                    if result is None:
                        print("No webhook delivery is due.")
                        return 0
                    return result
                if result is None:
                    await asyncio.sleep(1)
    finally:
        await engine.dispose()


def main() -> None:
    parser = ArgumentParser(description="Send queued Relay webhook deliveries.")
    parser.add_argument("webhook_url")
    parser.add_argument(
        "--watch", action="store_true", help="Keep polling for deliveries."
    )
    args = parser.parse_args()

    try:
        url = URL(args.webhook_url)
    except InvalidURL:
        parser.error("webhook_url must be an absolute HTTP or HTTPS URL")
    if url.scheme not in {"http", "https"} or not url.host:
        parser.error("webhook_url must be an absolute HTTP or HTTPS URL")

    try:
        exit_code = asyncio.run(run_worker(url, watch=args.watch))
    except KeyboardInterrupt:
        raise SystemExit(130) from None
    raise SystemExit(exit_code)


if __name__ == "__main__":
    main()
