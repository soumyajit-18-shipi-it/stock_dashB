"""Versioned explainable-investment and portfolio API routes."""

from __future__ import annotations

import asyncio
from functools import lru_cache
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from core.auth import UserPayload, require_authenticated_user
from explainability import PredictionExplanationService
from portfolio.jobs import portfolio_job_manager
from portfolio.persistence import portfolio_persistence
from portfolio.service import PortfolioService
from portfolio.types import HoldingPosition
from recommendation_engine import RecommendationService
from schemas import (
    DateRangeEnum,
    InvestmentHorizon,
    ModelEnum,
    PortfolioAnalysisResponse,
    PortfolioAnalyzeRequest,
    PortfolioCsvRequest,
    PortfolioCsvResponse,
    PortfolioExplainRequest,
    PortfolioExplanationResponse,
    PortfolioHoldingInput,
    PortfolioJobResponse,
    PortfolioSaveRequest,
    PredictionExplanationResponse,
    RecommendationExplainRequest,
    RecommendationExplanationResponse,
    RecommendationResponse,
    RiskTolerance,
)
from services.ai_service import AIProviderError
from services.watchlist_service import WatchlistService

router = APIRouter(tags=["investment-intelligence"])


@lru_cache(maxsize=1)
def get_recommendation_service() -> RecommendationService:
    return RecommendationService()


@lru_cache(maxsize=1)
def get_explanation_service() -> PredictionExplanationService:
    recommendation = get_recommendation_service()
    return recommendation.explanations


@lru_cache(maxsize=1)
def get_portfolio_service() -> PortfolioService:
    return PortfolioService()


def _positions(items: list[PortfolioHoldingInput]) -> list[HoldingPosition]:
    return [
        HoldingPosition(
            ticker=item.ticker,
            quantity=item.quantity,
            average_cost=item.average_cost,
            weight=item.weight,
        )
        for item in items
    ]


@router.get(
    "/recommendation/{ticker}",
    response_model=RecommendationResponse,
)
async def get_recommendation(
    ticker: str,
    range: DateRangeEnum = Query(default=DateRangeEnum.ONE_YEAR),
    model: ModelEnum = Query(default=ModelEnum.RANDOM_FOREST),
    risk_tolerance: RiskTolerance = Query(default=RiskTolerance.BALANCED),
    horizon: InvestmentHorizon = Query(default=InvestmentHorizon.MEDIUM),
    service: RecommendationService = Depends(get_recommendation_service),
) -> Any:
    try:
        result = await service.get_recommendation(
            ticker, range, model, risk_tolerance.value, horizon.value
        )
        return result.to_dict()
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post(
    "/recommendation/explain",
    response_model=RecommendationExplanationResponse,
)
async def explain_recommendation(
    request: RecommendationExplainRequest,
    service: RecommendationService = Depends(get_recommendation_service),
) -> Any:
    try:
        explanation = await service.explain_recommendation(
            request.recommendation.model_dump()
        )
        return {"explanation": explanation}
    except AIProviderError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc


@router.get(
    "/prediction/explanation",
    response_model=PredictionExplanationResponse,
)
async def get_prediction_explanation(
    ticker: str = Query(min_length=1, max_length=20),
    range: DateRangeEnum = Query(default=DateRangeEnum.ONE_YEAR),
    model: ModelEnum = Query(default=ModelEnum.RANDOM_FOREST),
    service: PredictionExplanationService = Depends(get_explanation_service),
) -> Any:
    try:
        return await asyncio.to_thread(service.explain, ticker, range, model)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/portfolio/parse-csv", response_model=PortfolioCsvResponse)
async def parse_portfolio_csv(
    request: PortfolioCsvRequest,
    service: PortfolioService = Depends(get_portfolio_service),
) -> Any:
    try:
        return {
            "holdings": [
                {
                    "ticker": item.ticker,
                    "quantity": item.quantity,
                    "average_cost": item.average_cost,
                    "weight": item.weight,
                }
                for item in service.parse_csv(request.content)
            ]
        }
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/portfolio/analyze", response_model=PortfolioAnalysisResponse)
async def analyze_portfolio(
    request: PortfolioAnalyzeRequest,
    service: PortfolioService = Depends(get_portfolio_service),
) -> Any:
    try:
        result = await service.analyze(_positions(request.holdings), request.range)
        return result.to_dict()
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post(
    "/portfolio/analyze-watchlist",
    response_model=PortfolioAnalysisResponse,
)
async def analyze_watchlist(
    request: Request,
    range: str = Query(default="5y", pattern="^(1y|5y)$"),
    user: UserPayload = Depends(require_authenticated_user),
    service: PortfolioService = Depends(get_portfolio_service),
) -> Any:
    del request
    watchlist = WatchlistService().get_watchlist(user.user_id)
    if not watchlist:
        raise HTTPException(status_code=400, detail="Watchlist is empty")
    weight = 1.0 / len(watchlist)
    positions = [
        HoldingPosition(ticker=item["ticker"], weight=weight)
        for item in watchlist[:30]
    ]
    result = await service.analyze(positions, range)
    return result.to_dict()


@router.post("/portfolio/jobs", response_model=PortfolioJobResponse)
async def submit_portfolio_job(
    request: PortfolioAnalyzeRequest,
    service: PortfolioService = Depends(get_portfolio_service),
) -> Any:
    positions = _positions(request.holdings)

    async def factory() -> dict[str, Any]:
        result = await service.analyze(positions, request.range)
        return result.to_dict()

    job = portfolio_job_manager.submit(factory)
    return {
        "job_id": job.job_id,
        "status": job.status,
        "result": None,
        "error": None,
    }


@router.get("/portfolio/jobs/{job_id}", response_model=PortfolioJobResponse)
async def get_portfolio_job(job_id: str) -> Any:
    job = portfolio_job_manager.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Portfolio job not found")
    return {
        "job_id": job.job_id,
        "status": job.status,
        "result": job.result,
        "error": job.error,
    }


@router.post(
    "/portfolio/explain",
    response_model=PortfolioExplanationResponse,
)
async def explain_portfolio(
    request: PortfolioExplainRequest,
    service: PortfolioService = Depends(get_portfolio_service),
) -> Any:
    try:
        analysis = PortfolioAnalysisResponse.model_validate(request.analysis)
        explanation = await service.ai_service.complete_chat(
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Explain the deterministic portfolio analytics supplied "
                        "by the user. Never change scores or invent facts. This is "
                        "decision support, not individualized financial advice."
                    ),
                },
                {
                    "role": "user",
                    "content": analysis.model_dump_json(),
                },
            ],
            provider="auto",
            temperature=0.1,
            max_tokens=900,
        )
        return {"explanation": explanation}
    except AIProviderError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc


@router.post("/portfolios")
async def save_portfolio(
    request: PortfolioSaveRequest,
    http_request: Request,
    user: UserPayload = Depends(require_authenticated_user),
) -> Any:
    del http_request
    return portfolio_persistence.save(
        user.user_id,
        request.name,
        _positions(request.holdings),
        request.analysis_snapshot.model_dump()
        if request.analysis_snapshot is not None
        else None,
    )


@router.get("/portfolios")
async def list_portfolios(
    request: Request,
    user: UserPayload = Depends(require_authenticated_user),
) -> Any:
    del request
    return portfolio_persistence.list_for_user(user.user_id)


@router.get("/portfolios/{portfolio_id}")
async def get_saved_portfolio(
    portfolio_id: str,
    request: Request,
    user: UserPayload = Depends(require_authenticated_user),
) -> Any:
    del request
    result = portfolio_persistence.get(user.user_id, portfolio_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    return result


@router.delete("/portfolios/{portfolio_id}")
async def delete_saved_portfolio(
    portfolio_id: str,
    request: Request,
    user: UserPayload = Depends(require_authenticated_user),
) -> dict[str, bool]:
    del request
    return {
        "deleted": portfolio_persistence.delete(user.user_id, portfolio_id)
    }
