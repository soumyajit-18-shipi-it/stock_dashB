import logging
import os
from datetime import datetime
from typing import Any, cast

from dotenv import load_dotenv

logger = logging.getLogger("stock_dashboard")

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")

_supabase_client: Any = None


def is_placeholder_value(value: str, *, kind: str = "generic") -> bool:
    cleaned = (value or "").strip().lower()
    if not cleaned:
        return True
    placeholder_markers = (
        "your_",
        "your-",
        "replace_me",
        "changeme",
        "example",
        "placeholder",
    )
    if any(marker in cleaned for marker in placeholder_markers):
        return True
    if kind == "url" and not cleaned.startswith("https://"):
        return True
    return False


class MockResponse:
    def __init__(self, data: Any) -> None:
        self.data = data


class MockTableQuery:
    # A persistent, in-memory store for mocks
    _store: dict[str, list[dict[str, Any]]] = {
        "watchlists": [],
        "search_history": [],
        "predictions": [],
        "user_profiles": [],
        "feedback_issues": [],
    }

    def __init__(self, table_name: str) -> None:
        self.table_name = table_name
        self.filters: list[tuple[str, Any]] = []
        self._order: tuple[str, bool] | None = None
        self._limit: int | None = None
        self._inserted_data: Any = None
        self._upserted_data: Any = None
        self._deleted: bool = False
        self._update_data: dict[str, Any] | None = None

    def select(self, *_: Any, **__: Any) -> "MockTableQuery":
        return self

    def eq(self, field: str, value: Any) -> "MockTableQuery":
        self.filters.append((field, value))
        return self

    def order(self, field: str, desc: bool = False) -> "MockTableQuery":
        self._order = (field, desc)
        return self

    def limit(self, limit_val: int) -> "MockTableQuery":
        self._limit = limit_val
        return self

    def insert(self, data: Any) -> "MockTableQuery":
        self._inserted_data = data
        return self

    def upsert(self, data: Any, *_: Any, **__: Any) -> "MockTableQuery":
        self._upserted_data = data
        return self

    def delete(self) -> "MockTableQuery":
        self._deleted = True
        return self

    def update(self, data: dict[str, Any]) -> "MockTableQuery":
        self._update_data = data
        return self

    def execute(self) -> MockResponse:
        current_time = datetime.utcnow().isoformat() + "Z"

        if self._inserted_data is not None:
            return MockResponse(self._handle_insert(current_time))

        if self._upserted_data is not None:
            return MockResponse(self._handle_upsert(current_time))

        if self._deleted:
            return MockResponse(self._handle_delete())

        if self._update_data is not None:
            return MockResponse(self._handle_update())

        return MockResponse(self._handle_select())

    def _handle_insert(self, current_time: str) -> list[dict[str, Any]]:
        data_list = (
            self._inserted_data
            if isinstance(self._inserted_data, list)
            else [self._inserted_data]
        )
        new_items = []
        for item in data_list:
            store = MockTableQuery._store[self.table_name]
            new_item = {
                "id": f"mock-{self.table_name}-{len(store) + 1}",
                "created_at": current_time,
                "searched_at": current_time,
                **item,
            }
            store.append(new_item)
            new_items.append(new_item)
        return new_items

    def _handle_upsert(self, current_time: str) -> list[dict[str, Any]]:
        data_list = (
            self._upserted_data
            if isinstance(self._upserted_data, list)
            else [self._upserted_data]
        )
        store = MockTableQuery._store[self.table_name]
        upserted = []
        for item in data_list:
            item_id = item.get("id")
            existing = next((row for row in store if item_id and row.get("id") == item_id), None)
            if existing:
                existing.update(item)
                upserted.append(existing)
            else:
                new_item = {
                    "id": item_id or f"mock-{self.table_name}-{len(store) + 1}",
                    "created_at": current_time,
                    "updated_at": current_time,
                    **item,
                }
                store.append(new_item)
                upserted.append(new_item)
        return upserted

    def _handle_delete(self) -> list[dict[str, Any]]:
        matching = []
        non_matching = []
        for item in MockTableQuery._store.get(self.table_name, []):
            if self._matches_filters(item):
                matching.append(item)
            else:
                non_matching.append(item)
        MockTableQuery._store[self.table_name] = non_matching
        return matching

    def _handle_update(self) -> list[dict[str, Any]]:
        matching = []
        for item in MockTableQuery._store.get(self.table_name, []):
            if self._matches_filters(item):
                if self._update_data:
                    item.update(self._update_data)
                matching.append(item)
        return matching

    def _handle_select(self) -> list[dict[str, Any]]:
        items = MockTableQuery._store.get(self.table_name, [])
        filtered_items = [item for item in items if self._matches_filters(item)]

        if self._order:
            field, desc = self._order
            try:
                filtered_items.sort(key=lambda x: x.get(field) or "", reverse=desc)
            except Exception as e:
                logger.debug(f"Sorting failed: {e}")

        if self._limit is not None:
            filtered_items = filtered_items[: self._limit]

        return filtered_items

    def _matches_filters(self, item: dict[str, Any]) -> bool:
        for field, val in self.filters:
            if item.get(field) != val:
                return False
        return True


class MockSupabaseClient:
    def table(self, name: str) -> MockTableQuery:
        return MockTableQuery(name)


def get_supabase_client() -> Any:
    global _supabase_client  # pylint: disable=global-statement
    if _supabase_client is None:
        try:
            # pylint: disable=import-outside-toplevel,no-name-in-module
            from supabase import create_client

            # Verify keys are valid
            if is_placeholder_value(SUPABASE_URL, kind="url") or is_placeholder_value(
                SUPABASE_SERVICE_ROLE_KEY, kind="service_role"
            ):
                logger.warning(
                    "Supabase URL or Key is missing or placeholder. "
                    "Falling back to MockSupabaseClient."
                )
                _supabase_client = MockSupabaseClient()
            else:
                _supabase_client = create_client(
                    SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY
                )
        except Exception:  # pylint: disable=broad-exception-caught
            logger.warning(
                "Failed to initialize Supabase client. Falling back to Mock."
            )
            _supabase_client = MockSupabaseClient()
    return cast(Any, _supabase_client)
