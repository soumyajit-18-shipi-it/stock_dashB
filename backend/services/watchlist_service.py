import logging
from typing import Any

from database.supabase_client import get_supabase_client


class WatchlistService:
    def __init__(self) -> None:
        self.client = get_supabase_client()
        self.logger = logging.getLogger("stock_dashboard")

    def get_watchlist(self, user_id: str | None) -> list[dict[str, Any]]:
        response = (
            self.client.table("watchlists")
            .select("*")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .execute()
        )
        return [self._normalize_item(item) for item in response.data]

    def add_to_watchlist(
        self, user_id: str | None, ticker: str, company_name: str | None = None
    ) -> dict[str, Any]:
        symbol = ticker.strip().upper()
        existing = (
            self.client.table("watchlists")
            .select("*")
            .eq("user_id", user_id)
            .eq("ticker", symbol)
            .limit(1)
            .execute()
        )
        if existing.data:
            return self._normalize_item(existing.data[0])

        data = {
            "user_id": user_id,
            "ticker": symbol,
            "company_name": company_name,
            "name": company_name,
        }
        try:
            response = self.client.table("watchlists").insert(data).execute()
        except Exception:  # pylint: disable=broad-exception-caught
            response = (
                self.client.table("watchlists")
                .insert({"user_id": user_id, "ticker": symbol, "name": company_name})
                .execute()
            )
        return self._normalize_item(response.data[0])

    def remove_from_watchlist(self, user_id: str | None, identifier: str) -> bool:
        response = (
            self.client.table("watchlists")
            .delete()
            .eq("user_id", user_id)
            .eq("id", identifier)
            .execute()
        )
        if response.data:
            return True

        response = (
            self.client.table("watchlists")
            .delete()
            .eq("user_id", user_id)
            .eq("ticker", identifier.strip().upper())
            .execute()
        )
        return len(response.data) > 0

    def _normalize_item(self, item: dict[str, Any]) -> dict[str, Any]:
        data = dict(item)
        company_name = data.get("company_name") or data.get("name")
        data["company_name"] = company_name
        data["name"] = company_name
        return data
