import asyncio

from wallet_service.domain.interfaces.wallet_repository import IWalletRepository
from wallet_service.infrastructure.cache.cache_service import CacheService


class DerivationService:
    """Manages HD wallet derivation indices."""

    def __init__(self, repository: IWalletRepository, cache: CacheService):
        self.repository = repository
        self.cache = cache
        self._index_locks = {}

    async def get_next_index(self, network: str) -> int:
        """Get next derivation index with caching and locking"""
        if network not in self._index_locks:
            self._index_locks[network] = asyncio.Lock()

        async with self._index_locks[network]:
            cache_key = f"next_index:{network}"
            cached_index = await self.cache.get(cache_key)

            if cached_index is not None:
                next_index = cached_index + 1
                await self.cache.set(cache_key, next_index)
                return cached_index

            next_index = await self.repository.get_next_derivation_index(network)

            await self.cache.set(cache_key, next_index + 1)

            return next_index
