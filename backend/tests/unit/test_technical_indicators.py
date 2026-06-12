import pandas as pd
import pytest
from features.technical_indicators import TechnicalIndicators


@pytest.fixture
def sample_data() -> pd.DataFrame:
    data = {
        "Open": [100, 101, 102, 103, 104, 105, 106, 107, 108, 109],
        "High": [105, 106, 107, 108, 109, 110, 111, 112, 113, 114],
        "Low": [95, 96, 97, 98, 99, 100, 101, 102, 103, 104],
        "Close": [102, 103, 101, 104, 105, 107, 106, 108, 110, 109],
        "Volume": [1000] * 10,
    }
    return pd.DataFrame(data)


class TestTechnicalIndicators:
    def test_add_moving_average(self, sample_data: pd.DataFrame) -> None:
        ti = TechnicalIndicators()
        ma = ti.add_moving_average(sample_data, window=3)
        assert len(ma) == len(sample_data)
        assert not ma.isna().all()

    def test_add_ma7(self, sample_data: pd.DataFrame) -> None:
        ti = TechnicalIndicators()
        df = ti.add_ma7(sample_data)
        assert "ma7" in df.columns

    def test_add_ma21(self, sample_data: pd.DataFrame) -> None:
        ti = TechnicalIndicators()
        df = ti.add_ma21(sample_data)
        assert "ma21" in df.columns

    def test_add_all_indicators(self, sample_data: pd.DataFrame) -> None:
        ti = TechnicalIndicators()
        df = ti.add_all_indicators(sample_data)
        assert "ma7" in df.columns
        assert "ma21" in df.columns

    def test_calculate_ema(self, sample_data: pd.DataFrame) -> None:
        ti = TechnicalIndicators()
        ema = ti.calculate_ema(sample_data["Close"], span=5)
        assert len(ema) == len(sample_data)

    def test_calculate_rsi(self, sample_data: pd.DataFrame) -> None:
        ti = TechnicalIndicators()
        rsi = ti.calculate_rsi(sample_data["Close"], window=5)
        assert len(rsi) == len(sample_data)
