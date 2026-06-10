import logging
import json
import time
from typing import Any
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from .api.routes import router
from .core.config import settings

# Structured Logging Setup
class JSONFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        log_obj = {
            "level": record.levelname,
            "message": record.getMessage(),
            "timestamp": self.formatTime(record, self.datefmt),
            "module": record.module,
        }
        if hasattr(record, "extra_info"):
            log_obj.update(record.extra_info)
        return json.dumps(log_obj)

logger = logging.getLogger("stock_dashboard")
handler = logging.StreamHandler()
handler.setFormatter(JSONFormatter())
logger.addHandler(handler)
logger.setLevel(logging.INFO)

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Production-grade stock analysis and ML prediction API",
    version=settings.VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration = (time.time() - start_time) * 1000
    
    logger.info(
        f"Request: {request.method} {request.url.path}",
        extra={"extra_info": {
            "method": request.method,
            "path": request.url.path,
            "duration_ms": duration,
            "status_code": response.status_code
        }}
    )
    return response

app.include_router(router, prefix=settings.API_V1_STR)

@app.get("/")
async def root():
    return {
        "message": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "docs": "/docs",
        "health": f"{settings.API_V1_STR}/health"
    }
