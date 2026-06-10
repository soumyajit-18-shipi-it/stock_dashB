import pytest
import pandas as pd
import numpy as np
from features.technical_indicators import TechnicalIndicators


class TestTechnicalIndicators:
    def setup_method(self):
        self.df = pd.DataFrame({
            "Close": [100, 102, 101, 103, 105, 104, 106, 108, 107, 109, 111, 110, 112, 114, 113, 115, 117, 116, 118, 120],
            "Volume": [1000, 1100, 1050, 1200, 1150, 1300, 1250, 1400, 1350, 1500, 1450, 1600, 1550, 1700, 1650, 1800, 1750, 1900, 1850, 2000]
        })

    def test_moving_average_window_7(self):
        ma = TechnicalIndicators.add_moving_average(self.df, "Close", 7)
        assert len(ma) == len(self.df)
        assert pd.isna(ma.iloc[0])
        assert pd.isna(ma.iloc[6])
        assert not pd.isna(ma.iloc[7])

    def test_moving_average_window_21(self):
        ma = TechnicalIndicators.add_moving_average(self.df, "Close", 21)
        assert len(ma) == len(self.df)
        assert all(pd.isna(ma.iloc[:20]))
        assert not pd.isna(ma.iloc[20])

    def test_add_ma7(self):
        df_with_ma7 = TechnicalIndicators.add_ma7(self.df)
        assert "ma7" in df_with_ma7.columns
        assert len(df_with_ma7) == len(self.df)

    def test_add_ma21(self):
        df_with_ma21 = TechnicalIndicators.add_ma21(self.df)
        assert "ma21" in df_with_ma21.columns
        assert len(df_with_ma21) == len(self.df)

    def test_add_all_indicators(self):
        df_all = TechnicalIndicators.add_all_indicators(self.df)
        assert "ma7" in df_all.columns
        assert "ma21" in df_all.columns

    def test_calculate_ema(self):
        ema = TechnicalIndicators.calculate_ema(self.df["Close"], 10)
        assert len(ema) == len(self.df)
        assert not pd.isna(ema.iloc[0])

    def test_calculate_rsi(self):
        rsi = TechnicalIndicators.calculate_rsi(self.df["Close"], 14)
        assert len(rsi) == len(self.df)
        assert all(0 <= x <= 100 for x in rsi.dropna())
