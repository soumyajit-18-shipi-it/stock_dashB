import logging
import os
import time
from typing import Any, Awaitable, Callable

from api.routes import router
from core.config import settings
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("stock_dashboard")

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
)

# Set all CORS enabled origins
if settings.CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


@app.middleware("http")  # nosemgrep
async def log_requests(
    request: Request, call_next: Callable[[Request], Awaitable[Any]]
) -> Any:
    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time
    logger.info(
        f"Path: {request.url.path} Method: {request.method} "
        f"Duration: {duration:.2f}s Status: {response.status_code}"
    )
    return response


app.include_router(router, prefix=settings.API_V1_STR)


@app.get("/")  # nosemgrep
async def root() -> dict[str, str]:

    return {
        "message": "Welcome to Stock Intelligence Dashboard API",
        "docs": "/docs",
        "version": settings.VERSION,
    }


if __name__ == "__main__":
    import uvicorn

    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", "8000"))
    uvicorn.run("main:app", host=host, port=port, reload=True)
