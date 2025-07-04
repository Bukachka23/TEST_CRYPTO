import asyncio

from aiokafka import AIOKafkaProducer
from user_verification_service.src.core.config import Settings
from user_verification_service.src.core.logger import Logger
from user_verification_service.src.domain.interfaces.event_publisher import IEventPublisher
from user_verification_service.src.domain.schemas.events import UserVerifiedEvent


class KafkaEventPublisher(IEventPublisher):
    """Kafka event publisher."""

    def __init__(self, settings: Settings, logger: Logger):
        self.settings = settings
        self.logger = logger
        self._producer: AIOKafkaProducer | None = None

    async def get_producer(self) -> AIOKafkaProducer:
        """Get producer instance."""
        if self._producer is None:
            self._producer = AIOKafkaProducer(
                bootstrap_servers=self.settings.kafka_bootstrap_servers,
                **self.settings.kafka_producer_config,
                value_serializer=lambda v: v,
                key_serializer=lambda k: k
            )
            await self._producer.start()
        return self._producer

    async def publish(self, event: UserVerifiedEvent) -> None:
        """Publish single event with retry logic"""
        producer = await self.get_producer()
        message = event.to_kafka_message()

        try:
            await producer.send_and_wait(topic=self.settings.kafka_topic_user_verified, **message)
        except Exception as e:
            self.logger.error(f"Failed to publish event: {e}")
            # Implement retry logic or dead letter queue
            raise

    async def publish_batch(self, events: list[UserVerifiedEvent]) -> None:
        """Batch publish for better performance."""
        producer = await self.get_producer()
        tasks = [
            producer.send(topic=self.settings.kafka_topic_user_verified, **event.to_kafka_message())
            for event in events
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)
        failures = [r for r in results if isinstance(r, Exception)]

        if failures:
            self.logger.error(f"Batch publish had {len(failures)} failures")
            raise Exception("Batch publish partially failed")

    async def close(self):
        """Cleanup resources."""
        if self._producer is not None:
            await self._producer.stop()
