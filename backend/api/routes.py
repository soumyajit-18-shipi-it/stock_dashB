from fastapi import APIRouter, HTTPException, Query, Header
from typing import List, Optional
from ..schemas import (
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
from ..data.provider import StockDataProvider
from ..features.engineering import FeatureEngineer
from ..ml.predictor import StockPredictor
from ..services import WatchlistService, HistoryService, PredictionService
from ..schemas import PredictionRecord as PredictionRecordSchema


router = APIRouter()
data_provider = StockDataProvider()
feature_engineer = FeatureEngineer()
predictor = StockPredictor()
watchlist_service = WatchlistService()
history_service = HistoryService()
prediction_service = PredictionService()


def get_user_id(x_user_id: Optional[str] = Header(None)) -> str:
    return x_user_id or "anonymous"


@router.get("/health", response_model=HealthResponse)
async def health_check():
    return HealthResponse(status="healthy")


@router.get("/stock/{ticker}", response_model=StockResponse)
async def get_stock(
    ticker: str,
    range: DateRangeEnum = Query(DateRangeEnum.ONE_YEAR),
    model: ModelEnum = Query(ModelEnum.LINEAR),
    x_user_id: Optional[str] = Header(None)
):
    ticker = ticker.upper()
    try:
        df = data_provider.get_stock_data(ticker, range.value)
        df = feature_engineer.prepare_features(df)

        profile_data = data_provider.get_company_info(ticker)
        profile = CompanyProfile(**profile_data)

        history = []
        for idx, row in df.iterrows():
            point = StockPricePoint(
                date=idx.strftime("%Y-%m-%d"),
                open=float(row["Open"]),
                high=float(row["High"]),
                low=float(row["Low"]),
                close=float(row["Close"]),
                volume=int(row["Volume"]),
                ma7=float(row["ma7"]) if pd.notna(row.get("ma7")) else None,
                ma21=float(row["ma21"]) if pd.notna(row.get("ma21")) else None,
            )
            history.append(point)

        prediction_result, metrics = predictor.predict(ticker, model, range.value)

        user_id = get_user_id(x_user_id)
        history_service.add_search_history(user_id, ticker)

        prediction_record = PredictionRecordSchema(
            ticker=ticker,
            model=model.value,
            predicted_price=prediction_result.predicted_price,
            confidence=prediction_result.confidence,
        )
        prediction_service.save_prediction(prediction_record)

        return StockResponse(
            ticker=ticker,
            profile=profile,
            history=history,
            prediction=prediction_result,
            metrics=metrics,
            confidence=prediction_result.confidence,
        )
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
