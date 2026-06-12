from typing import Any


class DataCache:
    def __init__(self) -> None:
        self._cache: dict[str, Any] | None = None

    def get_cache(self) -> dict[str, Any]:
        if self._cache is not None:
            return self._cache
        self._cache = {}
        return self._cache

    def get(self, key: str) -> Any:
        cache = self.get_cache()
        return cache.get(key)

    def set(self, key: str, value: Any) -> None:
        cache = self.get_cache()
        cache[key] = value

    def clear(self) -> None:
        self._cache = None
