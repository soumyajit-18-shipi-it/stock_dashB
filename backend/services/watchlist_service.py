from typing import List, Optional
from datetime import datetime
from ..database.supabase_client import get_supabase_client
from ..schemas import WatchlistItem, WatchlistCreate


class WatchlistService:
    def __init__(self):
        self.client = get_supabase_client()

    def get_watchlist(self, user_id: str) -> List[WatchlistItem]:
        response = self.client.table("watchlists").select("*").eq("user_id", user_id).order("created_at", desc=True).execute()
        return [WatchlistItem(**item) for item in response.data]

    def add_to_watchlist(self, user_id: str, item: WatchlistCreate) -> WatchlistItem:
        data = {
            "user_id": user_id,
            "ticker": item.ticker,
            "name": item.name,
        }
        response = self.client.table("watchlists").insert(data).execute()
        return WatchlistItem(**response.data[0])

    def remove_from_watchlist(self, user_id: str, watchlist_id: str) -> bool:
        response = self.client.table("watchlists").delete().eq("id", watchlist_id).eq("user_id", user_id).execute()
        return len(response.data) > 0

    def get_watchlist_by_ticker(self, user_id: str, ticker: str) -> Optional[WatchlistItem]:
        response = self.client.table("watchlists").select("*").eq("user_id", user_id).eq("ticker", ticker).execute()
        if response.data:
            return WatchlistItem(**response.data[0])
        return None
