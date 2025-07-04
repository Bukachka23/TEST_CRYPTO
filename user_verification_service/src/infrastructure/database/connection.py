from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from user_verification_service.src.core.config import Settings


class DatabaseConnection:
    """Connection manager with pooling."""

    def __init__(self, settings: Settings):
        self.engine = create_async_engine(
            settings.database_url,
            pool_size=settings.db_pool_size,
            max_overflow=settings.db_max_overflow,
            pool_pre_ping=settings.db_pool_pre_ping,
            echo=settings.db_echo,
            pool_recycle=3600,
            connect_args={
                "server_settings": {"jit": "off"},
                "command_timeout": 60,
                "prepared_statement_cache_size": 0,
            }
        )

        self.async_session = async_sessionmaker(self.engine, class_=AsyncSession, expire_on_commit=False)

    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator[AsyncSession | Any, Any]:
        """Get database session with automatic cleanup."""
        async with self.async_session() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()
