import logging
from typing import Any

from database.supabase_client import get_supabase_client


class WatchlistService:
    def __init__(self) -> None:
        self.client = get_supabase_client()
        self.logger = logging.getLogger("stock_dashboard")

    def get_watchlist(self, user_id: str | None) -> list[dict[str, Any]]:
        response = (
            self.client.table("watchlists").select("*").eq("user_id", user_id).execute()
        )
        return list(response.data)

    def add_to_watchlist(self, user_id: str | None, ticker: str) -> dict[str, Any]:
        data = {"user_id": user_id, "ticker": ticker}
        response = self.client.table("watchlists").insert(data).execute()
        return dict(response.data[0])

    def remove_from_watchlist(self, user_id: str | None, ticker: str) -> bool:
        response = (
            self.client.table("watchlists")
            .delete()
            .eq("user_id", user_id)
            .eq("ticker", ticker)
            .execute()
        )
        return len(response.data) > 0
