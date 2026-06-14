
from fastapi import APIRouter, HTTPException, Query, Header, Request
from typing import List, Optional, Dict, Any
from pydantic import BaseModel

from typing import Any, cast

from fastapi import APIRouter, HTTPException
from schemas import (
    DateRangeEnum,
    ModelEnum,
    PredictionRecord,
    StockResponse,
    WatchlistItem,
)
from services.history_service import HistoryService
from services.prediction_service import PredictionService
from services.stock_service import stock_service

from services import WatchlistService, HistoryService, PredictionService
from schemas import PredictionRecord as PredictionRecordSchema
from core.config import settings
import httpx
import json


from services.watchlist_service import WatchlistService

router = APIRouter()

@router.get("/test-route")
async def test_route():
    return {"message": "test route working"}
watchlist_service = WatchlistService()
history_service = HistoryService()
prediction_service = PredictionService()


@router.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "healthy"}


@router.get("/debug/data")
async def debug_data_pipeline(ticker: str = "AAPL") -> dict[str, Any]:
    try:
        data = await stock_service.get_full_stock_analysis(ticker)
        return {"status": "success", "data": data.dict()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/stock/{ticker}", response_model=StockResponse)
async def get_stock(
    ticker: str,
    range: DateRangeEnum = DateRangeEnum.ONE_YEAR,
    model: ModelEnum = ModelEnum.LINEAR,
) -> StockResponse:
    try:
        # 1. Fetch analysis
        analysis = await stock_service.get_full_stock_analysis(
            ticker, range, model
        )

        # 2. Add to search history (silently)
        try:
            history_service.add_search_history(None, ticker)
        except Exception:
            pass

        return analysis
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/watchlist/{ticker}", response_model=WatchlistItem)
async def add_watchlist(ticker: str) -> WatchlistItem:
    return watchlist_service.add_to_watchlist(None, ticker)


@router.get("/watchlist", response_model=list[WatchlistItem])
async def get_watchlist() -> list[WatchlistItem]:
    return cast(list[WatchlistItem], watchlist_service.get_watchlist(None))


@router.delete("/watchlist/{ticker}")
async def remove_watchlist(ticker: str) -> dict[str, bool]:
    success = watchlist_service.remove_from_watchlist(None, ticker)
    return {"success": success}


@router.get("/history", response_model=list[Any])
async def get_search_history() -> list[Any]:
    return cast(list[Any], history_service.get_search_history(None))


@router.delete("/history")
async def clear_search_history() -> dict[str, bool]:
    success = history_service.clear_search_history(None)
    return {"success": success}


@router.get("/predictions", response_model=list[PredictionRecord])
async def get_predictions() -> list[PredictionRecord]:
    return cast(list[PredictionRecord], prediction_service.get_predictions(None))


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
    max_tokens: Optional[int] = 8000
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

async def save_prediction(record: PredictionRecord) -> PredictionRecord:
    return prediction_service.save_prediction(record)
