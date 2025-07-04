from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession
from starlette.requests import Request
from wallet_service.core.middleware.error_handler import request_id_var
from wallet_service.infrastructure.cache.cache_service import CacheService
from wallet_service.services.wallet_service import WalletService


async def get_db_session(request: Request) -> AsyncGenerator[AsyncSession, None]:
    """Get database session with automatic cleanup."""
    async with request.app.state.db_connection.get_session() as session:
        yield session


async def get_wallet_service(request: Request) -> WalletService:
    """Get wallet service instance."""
    return request.app.state.wallet_service


async def get_cache(request: Request) -> CacheService:
    """Get Redis cache instance."""
    return request.app.state.redis_cache


def get_request_id() -> str:
    """Get request ID from context variable."""
    return request_id_var.get()
