import asyncio

from aiokafka import AIOKafkaProducer
from wallet_service.core.config import Settings
from wallet_service.core.logger import Logger
from wallet_service.domain.interfaces.event_publisher import IEventPublisher
from wallet_service.domain.schemas.events import WalletCreatedEvent


class KafkaEventPublisher(IEventPublisher):
    """Kafka producer tailored for wallet.created events."""

    def __init__(self, settings: Settings, logger: Logger) -> None:
        self.settings = settings
        self.logger = logger
        self._producer: AIOKafkaProducer | None = None
        self._lock = asyncio.Lock()

    async def _get_producer(self) -> AIOKafkaProducer:
        """Get producer instance."""
        if self._producer is None:
            async with self._lock:
                if self._producer is None:
                    self._producer = AIOKafkaProducer(
                        bootstrap_servers=self.settings.kafka_bootstrap_servers,
                        **self.settings.kafka_producer_config,
                        value_serializer=lambda v: v,
                        key_serializer=lambda k: k,
                    )
                    await self._producer.start()
        return self._producer

    async def publish(self, event: WalletCreatedEvent) -> None:
        """Publish wallet.created event to Kafka."""
        producer = await self._get_producer()
        message = event.to_kafka_message()
        try:
            await producer.send_and_wait(
                topic=self.settings.kafka_topic_wallet_created,
                **message,
            )
        except Exception as e:
            self.logger.error(f"Failed to publish wallet.created event: {e}")
            raise

    async def publish_batch(self, events: list[WalletCreatedEvent]) -> None:
        """Publish batch of wallet.created events to Kafka."""
        producer = await self._get_producer()
        tasks = []
        for event in events:
            message = event.to_kafka_message()
            future = producer.send(
                topic=self.settings.kafka_topic_wallet_created,
                **message,
            )
            tasks.append(future)
        results = await asyncio.gather(*tasks, return_exceptions=True)
        errors = [r for r in results if isinstance(r, Exception)]
        if errors:
            self.logger.error(f"Failed to publish {len(errors)} messages")
            raise Exception("Kafka batch publish failed")

    async def close(self) -> None:
        """Cleanup resources."""
        if self._producer is not None:
            await self._producer.stop()
            self._producer = None
