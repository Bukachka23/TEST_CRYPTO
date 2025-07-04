import asyncio
import base64
import hashlib

from user_verification_service.src.core.config import Settings
from user_verification_service.src.core.logger import Logger
from user_verification_service.src.domain.interfaces.event_publisher import IEventPublisher
from user_verification_service.src.domain.interfaces.repository import IVerificationRepository
from user_verification_service.src.domain.models.verification import NetworkType, UserVerification, VerificationStatus
from user_verification_service.src.domain.schemas.events import UserVerifiedEvent


class VerificationService:
    def __init__(self, repository: IVerificationRepository, event_publisher: IEventPublisher, settings: Settings, logger: Logger):
        self.repository = repository
        self.event_publisher = event_publisher
        self.settings = settings
        self.logger = logger
        self._semaphore = asyncio.Semaphore(settings.max_concurrent_verifications)

    async def verify_user(self, user_id: str, network: str, document_base64: str) -> UserVerification:
        async with self._semaphore:
            document_data = base64.b64decode(document_base64)

            if len(document_data) > self.settings.max_document_size_mb * 1024 * 1024:
                raise ValueError("Document too large")

            existing = await self.repository.get_by_user_and_network(user_id, network)
            if existing and existing.status == VerificationStatus.VERIFIED:
                return existing

            verification = UserVerification(
                user_id=user_id,
                network=NetworkType(network),
                document_hash=hashlib.sha256(document_data).hexdigest()
            )

            verification = await self.repository.save(verification)
            await asyncio.sleep(self.settings.verification_delay_seconds)

            verification.verify()
            await self.repository.update_status(verification.id, verification.status)

            asyncio.create_task(self._publish_event(verification))
            return verification

    async def _publish_event(self, verification: UserVerification) -> None:
        event = UserVerifiedEvent(user_id=verification.user_id, network=verification.network.value)

        for attempt in range(3):
            try:
                await self.event_publisher.publish(event)
                return
            except Exception as e:
                if attempt < 2:
                    await asyncio.sleep(2 ** attempt)
                else:
                    self.logger.error(f"Failed to publish event after 3 attempts: {e}")
