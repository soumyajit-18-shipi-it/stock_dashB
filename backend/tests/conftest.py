import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture
def sample_ticker():
    return "AAPL"


@pytest.fixture
def sample_invalid_ticker():
    return "INVALID_TICKER_XYZ123"
