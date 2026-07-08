from typing import Any


class DataCache:
    def __init__(self) -> None:
        self._cache: dict[str, Any] | None = None

    def get_cache(self) -> dict[str, Any]:
        if self._cache is None:
            self._cache = {}
        return self._cache

    def get(self, key: str) -> Any:
        return self.get_cache().get(key)

    def set(self, key: str, value: Any) -> None:
        self.get_cache()[key] = value

    def clear(self) -> None:
        self._cache = None
