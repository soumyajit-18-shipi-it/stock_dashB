from fastapi import APIRouter, HTTPException, Query
from core.yfinance_service import YFinanceService
from core.data_processor import DataProcessor
from core.models import StockResponse, PredictionOutcome

from ml.features import FeatureEngineer
from ml.models import LinearRegressionModel, RandomForestModel

router = APIRouter()

@router.get("/stock/{ticker}", response_model=StockResponse)
async def get_stock_data(
    ticker: str,
    range: str = Query("1y", regex="^(1m|6m|1y|5y)$"),
    model: str = Query("linear", regex="^(linear|rf)$")
):
    try:
        # Fetch data
        df, info = YFinanceService.fetch_data(ticker, period=range)
        
        # Process data (MAs)
        df_processed = DataProcessor.calculate_moving_averages(df)
        
        # ML Prediction
        train_df, predict_row = FeatureEngineer.prepare_features(df_processed)
        
        if len(train_df) < 10:
            raise ValueError("Insufficient data for ML prediction (need at least 21 days for MAs and training)")

        X_train, y_train = FeatureEngineer.get_feature_matrices(train_df)
        X_predict = predict_row[['Close', 'Volume', 'MA7', 'MA21']].values
        
        ml_model = LinearRegressionModel() if model == "linear" else RandomForestModel()
        predicted_price = ml_model.train_and_predict(X_train, y_train, X_predict)
        
        # Convert to records
        history = DataProcessor.dataframe_to_records(df_processed)
        
        # Get profile
        profile = YFinanceService.get_company_profile(info)
        
        last_close = float(df['Close'].iloc[-1])
        
        prediction = PredictionOutcome(
            model="Linear Regression" if model == "linear" else "Random Forest",
            predicted_price=round(predicted_price, 2),
            trend="increase" if predicted_price >= last_close else "decrease",
            current_price=last_close
        )
        
        return StockResponse(
            ticker=ticker.upper(),
            profile=profile,
            history=history,
            prediction=prediction
        )
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")
