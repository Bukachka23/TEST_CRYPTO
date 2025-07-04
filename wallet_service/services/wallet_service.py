import asyncio

from wallet_service.core.config import Settings
from wallet_service.core.exceptions import WalletGenerationException
from wallet_service.core.logger import Logger
from wallet_service.domain.interfaces.event_publisher import IEventPublisher
from wallet_service.domain.interfaces.wallet_repository import IWalletRepository
from wallet_service.domain.models.wallet import NetworkType, Wallet
from wallet_service.domain.schemas.events import WalletCreatedEvent
from wallet_service.infrastructure.cache.cache_service import CacheService
from wallet_service.infrastructure.crypto.wallet_factory import WalletGeneratorFactory
from wallet_service.services.derivation_service import DerivationService


class WalletService:
    """Main business logic for wallet operations."""

    def __init__(
            self,
            repository: IWalletRepository,
            generator_factory: WalletGeneratorFactory,
            event_publisher: IEventPublisher,
            derivation_service: DerivationService,
            cache: CacheService,
            settings: Settings,
            logger: Logger
    ):
        self.repository = repository
        self.generator_factory = generator_factory
        self.event_publisher = event_publisher
        self.derivation_service = derivation_service
        self.cache = cache
        self.settings = settings
        self.logger = logger
        self._generation_semaphore = asyncio.Semaphore(settings.max_concurrent_generations)

    async def create_wallet(self, user_id: str, network: str) -> Wallet:
        """Create wallet with idempotency and caching."""
        async with self._generation_semaphore:
            cache_key = f"wallet:{user_id}:{network}"
            cached_wallet = await self.cache.get(cache_key)

            if cached_wallet:
                self.logger.info(
                    "Returning cached wallet",
                    extra={
                        "user_id": user_id,
                        "network": network
                    }
                )
                return cached_wallet

            existing = await self.repository.get_by_user_and_network(user_id, network)

            if existing:
                await self.cache.set(cache_key, existing)
                return existing

            try:
                wallet = await self._generate_wallet(user_id, network)

                wallet = await self.repository.create(wallet)

                await self.cache.set(cache_key, wallet)

                asyncio.create_task(self._publish_wallet_created(wallet))

                return wallet

            except Exception as e:
                self.logger.error(
                    f"Failed to create wallet: {e}",
                    extra={
                        "user_id": user_id,
                        "network": network
                    },
                    exc_info=True
                )
                raise WalletGenerationException(f"Failed to generate wallet: {e!s}")

    async def _generate_wallet(self, user_id: str, network: str) -> Wallet | None:
        """Generate wallet address using appropriate generator."""
        network_type = NetworkType(network.lower())

        generator = self.generator_factory.get_generator(network_type)

        derivation_index = await self.derivation_service.get_next_index(network)

        mnemonic = self.settings.decrypted_mnemonic

        try:
            address = await generator.generate(
                mnemonic,
                user_id,
                derivation_index
            )
        finally:
            mnemonic = None
            import gc
            gc.collect()

        wallet = Wallet(
            user_id=user_id,
            network=network_type,
            wallet_address=address,
            derivation_index=derivation_index
        )

        return wallet

    async def get_wallet(self, user_id: str, network: str) -> Wallet | None:
        """Get wallet with caching and access tracking."""
        cache_key = f"wallet:{user_id}:{network}"
        cached_wallet = await self.cache.get(cache_key)

        if cached_wallet:
            asyncio.create_task(self.repository.update_last_accessed(cached_wallet.id))
            return cached_wallet

        wallet = await self.repository.get_by_user_and_network(user_id, network)

        if wallet:
            await self.cache.set(cache_key, wallet)
            await self.repository.update_last_accessed(wallet.id)

        return wallet

    async def _publish_wallet_created(self, wallet: Wallet) -> None:
        """Publish wallet created event with retry"""
        event = WalletCreatedEvent(
            user_id=wallet.user_id,
            network=wallet.network.value,
            wallet_address=wallet.wallet_address
        )

        for attempt in range(3):
            try:
                await self.event_publisher.publish(event)
                self.logger.info(
                    "Published wallet.created event",
                    extra={
                        "user_id": wallet.user_id,
                        "network": wallet.network.value
                    }
                )
                return
            except Exception as e:
                if attempt < 2:
                    await asyncio.sleep(2 ** attempt)
                else:
                    self.logger.error(
                        f"Failed to publish event after 3 attempts: {e}"
                    )
