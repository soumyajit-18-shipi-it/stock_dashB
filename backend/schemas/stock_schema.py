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
    logo: str | None = None
    website: str | None = None


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
    company_name: str | None = None
    created_at: datetime | None = None


class WatchlistCreate(BaseModel):
    ticker: str
    name: str | None = None
    company_name: str | None = None


class SearchHistoryItem(BaseModel):
    id: str | None = None
    query: str | None = None
    ticker: str
    searched_at: datetime | None = None


class SearchHistoryCreate(BaseModel):
    query: str
    ticker: str | None = None


class PredictionRecord(BaseModel):
    id: str | None = None
    user_id: str | None = None
    ticker: str
    model: str
    predicted_price: float
    actual_price: float | None = None
    confidence: float
    created_at: datetime | None = None


class HealthResponse(BaseModel):
    status: str
    version: str = "1.0.0"


class FeedbackCreate(BaseModel):
    category: str
    title: str
    description: str
    page_url: str | None = None
    screenshot_url: str | None = None


class FeedbackResponse(BaseModel):
    id: str
    user_id: str | None = None
    email: str | None = None
    category: str
    title: str
    description: str
    page_url: str | None = None
    screenshot_url: str | None = None
    status: str
    priority: str
    created_at: datetime
    updated_at: datetime
    submitter_name: str | None = None
    submitter_avatar_url: str | None = None
    submitter_provider: str | None = None


class AdminUserSummary(BaseModel):
    id: str
    email: str | None = None
    full_name: str | None = None
    avatar_url: str | None = None
    provider: str | None = None
    first_seen_at: datetime | None = None
    last_seen_at: datetime | None = None
    total_feedback_count: int = 0
    total_watchlist_items: int = 0
    total_searches: int = 0


class AdminUserCountResponse(BaseModel):
    total_users: int
    new_users_today: int
    new_users_this_week: int
    last_updated: datetime


class AdminStatsResponse(BaseModel):
    total_users: int
    new_users_today: int
    new_users_this_week: int
    active_today: int
    total_feedback_issues: int
    open_feedback_issues: int
    latest_signups: list[AdminUserSummary] = Field(default_factory=list)
    recent_feedback: list[FeedbackResponse] = Field(default_factory=list)
    users: list[AdminUserSummary] = Field(default_factory=list)
    last_updated: datetime
