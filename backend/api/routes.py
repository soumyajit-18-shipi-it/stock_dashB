from datetime import datetime
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
from services.watchlist_service import WatchlistService
from services.ai_service import (
    AI_PROVIDER_SETUP_HINT,
    AIProviderError,
    AIProviderNotConfigured,
    ai_service,
)
from ml.indic_intent_model import get_indic_intent_classifier

router = APIRouter()


@router.get("/test-route")
async def test_route() -> Any:
    return {"message": "test route working"}


watchlist_service = WatchlistService()
history_service = HistoryService()
prediction_service = PredictionService()
_stock_service: Any = None


def _get_stock_service() -> Any:
    global _stock_service
    if _stock_service is None:
        from services.stock_service import stock_service

        _stock_service = stock_service
    return _stock_service


def _parse_datetime(value: Any) -> Any:
    from datetime import timezone

    if not value:
        return None
    if hasattr(value, "tzinfo"):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    if not isinstance(value, str):
        return None
    try:
        normalized = value[:-1] + "+00:00" if value.endswith("Z") else value
        parsed = datetime.fromisoformat(normalized)
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
    except Exception:
        return None


def _fallback_name_from_email(email: str | None) -> str:
    if not email or "@" not in email:
        return "Unknown User"
    prefix = email.split("@", 1)[0].replace(".", " ").replace("_", " ").replace("-", " ")
    return prefix.title() or "Unknown User"


def _profile_sort_value(profile: dict[str, Any], field: str) -> str:
    return str(profile.get(field) or profile.get("created_at") or "")


def _load_table(client: Any, table_name: str) -> list[dict[str, Any]]:
    try:
        return cast(list[dict[str, Any]], client.table(table_name).select("*").execute().data or [])
    except Exception:
        return []


def _count_by_user(rows: list[dict[str, Any]], user_field: str = "user_id") -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        user_id = row.get(user_field)
        if user_id:
            counts[str(user_id)] = counts.get(str(user_id), 0) + 1
    return counts


def _build_profile_indexes(
    profiles: list[dict[str, Any]]
) -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    by_id = {str(p.get("id")): p for p in profiles if p.get("id")}
    by_email = {
        str(p.get("email")).lower(): p
        for p in profiles
        if p.get("email")
    }
    return by_id, by_email


def _enrich_feedback(
    feedback: list[dict[str, Any]],
    profiles_by_id: dict[str, dict[str, Any]],
    profiles_by_email: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    enriched = []
    for item in feedback:
        email = item.get("email")
        profile = None
        if item.get("user_id"):
            profile = profiles_by_id.get(str(item.get("user_id")))
        if not profile and email:
            profile = profiles_by_email.get(str(email).lower())

        submitter_email = email or (profile or {}).get("email")
        enriched.append({
            **item,
            "email": submitter_email,
            "submitter_name": (profile or {}).get("full_name") or _fallback_name_from_email(submitter_email),
            "submitter_avatar_url": (profile or {}).get("avatar_url"),
            "submitter_provider": (profile or {}).get("provider"),
        })
    return enriched


def _summarize_users(
    profiles: list[dict[str, Any]],
    feedback_counts: dict[str, int],
    watchlist_counts: dict[str, int],
    search_counts: dict[str, int],
    *,
    limit: int,
) -> list[dict[str, Any]]:
    sorted_profiles = sorted(
        profiles,
        key=lambda p: _profile_sort_value(p, "first_seen_at"),
        reverse=True,
    )
    summaries = []
    for profile in sorted_profiles[:limit]:
        user_id = str(profile.get("id") or "")
        email = profile.get("email")
        summaries.append({
            "id": user_id,
            "email": email,
            "full_name": profile.get("full_name") or _fallback_name_from_email(email),
            "avatar_url": profile.get("avatar_url"),
            "provider": profile.get("provider") or "google",
            "first_seen_at": profile.get("first_seen_at") or profile.get("created_at"),
            "last_seen_at": profile.get("last_seen_at") or profile.get("updated_at"),
            "total_feedback_count": feedback_counts.get(user_id, 0),
            "total_watchlist_items": watchlist_counts.get(user_id, 0),
            "total_searches": search_counts.get(user_id, 0),
        })
    return summaries


@router.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "healthy"}


@router.get("/health/ai")
async def ai_health_check() -> dict[str, Any]:
    return ai_service.health()


def _ai_error_payload(exc: AIProviderError) -> dict[str, str]:
    payload = {
        "error": str(exc),
        "code": exc.code,
    }
    if isinstance(exc, AIProviderNotConfigured):
        payload["setup_hint"] = AI_PROVIDER_SETUP_HINT
    return payload


def _raise_ai_http_error(exc: AIProviderError) -> None:
    raise HTTPException(status_code=exc.status_code, detail=_ai_error_payload(exc))


@router.post("/auth/sync-profile")
async def sync_auth_profile(
    current_user: UserPayload = Depends(require_authenticated_user),
) -> dict[str, bool]:
    from datetime import timezone

    client = get_supabase_client()
    now_str = datetime.now(timezone.utc).isoformat()
    try:
        existing = (
            client.table("user_profiles")
            .select("*")
            .eq("id", current_user.user_id)
            .execute()
            .data
            or []
        )
        existing_profile = existing[0] if existing else {}
        data = {
            "id": current_user.user_id,
            "email": current_user.email or existing_profile.get("email"),
            "full_name": existing_profile.get("full_name") or _fallback_name_from_email(current_user.email),
            "avatar_url": existing_profile.get("avatar_url") or "",
            "provider": existing_profile.get("provider") or "google",
            "last_seen_at": now_str,
            "updated_at": now_str,
        }
        if not existing:
            data["first_seen_at"] = now_str
            data["created_at"] = now_str
        client.table("user_profiles").upsert(data, on_conflict="id").execute()
        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to sync user profile") from e


@router.get("/debug/data")
async def debug_data_pipeline(ticker: str = "AAPL") -> dict[str, Any]:
    try:
        data = await _get_stock_service().get_full_stock_analysis(ticker)
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
        analysis = await _get_stock_service().get_full_stock_analysis(
            ticker, range, model
        )

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

    prov = request.provider or "auto"
    temp = request.temperature if request.temperature is not None else 0.3
    max_tok = request.max_tokens if request.max_tokens is not None else 8000

    try:
        ai_service.resolve_provider(prov, request.model)
    except AIProviderError as exc:
        _raise_ai_http_error(exc)

    if request.stream:
        from fastapi.responses import StreamingResponse

        return StreamingResponse(
            ai_service.stream_chat(
                messages=messages,
                provider=prov,
                model=request.model,
                temperature=temp,
                max_tokens=max_tok,
            ),
            media_type="text/event-stream",
        )

    try:
        full_content = await ai_service.complete_chat(
            messages=messages,
            provider=prov,
            model=request.model,
            temperature=temp,
            max_tokens=max_tok,
        )
    except AIProviderError as exc:
        _raise_ai_http_error(exc)

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
        feedback = res.data or []
        profiles = _load_table(client, "user_profiles")
        profiles_by_id, profiles_by_email = _build_profile_indexes(profiles)
        enriched = _enrich_feedback(feedback, profiles_by_id, profiles_by_email)
        return sorted(enriched, key=lambda f: str(f.get("created_at") or ""), reverse=True)
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
            created_dt = _parse_datetime(p.get("first_seen_at") or p.get("created_at"))
            if not created_dt:
                continue
            delta = now_utc - created_dt
            if delta.days < 1:
                new_users_today += 1
            if delta.days < 7:
                new_users_this_week += 1
                
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
        profiles = _load_table(client, "user_profiles")
        feedback = _load_table(client, "feedback_issues")
        watchlists = _load_table(client, "watchlists")
        searches = _load_table(client, "search_history")
        
        now_utc = datetime.now(timezone.utc)
        total_users = len(profiles)
        new_users_today = 0
        new_users_this_week = 0
        active_today = 0
        
        for p in profiles:
            created_dt = _parse_datetime(p.get("first_seen_at") or p.get("created_at"))
            if created_dt:
                delta = now_utc - created_dt
                if delta.days < 1:
                    new_users_today += 1
                if delta.days < 7:
                    new_users_this_week += 1

            last_seen_dt = _parse_datetime(p.get("last_seen_at") or p.get("updated_at"))
            if last_seen_dt and (now_utc - last_seen_dt).days < 1:
                active_today += 1
                
        total_feedback = len(feedback)
        open_feedback = sum(1 for f in feedback if f.get("status") == "open")
        feedback_counts = _count_by_user(feedback)
        watchlist_counts = _count_by_user(watchlists)
        search_counts = _count_by_user(searches)
        profiles_by_id, profiles_by_email = _build_profile_indexes(profiles)
        enriched_feedback = _enrich_feedback(feedback, profiles_by_id, profiles_by_email)
        enriched_feedback = sorted(
            enriched_feedback,
            key=lambda f: str(f.get("created_at") or ""),
            reverse=True,
        )
        users = _summarize_users(
            profiles,
            feedback_counts,
            watchlist_counts,
            search_counts,
            limit=50,
        )
        
        return {
            "total_users": total_users,
            "new_users_today": new_users_today,
            "new_users_this_week": new_users_this_week,
            "active_today": active_today,
            "total_feedback_issues": total_feedback,
            "open_feedback_issues": open_feedback,
            "latest_signups": users[:10],
            "recent_feedback": enriched_feedback[:20],
            "users": users,
            "last_updated": now_utc
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
