from abc import ABC, abstractmethod

from user_verification_service.src.domain.schemas.events import UserVerifiedEvent


class IEventPublisher(ABC):
    """Event publisher interface"""

    @abstractmethod
    async def publish(self, event: UserVerifiedEvent) -> None:
        """Publish event to message broker"""

    @abstractmethod
    async def publish_batch(self, events: list[UserVerifiedEvent]) -> None:
        """Publish multiple events efficiently"""
