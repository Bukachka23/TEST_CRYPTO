import asyncio
import json

from aiokafka import AIOKafkaConsumer
from aiokafka.errors import CommitFailedError
from wallet_service.core.config import Settings
from wallet_service.core.logger import Logger
from wallet_service.domain.schemas.events import UserVerifiedEvent
from wallet_service.services.event_handler import EventHandler


class KafkaEventConsumer:
    """Kafka consumer with manual commit and error handling."""

    def __init__(self, settings: Settings, event_handler: EventHandler, logger: Logger) -> None:
        self.settings = settings
        self.event_handler = event_handler
        self._consumer: AIOKafkaConsumer | None = None
        self._running = False
        self._tasks = set()
        self.logger = logger

    async def start(self) -> None:
        """Start consuming events"""
        self._consumer = AIOKafkaConsumer(
            self.settings.kafka_topic_user_verified,
            bootstrap_servers=self.settings.kafka_bootstrap_servers,
            group_id=self.settings.kafka_consumer_group,
            **self.settings.kafka_consumer_config,
            value_deserializer=lambda m: json.loads(m.decode("utf-8"))
        )

        await self._consumer.start()
        self._running = True

        asyncio.create_task(self._consume_loop())

    async def _consume_loop(self) -> None:
        """Main consumer loop with batch processing"""
        try:
            while self._running:
                # Fetch records with timeout
                records = await self._consumer.getmany(
                    timeout_ms=self.settings.consumer_poll_timeout_ms,
                    max_records=self.settings.batch_processing_size
                )

                if not records:
                    continue

                # Process batch
                batch_tasks = []
                for topic_partition, messages in records.items():
                    for message in messages:
                        task = asyncio.create_task(
                            self._process_message(message)
                        )
                        batch_tasks.append(task)

                # Wait for batch completion
                results = await asyncio.gather(*batch_tasks, return_exceptions=True)

                # Check for failures
                failures = [r for r in results if isinstance(r, Exception)]
                if failures:
                    self.logger.error(f"Batch processing had {len(failures)} failures")
                else:
                    await self._commit_offsets()

        except Exception as e:
            self.logger.error(f"Consumer loop error: {e}", exc_info=True)
        finally:
            await self.stop()

    async def _process_message(self, message) -> None:
        """Process single message with error handling"""
        try:
            event = UserVerifiedEvent(**message.value)
            self.logger.info(
                "Received user.verified event",
                extra={
                    "user_id": event.user_id,
                    "network": event.network,
                    "offset": message.offset
                }
            )

            await self.event_handler.handle_user_verified(event)

        except Exception as e:
            self.logger.error(
                f"Failed to process message: {e}",
                extra={"offset": message.offset},
                exc_info=True
            )
            raise

    async def _commit_offsets(self) -> None:
        """Commit offsets with retry logic"""
        for attempt in range(3):
            try:
                await self._consumer.commit()
                return
            except CommitFailedError as e:
                if attempt < 2:
                    await asyncio.sleep(2 ** attempt)
                else:
                    self.logger.error(f"Failed to commit offsets: {e}")
                    raise

    async def stop(self) -> None:
        """Graceful shutdown"""
        self._running = False

        for task in self._tasks:
            task.cancel()

        await asyncio.gather(*self._tasks, return_exceptions=True)

        if self._consumer:
            await self._consumer.stop()
