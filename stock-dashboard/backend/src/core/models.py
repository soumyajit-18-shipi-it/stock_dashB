from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class StockRecord(BaseModel):
    date: str
    open: float
    high: float
    low: float
    close: float
    volume: int
    ma7: Optional[float] = None
    ma21: Optional[float] = None

class CompanyProfile(BaseModel):
    name: str
    sector: str
    market_cap: float
    high_52w: float
    low_52w: float

class PredictionOutcome(BaseModel):
    model: str
    predicted_price: float
    trend: str
    current_price: float

class StockResponse(BaseModel):
    ticker: str
    profile: CompanyProfile
    history: List[StockRecord]
    prediction: PredictionOutcome
