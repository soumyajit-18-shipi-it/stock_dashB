from collections.abc import Generator
from unittest.mock import MagicMock, patch
import pytest
from services.history_service import HistoryService
from services.watchlist_service import WatchlistService
from services.prediction_service import PredictionService
from schemas import PredictionRecord


@pytest.fixture
def mock_supabase_client() -> Generator[MagicMock, None, None]:
    with (
        patch("services.history_service.get_supabase_client") as mock_get_history,
        patch("services.watchlist_service.get_supabase_client") as mock_get_watchlist,
        patch("services.prediction_service.get_supabase_client") as mock_get_prediction,
    ):
        client = MagicMock()
        mock_get_history.return_value = client
        mock_get_watchlist.return_value = client
        mock_get_prediction.return_value = client
        yield client


def test_history_service(mock_supabase_client: MagicMock) -> None:
    # Mock return values for HistoryService
    mock_execute = MagicMock()
    mock_execute.data = [
        {
            "user_id": "test_user",
            "ticker": "AAPL",
            "searched_at": "2026-06-21T12:00:00Z",
            "id": "1",
        }
    ]

    mock_supabase_client.table.return_value.select.return_value.eq.return_value.order.return_value.limit.return_value.execute.return_value = mock_execute
    mock_supabase_client.table.return_value.insert.return_value.execute.return_value = (
        mock_execute
    )
    mock_supabase_client.table.return_value.delete.return_value.eq.return_value.execute.return_value = mock_execute

    svc = HistoryService()

    # test get_search_history
    history = svc.get_search_history("test_user")
    assert len(history) == 1
    assert history[0].ticker == "AAPL"

    # test add_search_history
    added = svc.add_search_history("test_user", "AAPL")
    assert added.ticker == "AAPL"

    # test clear_search_history
    cleared = svc.clear_search_history("test_user")
    assert cleared is True


def test_watchlist_service(mock_supabase_client: MagicMock) -> None:
    mock_execute = MagicMock()
    mock_execute.data = [{"user_id": "test_user", "ticker": "AAPL"}]

    query = mock_supabase_client.table.return_value
    query.select.return_value = query
    query.eq.return_value = query
    query.order.return_value = query
    query.limit.return_value = query
    query.insert.return_value = query
    query.delete.return_value = query
    query.execute.return_value = mock_execute

    svc = WatchlistService()

    # test get_watchlist
    wl = svc.get_watchlist("test_user")
    assert len(wl) == 1
    assert wl[0]["ticker"] == "AAPL"

    # test add_to_watchlist
    added = svc.add_to_watchlist("test_user", "AAPL")
    assert added["ticker"] == "AAPL"

    # test remove_from_watchlist
    removed = svc.remove_from_watchlist("test_user", "AAPL")
    assert removed is True


def test_prediction_service(mock_supabase_client: MagicMock) -> None:
    mock_execute = MagicMock()
    mock_execute.data = [
        {
            "id": "1",
            "user_id": "test_user",
            "ticker": "AAPL",
            "model": "linear",
            "prediction_date": "2026-06-22",
            "predicted_price": 150.0,
            "created_at": "2026-06-21T12:00:00Z",
        }
    ]

    mock_supabase_client.table.return_value.select.return_value.eq.return_value.order.return_value.execute.return_value = mock_execute
    mock_supabase_client.table.return_value.insert.return_value.execute.return_value = (
        mock_execute
    )

    svc = PredictionService()

    # test get_predictions
    preds = svc.get_predictions("test_user")
    assert len(preds) == 1
    assert preds[0]["ticker"] == "AAPL"

    # test save_prediction
    record = PredictionRecord(
        ticker="AAPL",
        model="linear",
        predicted_price=150.0,
        confidence=0.8,
    )
    saved = svc.save_prediction(record)
    assert saved["ticker"] == "AAPL"
