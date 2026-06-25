import json
from typing import List, Optional, Any, cast
from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel

from database.supabase_client import get_supabase_client
from core.auth import require_authenticated_user, require_admin_user, UserPayload
from core.auth import get_current_user
from schemas import (
    DateRangeEnum,
    ModelEnum,
    PredictionRecord,
    StockResponse,
    WatchlistItem,
    WatchlistCreate,
    SearchHistoryCreate,
    FeedbackCreate,
    FeedbackResponse,
    AdminUserCountResponse,
    AdminStatsResponse,
)
from services.history_service import HistoryService
from services.prediction_service import PredictionService
from services.stock_service import stock_service
from services.watchlist_service import WatchlistService
from services.ai_service import ai_service
from ml.indic_intent_model import get_indic_intent_classifier

router = APIRouter()


@router.get("/test-route")
async def test_route() -> Any:
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
    request: Request,
    ticker: str,
    range: DateRangeEnum = DateRangeEnum.ONE_YEAR,
    model: ModelEnum = ModelEnum.LINEAR,
) -> StockResponse:
    try:
        # 1. Fetch analysis
        analysis = await stock_service.get_full_stock_analysis(ticker, range, model)

        # 2. Add to search history (silently)
        try:
            current_user = await get_current_user(request)
            history_service.add_search_history(current_user.user_id, ticker, ticker)
        except Exception:
            pass

        return analysis
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/watchlist", response_model=WatchlistItem)
async def add_watchlist(
    item: WatchlistCreate,
    current_user: UserPayload = Depends(require_authenticated_user),
) -> Any:
    company_name = item.company_name or item.name
    return cast(
        Any,
        watchlist_service.add_to_watchlist(
            current_user.user_id, item.ticker, company_name
        ),
    )


@router.post("/watchlist/{ticker}", response_model=WatchlistItem)
async def add_watchlist_by_ticker(
    ticker: str,
    current_user: UserPayload = Depends(require_authenticated_user),
) -> Any:
    return cast(
        Any,
        watchlist_service.add_to_watchlist(current_user.user_id, ticker),
    )


@router.get("/watchlist", response_model=list[WatchlistItem])
async def get_watchlist(
    current_user: UserPayload = Depends(require_authenticated_user),
) -> list[WatchlistItem]:
    return cast(
        list[WatchlistItem], watchlist_service.get_watchlist(current_user.user_id)
    )


@router.delete("/watchlist/{identifier}")
async def remove_watchlist(
    identifier: str,
    current_user: UserPayload = Depends(require_authenticated_user),
) -> dict[str, bool]:
    success = watchlist_service.remove_from_watchlist(current_user.user_id, identifier)
    return {"success": success}


@router.get("/history", response_model=list[Any])
async def get_search_history(
    current_user: UserPayload = Depends(require_authenticated_user),
) -> list[Any]:
    return cast(list[Any], history_service.get_search_history(current_user.user_id))


@router.post("/history", response_model=Any)
async def add_search_history(
    item: SearchHistoryCreate,
    current_user: UserPayload = Depends(require_authenticated_user),
) -> Any:
    return history_service.add_search_history(
        current_user.user_id, item.query, item.ticker
    )


@router.delete("/history")
async def clear_search_history(
    current_user: UserPayload = Depends(require_authenticated_user),
) -> dict[str, bool]:
    success = history_service.clear_search_history(current_user.user_id)
    return {"success": success}


@router.get("/predictions", response_model=list[PredictionRecord])
async def get_predictions(
    current_user: UserPayload = Depends(require_authenticated_user),
) -> list[PredictionRecord]:
    return cast(
        list[PredictionRecord], prediction_service.get_predictions(current_user.user_id)
    )


@router.post("/predictions", response_model=PredictionRecord)
async def save_prediction(
    prediction: PredictionRecord,
    current_user: UserPayload = Depends(require_authenticated_user),
) -> Any:
    return prediction_service.save_prediction(prediction, current_user.user_id)


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
async def ai_chat(request: ChatRequest) -> Any:
    """Chat completion with provider support and fallback."""
    if not request.messages:
        raise HTTPException(status_code=400, detail="At least one chat message is required")

    messages = [{"role": m.role, "content": m.content} for m in request.messages]
    last_user_message = next(
        (m["content"] for m in reversed(messages) if m["role"].lower() == "user"),
        "",
    )
    intent_prediction = get_indic_intent_classifier().predict(last_user_message)
    if intent_prediction is not None:
        messages.insert(
            0,
            {
                "role": "system",
                "content": (
                    "Indic finance query routing context: "
                    f"predicted_intent={intent_prediction.intent}, "
                    f"confidence={intent_prediction.confidence}. "
                    "Use this only as a routing hint; answer from the provided stock data "
                    "and avoid giving personalized financial advice."
                ),
            },
        )

    prov = request.provider or "groq"
    temp = request.temperature if request.temperature is not None else 0.3
    max_tok = request.max_tokens if request.max_tokens is not None else 8000

    if request.stream:
        from fastapi.responses import StreamingResponse

        return StreamingResponse(
            ai_service.stream_chat(
                messages=messages,
                provider=prov,
                model=request.model,
                api_key=request.api_key,
                base_url=request.base_url,
                temperature=temp,
                max_tokens=max_tok,
            ),
            media_type="text/event-stream",
        )

    # Non-streaming wrapper
    full_content = ""
    provider_error = ""
    async for chunk in ai_service.stream_chat(
        messages=messages,
        provider=prov,
        model=request.model,
        api_key=request.api_key,
        base_url=request.base_url,
        temperature=temp,
        max_tokens=max_tok,
    ):
        if chunk.startswith("data: "):
            data_str = chunk[6:].strip()
            if data_str == "[DONE]":
                break
            try:
                data = json.loads(data_str)
                if "choices" in data:
                    full_content += (
                        data["choices"][0].get("delta", {}).get("content", "")
                    )
                elif "error" in data:
                    provider_error = str(data["error"])
            except Exception:
                pass

    if provider_error:
        raise HTTPException(status_code=503, detail=provider_error)

    return {"choices": [{"message": {"role": "assistant", "content": full_content}}]}


@router.get("/ai/models", response_model=List[ModelOption])
async def ai_models(
    provider: str = "groq",
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
) -> List[ModelOption]:
    """Get available models from provider."""
    models = await ai_service.get_models(provider, api_key, base_url)
    return [ModelOption(id=m["id"], name=m["name"]) for m in models]


@router.post("/ai/test")
async def ai_test(request: ChatRequest) -> Any:
    """Test connection to AI provider."""
    try:
        models = await ai_service.get_models(
            request.provider or "groq", request.api_key, request.base_url
        )
        if models:
            return {"status": "connected", "models_count": len(models)}
        return {
            "status": "error",
            "message": "No models available or connection failed",
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}


@router.post("/feedback", response_model=FeedbackResponse)
async def create_feedback(
    feedback_in: FeedbackCreate,
    current_user: UserPayload = Depends(require_authenticated_user),
) -> Any:
    valid_categories = {'feature_request', 'bug_report', 'documentation_issue', 'setup_query', 'development_query'}
    if feedback_in.category not in valid_categories:
        raise HTTPException(status_code=400, detail=f"Invalid category: {feedback_in.category}")

    from datetime import datetime, timezone
    now_str = datetime.now(timezone.utc).isoformat()
    client = get_supabase_client()
    data = {
        "user_id": current_user.user_id,
        "email": current_user.email,
        "category": feedback_in.category,
        "title": feedback_in.title,
        "description": feedback_in.description,
        "page_url": feedback_in.page_url,
        "screenshot_url": feedback_in.screenshot_url,
        "status": "open",
        "priority": "normal",
        "created_at": now_str,
        "updated_at": now_str,
    }
    try:
        res = client.table("feedback_issues").insert(data).execute()
        if not res.data:
            raise HTTPException(status_code=500, detail="Failed to save feedback")
        return res.data[0]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.get("/feedback/my", response_model=List[FeedbackResponse])
async def get_my_feedback(
    current_user: UserPayload = Depends(require_authenticated_user),
) -> Any:
    client = get_supabase_client()
    try:
        res = client.table("feedback_issues").select("*").eq("user_id", current_user.user_id).execute()
        return res.data or []
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.get("/admin/feedback", response_model=List[FeedbackResponse])
async def get_admin_feedback(
    status: Optional[str] = None,
    category: Optional[str] = None,
    priority: Optional[str] = None,
    current_user: UserPayload = Depends(require_admin_user),
) -> Any:
    client = get_supabase_client()
    try:
        query = client.table("feedback_issues").select("*")
        if status:
            query = query.eq("status", status)
        if category:
            query = query.eq("category", category)
        if priority:
            query = query.eq("priority", priority)
        res = query.execute()
        return res.data or []
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.get("/admin/user-count", response_model=AdminUserCountResponse)
async def get_admin_user_count(
    current_user: UserPayload = Depends(require_admin_user),
) -> Any:
    from datetime import datetime, timezone
    client = get_supabase_client()
    try:
        res = client.table("user_profiles").select("*").execute()
        profiles = res.data or []
        
        now_utc = datetime.now(timezone.utc)
        total_users = len(profiles)
        new_users_today = 0
        new_users_this_week = 0
        
        for p in profiles:
            created_str = p.get("created_at")
            if not created_str:
                continue
            try:
                if created_str.endswith("Z"):
                    created_str = created_str[:-1] + "+00:00"
                created_dt = datetime.fromisoformat(created_str)
                if created_dt.tzinfo is None:
                    created_dt = created_dt.replace(tzinfo=timezone.utc)
                
                delta = now_utc - created_dt
                if delta.days < 1:
                    new_users_today += 1
                if delta.days < 7:
                    new_users_this_week += 1
            except Exception:
                pass
                
        return {
            "total_users": total_users,
            "new_users_today": new_users_today,
            "new_users_this_week": new_users_this_week,
            "last_updated": now_utc
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.get("/admin/stats", response_model=AdminStatsResponse)
async def get_admin_stats(
    current_user: UserPayload = Depends(require_admin_user),
) -> Any:
    from datetime import datetime, timezone
    client = get_supabase_client()
    try:
        res_users = client.table("user_profiles").select("*").execute()
        profiles = res_users.data or []
        
        res_feedback = client.table("feedback_issues").select("*").execute()
        feedback = res_feedback.data or []
        
        now_utc = datetime.now(timezone.utc)
        total_users = len(profiles)
        new_users_today = 0
        new_users_this_week = 0
        
        for p in profiles:
            created_str = p.get("created_at")
            if not created_str:
                continue
            try:
                if created_str.endswith("Z"):
                    created_str = created_str[:-1] + "+00:00"
                created_dt = datetime.fromisoformat(created_str)
                if created_dt.tzinfo is None:
                    created_dt = created_dt.replace(tzinfo=timezone.utc)
                
                delta = now_utc - created_dt
                if delta.days < 1:
                    new_users_today += 1
                if delta.days < 7:
                    new_users_this_week += 1
            except Exception:
                pass
                
        total_feedback = len(feedback)
        open_feedback = sum(1 for f in feedback if f.get("status") == "open")
        
        return {
            "total_users": total_users,
            "new_users_today": new_users_today,
            "new_users_this_week": new_users_this_week,
            "total_feedback_issues": total_feedback,
            "open_feedback_issues": open_feedback,
            "last_updated": now_utc
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
