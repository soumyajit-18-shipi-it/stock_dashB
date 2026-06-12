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
from services.watchlist_service import WatchlistService

router = APIRouter()
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
    date_range: DateRangeEnum = DateRangeEnum.ONE_YEAR,
    model_type: ModelEnum = ModelEnum.LINEAR,
) -> StockResponse:
    try:
        # 1. Fetch analysis
        analysis = await stock_service.get_full_stock_analysis(
            ticker, date_range, model_type
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
async def save_prediction(record: PredictionRecord) -> PredictionRecord:
    return prediction_service.save_prediction(record)
