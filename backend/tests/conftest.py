import os
import sys
from collections.abc import Generator
from typing import Any

import pytest
from fastapi.testclient import TestClient

# Add project root and backend to sys.path
root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
backend_dir = os.path.join(root_dir, "backend")

if root_dir not in sys.path:
    sys.path.insert(0, root_dir)
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

os.environ["SUPABASE_URL"] = "https://your-project-ref.supabase.co"
os.environ["SUPABASE_SERVICE_ROLE_KEY"] = "your_supabase_service_role_key"
os.environ["ADMIN_EMAILS"] = "routsoumyajit18@gmail.com,soumyajitrout24@gmail.com"

from main import app  # noqa: E402
from database.supabase_client import MockTableQuery, get_supabase_client  # noqa: E402


@pytest.fixture(autouse=True)
def reset_mock_supabase() -> Generator[None, None, None]:
    for table_name in MockTableQuery._store:
        MockTableQuery._store[table_name] = []
    yield


@pytest.fixture
def sample_ticker() -> str:
    return "AAPL"


@pytest.fixture
def sample_invalid_ticker() -> str:
    return "INVALID_TICKER_XYZ123"


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    with TestClient(app) as c:
        yield c


@pytest.fixture
def mock_db() -> Generator[Any, None, None]:
    yield get_supabase_client()
