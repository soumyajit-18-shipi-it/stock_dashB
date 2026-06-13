from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class DateRangeEnum(str, Enum):
    ONE_MONTH = "1m"
    SIX_MONTHS = "6m"
    ONE_YEAR = "1y"
    FIVE_YEARS = "5y"


class ModelEnum(str, Enum):
    LINEAR = "linear"
    RANDOM_FOREST = "rf"


class TrendDirection(str, Enum):
    INCREASE = "increase"
    DECREASE = "decrease"


class StockPricePoint(BaseModel):
    date: str
    open: float
    high: float
    low: float
    close: float
    volume: int
    ma7: float | None = None
    ma21: float | None = None


class CompanyProfile(BaseModel):
    ticker: str
    name: str | None = None
    sector: str | None = None
    industry: str | None = None
    market_cap: float | None = None
    current_price: float | None = None
    previous_close: float | None = None
    currency: str | None = None
    exchange: str | None = None
    country: str | None = None
    week_52_high: float | None = None
    week_52_low: float | None = None


class PredictionResult(BaseModel):
    predicted_price: float
    trend: TrendDirection
    confidence: float
    model_used: str


class ModelMetrics(BaseModel):
    rmse: float
    mae: float
    r2: float


class StockResponse(BaseModel):
    ticker: str
    profile: CompanyProfile
    history: list[StockPricePoint]
    prediction: PredictionResult
    metrics: ModelMetrics
    confidence: float = Field(ge=0, le=1)


class WatchlistItem(BaseModel):
    id: str | None = None
    ticker: str
    name: str | None = None
    created_at: datetime | None = None


class WatchlistCreate(BaseModel):
    ticker: str
    name: str | None = None


class SearchHistoryItem(BaseModel):
    id: str | None = None
    ticker: str
    searched_at: datetime | None = None


class PredictionRecord(BaseModel):
    id: str | None = None
    ticker: str
    model: str
    predicted_price: float
    actual_price: float | None = None
    confidence: float
    created_at: datetime | None = None


class HealthResponse(BaseModel):
    status: str
    version: str = "1.0.0"
