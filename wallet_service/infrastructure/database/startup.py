from sqlalchemy import text
from wallet_service.core.config import Settings
from wallet_service.infrastructure.database.connection import DatabaseConnection
from wallet_service.infrastructure.database.models import Base


async def create_database_tables() -> None:
    """Create wallet service tables on startup."""
    settings = Settings()
    db_connection = DatabaseConnection(settings)

    async with db_connection.engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def perform_startup_checks() -> None:
    """Run a simple query to ensure DB is reachable."""
    settings = Settings()
    db_connection = DatabaseConnection(settings)

    async with db_connection.get_session() as session:
        await session.execute(text("SELECT 1"))
