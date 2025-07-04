from collections.abc import AsyncGenerator

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.requests import Request
from user_verification_service.src.core.config import Settings
from user_verification_service.src.core.logger import Logger
from user_verification_service.src.infrastructure.repositories.verification_repository import VerificationRepository
from user_verification_service.src.services.verification_service import VerificationService

settings = Settings()
logger = Logger()


async def get_db_session(request: Request) -> AsyncGenerator[AsyncSession, None]:
    """Provide database session for request"""
    async with request.app.state.db_connection.get_session() as session:
        yield session


async def get_verification_service(session: AsyncSession = Depends(get_db_session), request: Request = None) -> VerificationService:
    """Provide configured verification service"""
    return VerificationService(
        repository=VerificationRepository(session),
        event_publisher=request.app.state.kafka_publisher,
        settings=settings,
        logger=logger
    )
