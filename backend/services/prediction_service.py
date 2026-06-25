from typing import Any

from database.supabase_client import get_supabase_client
from schemas import PredictionRecord


class PredictionService:
    def __init__(self) -> None:
        self.client = get_supabase_client()

    def get_predictions(self, user_id: str | None) -> list[dict[str, Any]]:
        response = (
            self.client.table("predictions")
            .select("*")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .execute()
        )
        return list(response.data)

    def save_prediction(
        self, record: PredictionRecord, user_id: str | None = None
    ) -> dict[str, Any]:
        data = record.dict()
        if user_id:
            data["user_id"] = user_id
        response = self.client.table("predictions").insert(data).execute()
        return dict(response.data[0])
