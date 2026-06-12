import pandas as pd


class TechnicalIndicators:
    @staticmethod
    def add_moving_average(
        df: pd.DataFrame, column: str = "Close", window: int = 7
    ) -> pd.Series:
        return df[column].rolling(window=window).mean()

    @staticmethod
    def add_ma7(df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        df["ma7"] = TechnicalIndicators.add_moving_average(df, "Close", 7)
        return df

    @staticmethod
    def add_ma21(df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        df["ma21"] = TechnicalIndicators.add_moving_average(df, "Close", 21)
        return df

    @staticmethod
    def add_all_indicators(df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        df["ma7"] = TechnicalIndicators.add_moving_average(df, "Close", 7)
        df["ma21"] = TechnicalIndicators.add_moving_average(df, "Close", 21)
        return df

    @staticmethod
    def calculate_ema(series: pd.Series, span: int) -> pd.Series:
        return series.ewm(span=span, adjust=False).mean()

    @staticmethod
    def calculate_rsi(series: pd.Series, window: int = 14) -> pd.Series:
        delta = series.diff()
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        avg_gain = gain.rolling(window=window).mean()
        avg_loss = loss.rolling(window=window).mean()
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
