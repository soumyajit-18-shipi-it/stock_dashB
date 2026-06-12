from fastapi import APIRouter, Header, HTTPException, Query
from schemas import (
    DateRangeEnum,
    HealthResponse,
    ModelEnum,
    PredictionRecord,
    SearchHistoryItem,
    StockResponse,
    WatchlistCreate,
    WatchlistItem,
)
from schemas import PredictionRecord as PredictionRecordSchema
from services import HistoryService, PredictionService, WatchlistService
from services.stock_service import stock_service

router = APIRouter()
watchlist_service = WatchlistService()
history_service = HistoryService()
prediction_service = PredictionService()


def get_user_id(x_user_id: str | None = Header(None)) -> str | None:
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
                "industry": data.profile.industry,
            },
            "history_count": len(data.history),
            "prediction_check": data.prediction.model_dump(),
            "metrics": stock_service.last_metrics,
        }
    except Exception as e:
        return {"error": str(e)}


@router.get("/stock/{ticker}", response_model=StockResponse)
async def get_stock(
    ticker: str,
    range: DateRangeEnum = Query(DateRangeEnum.ONE_YEAR),
    model: ModelEnum = Query(ModelEnum.LINEAR),
    x_user_id: str | None = Header(None),
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
        raise HTTPException(status_code=404, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error fetching stock data: {str(e)}"
        ) from e


@router.post("/watchlist", response_model=WatchlistItem)
async def add_watchlist(item: WatchlistCreate, x_user_id: str | None = Header(None)):
    user_id = get_user_id(x_user_id)
    try:
        return watchlist_service.add_to_watchlist(user_id, item)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.get("/watchlist", response_model=list[WatchlistItem])
async def get_watchlist(x_user_id: str | None = Header(None)):
    user_id = get_user_id(x_user_id)
    return watchlist_service.get_watchlist(user_id)


@router.delete("/watchlist/{watchlist_id}")
async def remove_watchlist(watchlist_id: str, x_user_id: str | None = Header(None)):
    user_id = get_user_id(x_user_id)
    if not watchlist_service.remove_from_watchlist(user_id, watchlist_id):
        raise HTTPException(status_code=404, detail="Watchlist item not found")
    return {"status": "deleted"}


@router.get("/history", response_model=list[SearchHistoryItem])
async def get_search_history(x_user_id: str | None = Header(None)):
    user_id = get_user_id(x_user_id)
    return history_service.get_search_history(user_id)


@router.delete("/history")
async def clear_search_history(x_user_id: str | None = Header(None)):
    user_id = get_user_id(x_user_id)
    history_service.clear_search_history(user_id)
    return {"status": "cleared"}


@router.get("/predictions", response_model=list[PredictionRecord])
async def get_predictions(
    ticker: str | None = Query(None), x_user_id: str | None = Header(None)
):
    return prediction_service.get_predictions(ticker)


@router.post("/predictions", response_model=PredictionRecord)
async def save_prediction(prediction: PredictionRecord):
    return prediction_service.save_prediction(prediction)
