from database.supabase_client import get_supabase_client
from schemas import PredictionRecord


class PredictionService:
    def __init__(self):
        self.client = get_supabase_client()

    def get_predictions(
        self, ticker: str | None = None, limit: int = 100
    ) -> list[PredictionRecord]:
        query = self.client.table("predictions").select("*")
        if ticker:
            query = query.eq("ticker", ticker)
        response = query.order("created_at", desc=True).limit(limit).execute()
        return [PredictionRecord(**item) for item in response.data]

    def save_prediction(self, prediction: PredictionRecord) -> PredictionRecord:
        data = {
            "ticker": prediction.ticker,
            "model": prediction.model,
            "predicted_price": prediction.predicted_price,
            "actual_price": prediction.actual_price,
            "confidence": prediction.confidence,
        }
        response = self.client.table("predictions").insert(data).execute()
        return PredictionRecord(**response.data[0])

    def update_actual_price(self, prediction_id: str, actual_price: float) -> bool:
        response = (
            self.client.table("predictions")
            .update({"actual_price": actual_price})
            .eq("id", prediction_id)
            .execute()
        )
        return len(response.data) > 0
