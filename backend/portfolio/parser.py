"""Strict CSV portfolio parser with explicit column aliases."""

from __future__ import annotations

import csv
import io
from dataclasses import dataclass

from portfolio.types import HoldingPosition


@dataclass(frozen=True)
class PortfolioParserConfig:
    max_holdings: int = 30
    ticker_aliases: tuple[str, ...] = ("ticker", "symbol", "stock", "security")
    quantity_aliases: tuple[str, ...] = ("quantity", "qty", "shares", "units")
    cost_aliases: tuple[str, ...] = (
        "average_cost",
        "avg_cost",
        "cost_basis",
        "buy_price",
    )
    weight_aliases: tuple[str, ...] = ("weight", "allocation", "target_weight")


class PortfolioParser:
    def __init__(self, config: PortfolioParserConfig | None = None) -> None:
        self.config = config or PortfolioParserConfig()

    def parse_csv(self, content: str) -> list[HoldingPosition]:
        if not content.strip():
            raise ValueError("Portfolio CSV is empty")
        reader = csv.DictReader(io.StringIO(content.lstrip("\ufeff")))
        if not reader.fieldnames:
            raise ValueError("Portfolio CSV must include a header row")
        normalized = {
            self._normalize(name): name for name in reader.fieldnames if name
        }
        ticker_column = self._find(normalized, self.config.ticker_aliases)
        quantity_column = self._find(normalized, self.config.quantity_aliases)
        cost_column = self._find(normalized, self.config.cost_aliases)
        weight_column = self._find(normalized, self.config.weight_aliases)
        if not ticker_column:
            raise ValueError("CSV requires a ticker or symbol column")
        if not quantity_column and not weight_column:
            raise ValueError("CSV requires quantity/shares or weight/allocation")

        holdings: list[HoldingPosition] = []
        seen: set[str] = set()
        for row_number, row in enumerate(reader, start=2):
            ticker = str(row.get(ticker_column) or "").strip().upper()
            if not ticker:
                continue
            if ticker in seen:
                raise ValueError(f"Duplicate ticker {ticker} on row {row_number}")
            quantity = self._optional_number(
                row.get(quantity_column) if quantity_column else None,
                f"quantity on row {row_number}",
            )
            average_cost = self._optional_number(
                row.get(cost_column) if cost_column else None,
                f"average cost on row {row_number}",
            )
            weight = self._optional_number(
                row.get(weight_column) if weight_column else None,
                f"weight on row {row_number}",
            )
            if weight is not None and weight > 1.0:
                weight /= 100.0
            if quantity is None and weight is None:
                raise ValueError(
                    f"Row {row_number} requires quantity or weight"
                )
            if quantity is not None and quantity <= 0:
                raise ValueError(f"Quantity must be positive on row {row_number}")
            if weight is not None and weight <= 0:
                raise ValueError(f"Weight must be positive on row {row_number}")
            holdings.append(
                HoldingPosition(
                    ticker=ticker,
                    quantity=quantity,
                    average_cost=average_cost,
                    weight=weight,
                )
            )
            seen.add(ticker)
        if not holdings:
            raise ValueError("Portfolio CSV contains no holdings")
        if len(holdings) > self.config.max_holdings:
            raise ValueError(
                f"Portfolio exceeds the {self.config.max_holdings}-holding limit"
            )
        weighted = [item.weight is not None for item in holdings]
        if any(weighted) and not all(weighted):
            raise ValueError(
                "Provide weights for every holding or quantities for every holding"
            )
        return holdings

    @staticmethod
    def _normalize(value: str) -> str:
        return value.strip().lower().replace(" ", "_").replace("-", "_")

    @staticmethod
    def _find(
        normalized: dict[str, str], aliases: tuple[str, ...]
    ) -> str | None:
        return next((normalized[name] for name in aliases if name in normalized), None)

    @staticmethod
    def _optional_number(value: object, label: str) -> float | None:
        if value is None or str(value).strip() == "":
            return None
        cleaned = str(value).strip().replace(",", "").replace("%", "")
        try:
            return float(cleaned)
        except ValueError as exc:
            raise ValueError(f"Invalid {label}: {value}") from exc
