from pydantic import BaseModel
from typing import List, Optional, Literal

class StockProfile(BaseModel):
    name: str
    sector: str
    market_cap: int
    high_52w: float
    low_52w: float

class StockHistoryItem(BaseModel):
    date: str
    open: float
    high: float
    low: float
    close: float
    volume: int
    ma7: Optional[float] = None
    ma21: Optional[float] = None

class StockPrediction(BaseModel):
    model: str
    predicted_price: float
    trend: Literal["increase", "decrease"]
    current_price: float

class StockResponse(BaseModel):
    ticker: str
    profile: StockProfile
    history: List[StockHistoryItem]
    prediction: StockPrediction
