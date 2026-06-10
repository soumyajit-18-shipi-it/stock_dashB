import os
import logging
from datetime import datetime
from typing import Any
from dotenv import load_dotenv

logger = logging.getLogger("stock_dashboard")

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")

_supabase_client: Any = None


class MockTableQuery:
    # A persistent, in-memory store for mocks
    _store: dict = {
        "watchlists": [],
        "search_history": [],
        "predictions": []
    }

    def __init__(self, table_name: str):
        self.table_name = table_name
        self.filters = []
        self._order = None
        self._limit = None
        self._inserted_data = None
        self._deleted = False
        self._update_data = None

    def select(self, *args, **kwargs):
        return self

    def eq(self, field, value):
        self.filters.append((field, value))
        return self

    def order(self, field, desc=False):
        self._order = (field, desc)
        return self

    def limit(self, limit_val):
        self._limit = limit_val
        return self

    def insert(self, data):
        self._inserted_data = data
        return self

    def delete(self):
        self._deleted = True
        return self

    def update(self, data):
        self._update_data = data
        return self

    def execute(self):
        class MockResponse:
            def __init__(self, data):
                self.data = data

        current_time = datetime.utcnow().isoformat() + "Z"

        if self._inserted_data is not None:
            if isinstance(self._inserted_data, list):
                new_items = []
                for item in self._inserted_data:
                    new_item = {
                        "id": f"mock-{self.table_name}-{len(MockTableQuery._store[self.table_name]) + 1}",
                        "created_at": current_time,
                        "searched_at": current_time,
                        **item
                    }
                    MockTableQuery._store[self.table_name].append(new_item)
                    new_items.append(new_item)
                return MockResponse(new_items)
            else:
                new_item = {
                    "id": f"mock-{self.table_name}-{len(MockTableQuery._store[self.table_name]) + 1}",
                    "created_at": current_time,
                    "searched_at": current_time,
                    **self._inserted_data
                }
                MockTableQuery._store[self.table_name].append(new_item)
                return MockResponse([new_item])

        if self._deleted:
            matching = []
            non_matching = []
            for item in MockTableQuery._store.get(self.table_name, []):
                match = True
                for field, val in self.filters:
                    if item.get(field) != val:
                        match = False
                        break
                if match:
                    matching.append(item)
                else:
                    non_matching.append(item)
            MockTableQuery._store[self.table_name] = non_matching
            return MockResponse(matching)

        if self._update_data is not None:
            matching = []
            for item in MockTableQuery._store.get(self.table_name, []):
                match = True
                for field, val in self.filters:
                    if item.get(field) != val:
                        match = False
                        break
                if match:
                    item.update(self._update_data)
                    matching.append(item)
            return MockResponse(matching)

        items = MockTableQuery._store.get(self.table_name, [])
        filtered_items = []
        for item in items:
            match = True
            for field, val in self.filters:
                if item.get(field) != val:
                    match = False
                    break
            if match:
                filtered_items.append(item)

        if self._order:
            field, desc = self._order
            try:
                filtered_items.sort(key=lambda x: x.get(field) or "", reverse=desc)
            except Exception:
                pass

        if self._limit is not None:
            filtered_items = filtered_items[:self._limit]

        return MockResponse(filtered_items)


class MockSupabaseClient:
    def table(self, name: str):
        return MockTableQuery(name)


def get_supabase_client() -> Any:
    global _supabase_client
    if _supabase_client is None:
        try:
            from supabase import create_client
            # Verify keys are valid (not starting with sb_secret or containing placeholder text)
            if (not SUPABASE_URL 
                    or "your_supabase" in SUPABASE_URL 
                    or not SUPABASE_SERVICE_ROLE_KEY 
                    or "your_service" in SUPABASE_SERVICE_ROLE_KEY 
                    or SUPABASE_SERVICE_ROLE_KEY.startswith("sb_secret")):
                logger.warning("Supabase URL or Key is missing or placeholder/local-stub. Falling back to MockSupabaseClient.")
                _supabase_client = MockSupabaseClient()
            else:
                _supabase_client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
        except Exception as e:
            logger.warning(f"Failed to initialize Supabase client: {e}. Falling back to MockSupabaseClient.")
            _supabase_client = MockSupabaseClient()
    return _supabase_client

