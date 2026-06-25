import re
import logging

logger = logging.getLogger("stock_dashboard")

_SUFFIX_MAP = {
    ".NS": "NSE",
    ".BO": "BSE",
}


def to_finnhub_symbol(ticker: str) -> str:
    """Convert a Yahoo Finance ticker to a Finnhub-compatible symbol.

    Yahoo Finance uses suffixes like .NS for NSE and .BO for BSE.
    Finnhub requires the exchange prefix format: NSE:RELIANCE, BSE:TCS.

    For non-Indian tickers (no suffix), the ticker is returned as-is,
    which is compatible with both Yahoo Finance and Finnhub.
    """
    original = ticker
    cleaned = ticker.strip().upper()

    for suffix, exchange in _SUFFIX_MAP.items():
        if cleaned.endswith(suffix):
            base = cleaned[: -len(suffix)]
            if base:
                result = f"{exchange}:{base}"
                logger.debug(
                    "Symbol conversion: %s -> %s (suffix=%s, exchange=%s)",
                    original, result, suffix, exchange,
                )
                return result

    logger.debug("Symbol conversion: %s -> %s (no suffix, passed through)", original, cleaned)
    return cleaned


def is_indian_ticker(ticker: str) -> bool:
    """Check if a ticker is an Indian stock (has .NS or .BO suffix)."""
    cleaned = ticker.strip().upper()
    return cleaned.endswith(".NS") or cleaned.endswith(".BO")
