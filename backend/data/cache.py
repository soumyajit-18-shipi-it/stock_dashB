from datetime import datetime, timedelta
from typing import Any, Optional
import threading


class DataCache:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._cache = {}
                    cls._instance._timestamps = {}
                    cls._instance._ttl = 300
        return cls._instance

    def get(self, key: str) -> Optional[Any]:
        if key in self._cache:
            if datetime.now() - self._timestamps.get(key, datetime.min) < timedelta(seconds=self._ttl):
                return self._cache[key]
            else:
                del self._cache[key]
                del self._timestamps[key]
        return None

    def set(self, key: str, value: Any) -> None:
        self._cache[key] = value
        self._timestamps[key] = datetime.now()

    def clear(self) -> None:
        self._cache.clear()
        self._timestamps.clear()
