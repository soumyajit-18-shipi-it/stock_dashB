import os
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .api import router

load_dotenv()

app = FastAPI(
    title="Stock Intelligence Dashboard API",
    description="Production-grade stock analysis and ML prediction API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api/v1")


@app.get("/")
async def root():
    return {"message": "Stock Intelligence Dashboard API", "docs": "/docs"}
