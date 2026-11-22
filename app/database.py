from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from app.config import Settings


@asynccontextmanager
async def lifespan(application: FastAPI) -> AsyncGenerator[None]:
    application.state.event_engine = None
    try:
        yield
    finally:
        engine: AsyncEngine | None = application.state.event_engine
        if engine is not None:
            await engine.dispose()


def get_database_engine(application: FastAPI) -> AsyncEngine:
    engine: AsyncEngine | None = application.state.event_engine
    if engine is None:
        settings = Settings.model_validate({})
        engine = create_async_engine(
            settings.database_url,
            connect_args={"connect_timeout": 5},
            hide_parameters=True,
        )
        application.state.event_engine = engine
    return engine
