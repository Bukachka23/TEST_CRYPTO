import asyncio
import time
from typing import Any

from wallet_service.core.config import Settings


class CacheService:
    """Simple in-memory cache replacement."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._store: dict[str, tuple[float, Any]] = {}
        self._lock = asyncio.Lock()

    async def _prefixed(self, key: str) -> str:
        """Add prefix to key."""
        return f"{self.settings.cache_key_prefix}{key}"

    async def get(self, key: str) -> Any | None:
        """Get key from cache."""
        async with self._lock:
            full_key = await self._prefixed(key)
            entry = self._store.get(full_key)
            if not entry:
                return None

            expiry, value = entry
            if expiry and expiry < time.time():
                del self._store[full_key]
                return None

            return value

    async def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        """Set key in cache."""
        ttl = ttl or self.settings.cache_ttl_seconds
        expiry = time.time() + ttl if ttl else 0
        async with self._lock:
            full_key = await self._prefixed(key)
            self._store[full_key] = (expiry, value)

    async def delete(self, key: str) -> None:
        """Delete key from cache."""
        async with self._lock:
            full_key = await self._prefixed(key)
            self._store.pop(full_key, None)

    async def close(self) -> None:
        """Cleanup resources."""
        async with self._lock:
            self._store.clear()
