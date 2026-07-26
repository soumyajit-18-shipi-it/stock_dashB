"""Bounded in-process background jobs for expensive portfolio analysis."""

from __future__ import annotations

import asyncio
import time
import uuid
from dataclasses import dataclass
from typing import Any, Awaitable, Callable


@dataclass
class PortfolioJob:
    job_id: str
    status: str
    created_at: float
    updated_at: float
    result: dict[str, Any] | None = None
    error: str | None = None


class PortfolioJobManager:
    def __init__(self, max_concurrent: int = 2, ttl_seconds: int = 3600) -> None:
        self._jobs: dict[str, PortfolioJob] = {}
        self._semaphore = asyncio.Semaphore(max_concurrent)
        self.ttl_seconds = ttl_seconds

    def submit(
        self, factory: Callable[[], Awaitable[dict[str, Any]]]
    ) -> PortfolioJob:
        self._prune()
        job_id = str(uuid.uuid4())
        now = time.time()
        job = PortfolioJob(job_id, "queued", now, now)
        self._jobs[job_id] = job
        asyncio.create_task(self._run(job, factory))
        return job

    def get(self, job_id: str) -> PortfolioJob | None:
        self._prune()
        return self._jobs.get(job_id)

    async def _run(
        self,
        job: PortfolioJob,
        factory: Callable[[], Awaitable[dict[str, Any]]],
    ) -> None:
        async with self._semaphore:
            job.status = "running"
            job.updated_at = time.time()
            try:
                job.result = await factory()
                job.status = "completed"
            except Exception as exc:  # pylint: disable=broad-exception-caught
                job.error = str(exc)
                job.status = "failed"
            job.updated_at = time.time()

    def _prune(self) -> None:
        cutoff = time.time() - self.ttl_seconds
        expired = [
            job_id
            for job_id, job in self._jobs.items()
            if job.updated_at < cutoff
        ]
        for job_id in expired:
            self._jobs.pop(job_id, None)


portfolio_job_manager = PortfolioJobManager()
