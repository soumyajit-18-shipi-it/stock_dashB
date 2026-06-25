"""Screener.in provider for Indian stock company metadata.

Screener.in provides free, publicly accessible company profiles for
Indian stocks including sector, industry, and market capitalisation.

Rate-limit note: Screener.in does not publish an official API. This
module parses the public HTML pages with lightweight regex. To avoid
abuse, the caller should enforce a minimum interval between requests
and respect 24-hour caching.
"""

import logging
import re
import time
from typing import Any

import requests

logger = logging.getLogger("stock_dashboard")

_REQUEST_TIMEOUT = 15
_MIN_INTERVAL = 1.0  # seconds between requests
_last_request: float = 0.0


def _rate_limit() -> None:
    global _last_request
    elapsed = time.time() - _last_request
    if elapsed < _MIN_INTERVAL:
        time.sleep(_MIN_INTERVAL - elapsed)
    _last_request = time.time()


def _get_screener_symbol(ticker: str) -> str | None:
    """Convert Yahoo ticker suffix to Screener.in symbol.

    Screener.in uses plain NSE symbols (e.g. RELIANCE, TCS).
    Yahoo Finance suffixes (.NS, .BO) must be stripped.
    """
    cleaned = ticker.strip().upper()
    if cleaned.endswith(".NS"):
        return cleaned[:-3]
    if cleaned.endswith(".BO"):
        return cleaned[:-3]
    return None  # Not an Indian ticker


def fetch_company_profile(ticker: str) -> dict[str, Any] | None:
    """Fetch company metadata from Screener.in.

    Returns a dict with keys: sector, industry, marketCap, name, source
    Returns None if the ticker is not Indian or the page cannot be parsed.
    """
    sym = _get_screener_symbol(ticker)
    if not sym:
        return None

    _rate_limit()

    url = f"https://www.screener.in/company/{sym}/consolidated/"
    session = requests.Session()
    session.headers.update({
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/122.0.0.0 Safari/537.36"
        ),
    })

    try:
        response = session.get(url, timeout=_REQUEST_TIMEOUT)
        if response.status_code != 200:
            logger.warning(
                "Screener returned status %d for %s (sym=%s)",
                response.status_code, ticker, sym,
            )
            return None

        html = response.text
        result: dict[str, Any] = {"source": "screener.in"}

        # ---- Sector ----
        m = re.search(r'title="Broad Sector">([^<]+)</a>', html)
        if m:
            result["sector"] = m.group(1).strip()

        # ---- Industry ----
        m = re.search(r'title="Broad Industry">([^<]+)</a>', html)
        if m:
            result["industry"] = m.group(1).strip()

        # ---- Market Cap (₹ X,XX,XXX Cr) ----
        m = re.search(
            r'Market Cap.*?<span class="number">([\d,]+)</span>\s*Cr\.?',
            html, re.DOTALL,
        )
        if m:
            num_str = m.group(1).replace(",", "")
            try:
                # Screener.in values are in Crores (Cr)
                # 1 Cr = 10,000,000
                result["marketCap"] = float(num_str) * 10_000_000
            except ValueError:
                pass

        # ---- Company Name ----
        m = re.search(r'<h1[^>]*>([^<]+)</h1>', html)
        if m:
            result["name"] = m.group(1).strip()

        logger.info(
            "Screener profile for %s (sym=%s): sector=%s industry=%s marketCap=%s name=%s",
            ticker, sym,
            result.get("sector"),
            result.get("industry"),
            result.get("marketCap"),
            result.get("name"),
        )

        # Only return if we got at least one meaningful field
        if result.get("sector") or result.get("industry") or result.get("marketCap"):
            return result

        logger.warning("Screener returned no useful data for %s (sym=%s)", ticker, sym)
        return None

    except requests.exceptions.Timeout:
        logger.warning("Screener request timed out for %s (sym=%s)", ticker, sym)
        return None
    except requests.exceptions.RequestException as exc:
        logger.warning("Screener request failed for %s (sym=%s): %s", ticker, sym, exc)
        return None
    except Exception as exc:
        logger.warning("Screener parse error for %s (sym=%s): %s", ticker, sym, exc)
        return None
