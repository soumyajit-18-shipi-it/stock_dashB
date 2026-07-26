"""Supabase persistence for named portfolios and analysis snapshots."""

from __future__ import annotations

from typing import Any

from database.supabase_client import get_supabase_client
from portfolio.types import HoldingPosition


class PortfolioPersistenceService:
    def __init__(self) -> None:
        self.client = get_supabase_client()

    def save(
        self,
        user_id: str,
        name: str,
        positions: list[HoldingPosition],
        analysis: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        response = (
            self.client.table("portfolios")
            .insert(
                {
                    "user_id": user_id,
                    "name": name.strip(),
                    "analysis_snapshot": analysis,
                }
            )
            .execute()
        )
        portfolio = dict(response.data[0])
        portfolio_id = portfolio["id"]
        rows = [
            {
                "portfolio_id": portfolio_id,
                "ticker": item.ticker,
                "quantity": item.quantity,
                "average_cost": item.average_cost,
                "target_weight": item.weight,
            }
            for item in positions
        ]
        holdings = (
            self.client.table("portfolio_holdings").insert(rows).execute().data
            if rows
            else []
        )
        portfolio["holdings"] = holdings
        return portfolio

    def list_for_user(self, user_id: str) -> list[dict[str, Any]]:
        response = (
            self.client.table("portfolios")
            .select("*")
            .eq("user_id", user_id)
            .order("updated_at", desc=True)
            .execute()
        )
        return [dict(item) for item in response.data]

    def get(self, user_id: str, portfolio_id: str) -> dict[str, Any] | None:
        response = (
            self.client.table("portfolios")
            .select("*")
            .eq("user_id", user_id)
            .eq("id", portfolio_id)
            .limit(1)
            .execute()
        )
        if not response.data:
            return None
        portfolio = dict(response.data[0])
        holdings = (
            self.client.table("portfolio_holdings")
            .select("*")
            .eq("portfolio_id", portfolio_id)
            .execute()
            .data
        )
        portfolio["holdings"] = holdings
        return portfolio

    def delete(self, user_id: str, portfolio_id: str) -> bool:
        response = (
            self.client.table("portfolios")
            .delete()
            .eq("user_id", user_id)
            .eq("id", portfolio_id)
            .execute()
        )
        return bool(response.data)


portfolio_persistence = PortfolioPersistenceService()
