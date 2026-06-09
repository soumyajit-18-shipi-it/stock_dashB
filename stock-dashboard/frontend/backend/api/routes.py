from fastapi import APIRouter, HTTPException, Query
from backend.schemas.stock_schema import StockResponse, StockProfile, StockHistoryItem, StockPrediction
from backend.data.provider import fetch_stock_raw_data, get_company_profile
from backend.features.engineering import apply_technical_indicators, prepare_ml_features
from backend.ml.model import StockPredictor
import pandas as pd

router = APIRouter(prefix="/api/v1")

@router.get("/health")
async def health_check():
    return {"status": "ok"}

@router.get("/stock/{ticker}", response_model=StockResponse)
async def get_stock_data(
    ticker: str,
    range: str = Query("1y", regex="^(1m|6m|1y|5y)$"),
    model: str = Query("linear", regex="^(linear|rf)$")
):
    try:
        # 1. Fetch data
        df, info = fetch_stock_raw_data(ticker, range)
        
        if df.empty:
            raise HTTPException(status_code=404, detail=f"No data found for ticker {ticker}")
            
        # 2. Extract Profile
        profile_data = get_company_profile(info)
        profile = StockProfile(**profile_data)
        
        # 3. Apply Indicators
        df_with_indicators = apply_technical_indicators(df)
        
        # 4. ML Prediction
        df_ml = prepare_ml_features(df_with_indicators)
        predictor = StockPredictor(model_type=model)
        predicted_price, trend, current_price = predictor.train_and_predict(df_ml)
        
        prediction = StockPrediction(
            model="Linear Regression" if model == "linear" else "Random Forest",
            predicted_price=predicted_price,
            trend=trend,
            current_price=current_price
        )
        
        # 5. Format History
        history = []
        for index, row in df_with_indicators.iterrows():
            history.append(StockHistoryItem(
                date=index.strftime('%Y-%m-%d'),
                open=float(row['Open']),
                high=float(row['High']),
                low=float(row['Low']),
                close=float(row['Close']),
                volume=int(row['Volume']),
                ma7=float(row['ma7']) if not pd.isna(row['ma7']) else None,
                ma21=float(row['ma21']) if not pd.isna(row['ma21']) else None
            ))
            
        return StockResponse(
            ticker=ticker,
            profile=profile,
            history=history,
            prediction=prediction
        )
        
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))
