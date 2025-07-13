from uuid import UUID

from sqlalchemy import and_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from user_verification_service.src.domain.interfaces.repository import (
    IVerificationRepository,
)
from user_verification_service.src.domain.models.verification import (
    NetworkType,
    UserVerification,
    VerificationStatus,
)
from user_verification_service.src.infrastructure.database.models import (
    VerificationModel,
)


class VerificationRepository(IVerificationRepository):
    """Repository for user verification."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def save(self, verification: UserVerification) -> UserVerification:
        """Save verification to database."""
        db_verification = VerificationModel(
            user_id=verification.user_id,
            network=verification.network.value,
            document_hash=verification.document_hash,
            status=verification.status.value,
            verified_at=verification.verified_at,
            created_at=verification.created_at
        )

        self.session.add(db_verification)
        await self.session.flush()
        verification.id = db_verification.id
        return verification

    async def get_by_user_and_network(self, user_id: str, network: str) -> UserVerification | None:
        """Get verification by user and network."""
        stmt = select(VerificationModel).where(
            and_(VerificationModel.user_id == user_id, VerificationModel.network == network)
        )

        result = await self.session.execute(stmt)
        db_verification = result.scalar_one_or_none()

        return self._to_domain(db_verification) if db_verification else None

    async def update_status(self, verification_id: UUID, status: VerificationStatus) -> None:
        """Update verification status."""
        stmt = update(VerificationModel).where(VerificationModel.id == verification_id).values(status=status.value)
        await self.session.execute(stmt)

    def _to_domain(self, db_verification: VerificationModel) -> UserVerification:
        """Convert database model to domain model"""
        verification = UserVerification(
            user_id=db_verification.user_id,
            network=NetworkType(db_verification.network),
            document_hash=db_verification.document_hash
        )
        verification.id = db_verification.id
        verification.status = VerificationStatus(db_verification.status)
        verification.verified_at = db_verification.verified_at
        verification.created_at = db_verification.created_at
        return verification