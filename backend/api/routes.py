from fastapi import APIRouter, HTTPException, Query, Header, Request
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from schemas import (
    StockResponse,
    CompanyProfile,
    StockPricePoint,
    PredictionResult,
    ModelMetrics,
    WatchlistItem,
    WatchlistCreate,
    SearchHistoryItem,
    PredictionRecord,
    HealthResponse,
    DateRangeEnum,
    ModelEnum,
)
from services.stock_service import stock_service
from services import WatchlistService, HistoryService, PredictionService
from schemas import PredictionRecord as PredictionRecordSchema
from core.config import settings
import httpx
import json


router = APIRouter()
watchlist_service = WatchlistService()
history_service = HistoryService()
prediction_service = PredictionService()


def get_user_id(x_user_id: Optional[str] = Header(None)) -> Optional[str]:
    return x_user_id


@router.get("/health", response_model=HealthResponse)
async def health_check():
    return HealthResponse(status="healthy")


@router.get("/debug/metrics")
async def get_debug_metrics():
    return stock_service.last_metrics


@router.get("/debug/data-pipeline/{ticker}")
async def debug_data_pipeline(ticker: str):
    ticker = ticker.upper()
    try:
        data = await stock_service.get_full_stock_analysis(ticker)
        return {
            "ticker": ticker,
            "profile_source_merge": {
                "name": data.profile.name,
                "sector": data.profile.sector,
                "industry": data.profile.industry
            },
            "history_count": len(data.history),
            "prediction_check": data.prediction.model_dump(),
            "metrics": stock_service.last_metrics
        }
    except Exception as e:
        return {"error": str(e)}


@router.get("/stock/{ticker}", response_model=StockResponse)
async def get_stock(
    ticker: str,
    range: DateRangeEnum = Query(DateRangeEnum.ONE_YEAR),
    model: ModelEnum = Query(ModelEnum.LINEAR),
    x_user_id: Optional[str] = Header(None)
):
    try:
        data = await stock_service.get_full_stock_analysis(ticker, range, model)
        
        # Persistence
        user_id = get_user_id(x_user_id)
        history_service.add_search_history(user_id, ticker)
        
        prediction_record = PredictionRecordSchema(
            ticker=ticker,
            model=model.value,
            predicted_price=data.prediction.predicted_price,
            confidence=data.prediction.confidence,
        )
        prediction_service.save_prediction(prediction_record)
        
        return data
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching stock data: {str(e)}")


import pandas as pd


@router.post("/watchlist", response_model=WatchlistItem)
async def add_watchlist(
    item: WatchlistCreate,
    x_user_id: Optional[str] = Header(None)
):
    user_id = get_user_id(x_user_id)
    try:
        return watchlist_service.add_to_watchlist(user_id, item)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/watchlist", response_model=List[WatchlistItem])
async def get_watchlist(x_user_id: Optional[str] = Header(None)):
    user_id = get_user_id(x_user_id)
    return watchlist_service.get_watchlist(user_id)


@router.delete("/watchlist/{watchlist_id}")
async def remove_watchlist(
    watchlist_id: str,
    x_user_id: Optional[str] = Header(None)
):
    user_id = get_user_id(x_user_id)
    if not watchlist_service.remove_from_watchlist(user_id, watchlist_id):
        raise HTTPException(status_code=404, detail="Watchlist item not found")
    return {"status": "deleted"}


@router.get("/history", response_model=List[SearchHistoryItem])
async def get_search_history(x_user_id: Optional[str] = Header(None)):
    user_id = get_user_id(x_user_id)
    return history_service.get_search_history(user_id)


@router.delete("/history")
async def clear_search_history(x_user_id: Optional[str] = Header(None)):
    user_id = get_user_id(x_user_id)
    history_service.clear_search_history(user_id)
    return {"status": "cleared"}


@router.get("/predictions", response_model=List[PredictionRecord])
async def get_predictions(
    ticker: Optional[str] = Query(None),
    x_user_id: Optional[str] = Header(None)
):
    return prediction_service.get_predictions(ticker)


@router.post("/predictions", response_model=PredictionRecord)
async def save_prediction(prediction: PredictionRecord):
    return prediction_service.save_prediction(prediction)


from services.ai_service import ai_service


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    messages: List[ChatMessage]
    provider: Optional[str] = "groq"
    model: Optional[str] = None
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    temperature: Optional[float] = 0.3
    max_tokens: Optional[int] = 2000
    stream: Optional[bool] = False


class ModelOption(BaseModel):
    id: str
    name: str


@router.post("/ai/chat")
async def ai_chat(request: ChatRequest):
    """Chat completion with provider support and fallback."""
    messages = [{"role": m.role, "content": m.content} for m in request.messages]
    
    if request.stream:
        from fastapi.responses import StreamingResponse
        return StreamingResponse(
            ai_service.stream_chat(
                messages=messages,
                provider=request.provider,
                model=request.model,
                api_key=request.api_key,
                base_url=request.base_url,
                temperature=request.temperature,
                max_tokens=request.max_tokens,
            ),
            media_type="text/event-stream"
        )
    
    # Non-streaming wrapper
    full_content = ""
    async for chunk in ai_service.stream_chat(
        messages=messages,
        provider=request.provider,
        model=request.model,
        api_key=request.api_key,
        base_url=request.base_url,
        temperature=request.temperature,
        max_tokens=request.max_tokens,
    ):
        if chunk.startswith("data: "):
            data_str = chunk[6:].strip()
            if data_str == "[DONE]": break
            try:
                data = json.loads(data_str)
                if "choices" in data:
                    full_content += data["choices"][0].get("delta", {}).get("content", "")
                elif "error" in data:
                    raise HTTPException(status_code=500, detail=data["error"])
            except: pass
    
    return {"choices": [{"message": {"role": "assistant", "content": full_content}}]}


@router.get("/ai/models", response_model=List[ModelOption])
async def ai_models(
    provider: str = "groq",
    api_key: Optional[str] = None,
    base_url: Optional[str] = None
):
    """Get available models from provider."""
    models = await ai_service.get_models(provider, api_key, base_url)
    return [ModelOption(id=m["id"], name=m["name"]) for m in models]


@router.post("/ai/test")
async def ai_test(request: ChatRequest):
    """Test connection to AI provider."""
    try:
        models = await ai_service.get_models(request.provider, request.api_key, request.base_url)
        if models:
            return {"status": "connected", "models_count": len(models)}
        return {"status": "error", "message": "No models available or connection failed"}
    except Exception as e:
        return {"status": "error", "message": str(e)}
