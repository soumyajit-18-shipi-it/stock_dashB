import logging
import os
import time
from pathlib import Path
from typing import Any, Awaitable, Callable

from api.routes import router
from core.config import settings
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from services.ai_service import ai_service

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("stock_dashboard")

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
)


@app.on_event("startup")
def startup_event() -> None:
    logger.info("=" * 60)
    logger.info("STOCK INTELLIGENCE DASHBOARD API STARTED")
    logger.info("Local API: http://localhost:8000")
    logger.info("API docs:  http://localhost:8000/docs")
    logger.info("Note: http://0.0.0.0:8000 is a network bind address. Use localhost:8000 in your browser.")
    ai_status = ai_service.startup_diagnostics()
    logger.info("AI provider configured: %s", "yes" if ai_status["configured"] else "no")
    logger.info("AI provider name: %s", ai_status.get("provider") or "none")
    logger.info("AI model name: %s", ai_status.get("model") or "none")
    logger.info("=" * 60)


# Set all CORS enabled origins
if settings.cors_origins_list:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
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


@app.get("/favicon.ico", include_in_schema=False)
async def favicon() -> FileResponse:
    base_dir = Path(__file__).resolve().parents[1]
    paths = [
        base_dir / "frontend" / "dist" / "favicon.ico",
        base_dir / "frontend" / "public" / "favicon.ico",
    ]
    for path in paths:
        if path.exists():
            return FileResponse(path)
    # Default fallback to public favicon if exists, otherwise return 404
    fallback_path = base_dir / "frontend" / "public" / "favicon.ico"
    if fallback_path.exists():
        return FileResponse(fallback_path)
    raise HTTPException(status_code=404, detail="Favicon not found")


@app.get("/")  # nosemgrep
async def root() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/health")
async def render_health_check() -> dict[str, str]:
    return {"status": "ok"}


frontend_dist = Path(__file__).resolve().parents[1] / "frontend" / "dist"
if frontend_dist.exists():
    app.mount("/", StaticFiles(directory=frontend_dist, html=True), name="frontend")


if __name__ == "__main__":
    import uvicorn

    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", "8000"))
    uvicorn.run("main:app", host=host, port=port, reload=True)
