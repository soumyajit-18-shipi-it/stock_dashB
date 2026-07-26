"""Canonical vectorized technical-indicator calculations.

All backend consumers use this module so charting, recommendation scoring, and
model feature engineering cannot drift into different formula implementations.
The formulas follow the conventional Wilder/EMA definitions used by mature
technical-analysis libraries while retaining the legacy ``ma7`` and ``ma21``
columns required by persisted prediction models.
"""

from __future__ import annotations

import numpy as np
import pandas as pd


class TechnicalIndicators:
    """Add price, trend, momentum, volatility, and volume indicators."""

    @staticmethod
    def add_moving_average(
        df: pd.DataFrame, column: str = "Close", window: int = 7
    ) -> pd.Series:
        return df[column].rolling(window=window, min_periods=window).mean()

    @staticmethod
    def add_ma7(df: pd.DataFrame) -> pd.DataFrame:
        result = df.copy()
        result["ma7"] = TechnicalIndicators.add_moving_average(result, "Close", 7)
        return result

    @staticmethod
    def add_ma21(df: pd.DataFrame) -> pd.DataFrame:
        result = df.copy()
        result["ma21"] = TechnicalIndicators.add_moving_average(result, "Close", 21)
        return result

    @staticmethod
    def calculate_ema(series: pd.Series, span: int) -> pd.Series:
        return series.ewm(span=span, adjust=False, min_periods=span).mean()

    @staticmethod
    def calculate_rsi(series: pd.Series, window: int = 14) -> pd.Series:
        """Return Wilder's relative strength index."""
        delta = series.diff()
        gain = delta.clip(lower=0.0)
        loss = -delta.clip(upper=0.0)
        alpha = 1.0 / window
        avg_gain = gain.ewm(
            alpha=alpha, adjust=False, min_periods=window
        ).mean()
        avg_loss = loss.ewm(
            alpha=alpha, adjust=False, min_periods=window
        ).mean()
        relative_strength = avg_gain / avg_loss.replace(0.0, np.nan)
        rsi = 100.0 - (100.0 / (1.0 + relative_strength))
        return rsi.where(avg_loss.ne(0.0), 100.0)

    @staticmethod
    def _true_range(df: pd.DataFrame) -> pd.Series:
        previous_close = df["Close"].shift(1)
        ranges = pd.concat(
            [
                df["High"] - df["Low"],
                (df["High"] - previous_close).abs(),
                (df["Low"] - previous_close).abs(),
            ],
            axis=1,
        )
        return ranges.max(axis=1)

    @staticmethod
    def calculate_atr(df: pd.DataFrame, window: int = 14) -> pd.Series:
        true_range = TechnicalIndicators._true_range(df)
        return true_range.ewm(
            alpha=1.0 / window, adjust=False, min_periods=window
        ).mean()

    @staticmethod
    def calculate_adx(df: pd.DataFrame, window: int = 14) -> pd.Series:
        """Return Wilder's average directional index."""
        up_move = df["High"].diff()
        down_move = -df["Low"].diff()
        positive_dm = pd.Series(
            np.where((up_move > down_move) & (up_move > 0), up_move, 0.0),
            index=df.index,
        )
        negative_dm = pd.Series(
            np.where((down_move > up_move) & (down_move > 0), down_move, 0.0),
            index=df.index,
        )
        atr = TechnicalIndicators.calculate_atr(df, window)
        positive_di = (
            100.0
            * positive_dm.ewm(
                alpha=1.0 / window, adjust=False, min_periods=window
            ).mean()
            / atr.replace(0.0, np.nan)
        )
        negative_di = (
            100.0
            * negative_dm.ewm(
                alpha=1.0 / window, adjust=False, min_periods=window
            ).mean()
            / atr.replace(0.0, np.nan)
        )
        directional_index = (
            100.0
            * (positive_di - negative_di).abs()
            / (positive_di + negative_di).replace(0.0, np.nan)
        )
        return directional_index.ewm(
            alpha=1.0 / window, adjust=False, min_periods=window
        ).mean()

    @staticmethod
    def calculate_obv(df: pd.DataFrame) -> pd.Series:
        direction = np.sign(df["Close"].diff()).fillna(0.0)
        return (direction * df["Volume"].fillna(0.0)).cumsum()

    @staticmethod
    def calculate_vwap(df: pd.DataFrame) -> pd.Series:
        typical_price = (df["High"] + df["Low"] + df["Close"]) / 3.0
        volume = df["Volume"].fillna(0.0)
        return (typical_price * volume).cumsum() / volume.cumsum().replace(0.0, np.nan)

    @classmethod
    def add_all_indicators(cls, df: pd.DataFrame) -> pd.DataFrame:
        """Return a copy containing the complete shared indicator set."""
        result = df.copy()
        close = result["Close"].astype(float)

        # Legacy model/chart contract.
        result["ma7"] = cls.add_moving_average(result, "Close", 7)
        result["ma21"] = cls.add_moving_average(result, "Close", 21)

        # Trend and moving averages.
        result["sma_20"] = close.rolling(20, min_periods=20).mean()
        result["sma_50"] = close.rolling(50, min_periods=50).mean()
        result["ema_12"] = cls.calculate_ema(close, 12)
        result["ema_20"] = cls.calculate_ema(close, 20)
        result["ema_26"] = cls.calculate_ema(close, 26)
        result["ema_50"] = cls.calculate_ema(close, 50)
        result["macd"] = result["ema_12"] - result["ema_26"]
        result["macd_signal"] = result["macd"].ewm(
            span=9, adjust=False, min_periods=9
        ).mean()
        result["macd_histogram"] = result["macd"] - result["macd_signal"]

        # Volatility and oscillator indicators.
        rolling_std = close.rolling(20, min_periods=20).std(ddof=0)
        result["bollinger_middle"] = result["sma_20"]
        result["bollinger_upper"] = result["sma_20"] + 2.0 * rolling_std
        result["bollinger_lower"] = result["sma_20"] - 2.0 * rolling_std
        result["bollinger_percent_b"] = (
            (close - result["bollinger_lower"])
            / (result["bollinger_upper"] - result["bollinger_lower"]).replace(
                0.0, np.nan
            )
        )
        result["atr_14"] = cls.calculate_atr(result, 14)
        result["adx_14"] = cls.calculate_adx(result, 14)
        result["rsi_14"] = cls.calculate_rsi(close, 14)
        rsi_min = result["rsi_14"].rolling(14, min_periods=14).min()
        rsi_max = result["rsi_14"].rolling(14, min_periods=14).max()
        result["stoch_rsi"] = (
            (result["rsi_14"] - rsi_min)
            / (rsi_max - rsi_min).replace(0.0, np.nan)
        )
        result["stoch_rsi_k"] = (
            result["stoch_rsi"].rolling(3, min_periods=3).mean() * 100.0
        )
        result["stoch_rsi_d"] = (
            result["stoch_rsi_k"].rolling(3, min_periods=3).mean()
        )

        # Volume indicators.
        result["obv"] = cls.calculate_obv(result)
        result["vwap"] = cls.calculate_vwap(result)
        result["obv_slope_20"] = (
            result["obv"].diff(20)
            / result["Volume"].rolling(20, min_periods=20).sum().replace(0.0, np.nan)
        )
        volume_mean = result["Volume"].rolling(20, min_periods=20).mean()
        volume_std = result["Volume"].rolling(20, min_periods=20).std(ddof=0)
        result["volume_zscore"] = (
            (result["Volume"] - volume_mean) / volume_std.replace(0.0, np.nan)
        )
        result["volume_confirmation"] = (
            np.sign(close.pct_change(5)) * result["volume_zscore"]
        )

        # Ichimoku uses unshifted spans for current-state comparisons. The
        # conventional displaced spans are also exposed for chart consumers.
        conversion = (
            result["High"].rolling(9, min_periods=9).max()
            + result["Low"].rolling(9, min_periods=9).min()
        ) / 2.0
        base = (
            result["High"].rolling(26, min_periods=26).max()
            + result["Low"].rolling(26, min_periods=26).min()
        ) / 2.0
        span_a_current = (conversion + base) / 2.0
        span_b_current = (
            result["High"].rolling(52, min_periods=52).max()
            + result["Low"].rolling(52, min_periods=52).min()
        ) / 2.0
        result["ichimoku_conversion"] = conversion
        result["ichimoku_base"] = base
        result["ichimoku_span_a_current"] = span_a_current
        result["ichimoku_span_b_current"] = span_b_current
        result["ichimoku_span_a"] = span_a_current.shift(26)
        result["ichimoku_span_b"] = span_b_current.shift(26)
        result["ichimoku_lagging"] = close.shift(-26)

        # Price structure and normalized composite primitives.
        result["support_20"] = result["Low"].rolling(20, min_periods=20).min()
        result["resistance_20"] = result["High"].rolling(20, min_periods=20).max()
        atr_safe = result["atr_14"].replace(0.0, np.nan)
        result["trend_strength"] = np.tanh(
            (result["ema_20"] - result["ema_50"]) / atr_safe
        )
        result["momentum_20"] = close.pct_change(20)
        result["distance_to_support_atr"] = (
            close - result["support_20"]
        ) / atr_safe
        result["distance_to_resistance_atr"] = (
            result["resistance_20"] - close
        ) / atr_safe
        return result.replace([np.inf, -np.inf], np.nan)
