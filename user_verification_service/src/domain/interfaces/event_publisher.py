from abc import ABC, abstractmethod

from user_verification_service.src.domain.schemas.events import UserVerifiedEvent


class IEventPublisher(ABC):
    @abstractmethod
    async def publish(self, event: UserVerifiedEvent) -> None:
        pass

    @abstractmethod
    async def publish_batch(self, events: list[UserVerifiedEvent]) -> None:
        pass
