from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


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
    ma7: Optional[float] = None
    ma21: Optional[float] = None


class CompanyProfile(BaseModel):
    ticker: str
    name: Optional[str] = None
    sector: Optional[str] = None
    industry: Optional[str] = None
    market_cap: Optional[float] = None
    current_price: Optional[float] = None
    previous_close: Optional[float] = None
    currency: Optional[str] = None
    exchange: Optional[str] = None
    country: Optional[str] = None
    week_52_high: Optional[float] = None
    week_52_low: Optional[float] = None


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
    history: List[StockPricePoint]
    prediction: PredictionResult
    metrics: ModelMetrics
    confidence: float = Field(ge=0, le=1)


class WatchlistItem(BaseModel):
    id: Optional[str] = None
    ticker: str
    name: Optional[str] = None
    created_at: Optional[datetime] = None


class WatchlistCreate(BaseModel):
    ticker: str
    name: Optional[str] = None


class SearchHistoryItem(BaseModel):
    id: Optional[str] = None
    ticker: str
    searched_at: Optional[datetime] = None


class PredictionRecord(BaseModel):
    id: Optional[str] = None
    ticker: str
    model: str
    predicted_price: float
    actual_price: Optional[float] = None
    confidence: float
    created_at: Optional[datetime] = None


class HealthResponse(BaseModel):
    status: str
    version: str = "1.0.0"
