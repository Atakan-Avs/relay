from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.database import lifespan
from app.routers import events, health

app = FastAPI(title="Relay", lifespan=lifespan)
app.include_router(health.router)
app.include_router(events.router)


@app.exception_handler(RequestValidationError)
async def validation_error(
    _request: Request, error: RequestValidationError
) -> JSONResponse:
    detail = [
        {"loc": item["loc"], "type": item["type"], "msg": item["msg"]}
        for item in error.errors()
    ]
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        content={"detail": detail},
    )
