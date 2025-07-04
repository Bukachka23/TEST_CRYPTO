from abc import ABC, abstractmethod
from uuid import UUID

from user_verification_service.src.domain.models.verification import (
    UserVerification,
    VerificationStatus,
)


class IVerificationRepository(ABC):
    @abstractmethod
    async def save(self, verification: UserVerification) -> UserVerification:
        pass

    @abstractmethod
    async def get_by_user_and_network(self, user_id: str, network: str) -> UserVerification | None:
        pass

    @abstractmethod
    async def update_status(self, verification_id: UUID, status: VerificationStatus) -> None:
        pass
