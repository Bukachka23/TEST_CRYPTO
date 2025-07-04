import asyncio

from wallet_service.core.config import Settings
from wallet_service.core.exceptions import WalletAlreadyExistsException
from wallet_service.core.logger import Logger
from wallet_service.domain.schemas.events import UserVerifiedEvent
from wallet_service.services.wallet_service import WalletService


class EventHandler:
    """Handles incoming Kafka events."""

    def __init__(self, wallet_service: WalletService, settings: Settings, logger: Logger):
        self.wallet_service = wallet_service
        self.settings = settings
        self._processed_events = set()
        self._event_lock = asyncio.Lock()
        self.logger = logger

    async def handle_user_verified(self, event: UserVerifiedEvent) -> None:
        """Handle user.verified event with idempotency."""
        event_key = f"{event.user_id}:{event.network}:{event.timestamp}"

        async with self._event_lock:
            if event_key in self._processed_events:
                self.logger.warning(
                    "Duplicate event detected, skipping",
                    extra={
                        "user_id": event.user_id,
                        "network": event.network
                    }
                )
                return

            self._processed_events.add(event_key)

            if len(self._processed_events) > 10000:
                self._processed_events = set(list(self._processed_events)[-5000:])

        try:
            wallet = await self.wallet_service.create_wallet(user_id=event.user_id, network=event.network)

            self.logger.info(
                "Wallet created for verified user",
                extra={
                    "user_id": event.user_id,
                    "network": event.network,
                    "wallet_address": wallet.wallet_address
                }
            )

        except WalletAlreadyExistsException:
            self.logger.info(
                "Wallet already exists for user",
                extra={
                    "user_id": event.user_id,
                    "network": event.network
                }
            )
        except Exception as e:
            self.logger.error(
                f"Failed to handle user.verified event: {e}",
                extra={
                    "user_id": event.user_id,
                    "network": event.network
                },
                exc_info=True
            )
            async with self._event_lock:
                self._processed_events.discard(event_key)
            raise
