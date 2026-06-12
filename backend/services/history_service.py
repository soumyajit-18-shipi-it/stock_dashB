from database.supabase_client import get_supabase_client
from schemas import SearchHistoryItem


class HistoryService:
    def __init__(self):
        self.client = get_supabase_client()

    def get_search_history(
        self, user_id: str | None, limit: int = 50
    ) -> list[SearchHistoryItem]:
        response = (
            self.client.table("search_history")
            .select("*")
            .eq("user_id", user_id)
            .order("searched_at", desc=True)
            .limit(limit)
            .execute()
        )
        return [SearchHistoryItem(**item) for item in response.data]

    def add_search_history(self, user_id: str | None, ticker: str) -> SearchHistoryItem:
        data = {
            "user_id": user_id,
            "ticker": ticker,
        }
        response = self.client.table("search_history").insert(data).execute()
        return SearchHistoryItem(**response.data[0])

    def clear_search_history(self, user_id: str | None) -> bool:
        response = (
            self.client.table("search_history")
            .delete()
            .eq("user_id", user_id)
            .execute()
        )
        return len(response.data) > 0
