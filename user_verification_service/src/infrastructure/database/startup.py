from sqlalchemy import text
from user_verification_service.src.core.config import Settings
from user_verification_service.src.infrastructure.database.connection import (
    DatabaseConnection,
)
from user_verification_service.src.infrastructure.database.models import Base


async def create_database_tables():
    """Create database tables on startup"""
    settings = Settings()
    db_connection = DatabaseConnection(settings)

    async with db_connection.engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def perform_startup_checks():
    """Perform health checks on startup"""
    settings = Settings()
    db_connection = DatabaseConnection(settings)

    async with db_connection.get_session() as session:
        await session.execute(text("SELECT 1"))
