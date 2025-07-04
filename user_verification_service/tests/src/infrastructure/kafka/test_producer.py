import asyncio
from datetime import datetime
from unittest.mock import AsyncMock, patch

import pytest
from aiokafka import AIOKafkaProducer
from user_verification_service.src.domain.schemas.events import UserVerifiedEvent
from user_verification_service.src.infrastructure.kafka.producer import KafkaEventPublisher


class TestKafkaEventPublisher:
    """Test cases for KafkaEventPublisher."""

    def test_kafka_event_publisher_initialization(self, test_settings, mock_logger):
        """Test that KafkaEventPublisher initializes correctly."""
        # Arrange & Act
        publisher = KafkaEventPublisher(test_settings, mock_logger)

        # Assert
        assert publisher.settings == test_settings
        assert publisher.logger == mock_logger
        assert publisher._producer is None

    async def test_get_producer_creates_new_producer_on_first_call(self, kafka_event_publisher, test_settings):
        """Test that get_producer creates a new producer on first call."""
        # Arrange
        with patch("user_verification_service.src.infrastructure.kafka.producer.AIOKafkaProducer") as mock_producer_class:
            mock_producer = AsyncMock(spec=AIOKafkaProducer)
            mock_producer_class.return_value = mock_producer

            # Act
            result = await kafka_event_publisher.get_producer()

            # Assert
            mock_producer_class.assert_called_once()
            call_args = mock_producer_class.call_args
            assert call_args.kwargs["bootstrap_servers"] == test_settings.kafka_bootstrap_servers
            assert call_args.kwargs["acks"] == test_settings.kafka_producer_config["acks"]
            assert call_args.kwargs["compression_type"] == test_settings.kafka_producer_config["compression_type"]
            assert callable(call_args.kwargs["value_serializer"])
            assert callable(call_args.kwargs["key_serializer"])
            mock_producer.start.assert_called_once()
            assert result == mock_producer
            assert kafka_event_publisher._producer == mock_producer

    async def test_get_producer_returns_existing_producer_on_subsequent_calls(self, kafka_event_publisher):
        """Test that get_producer returns existing producer on subsequent calls."""
        # Arrange
        existing_producer = AsyncMock(spec=AIOKafkaProducer)
        kafka_event_publisher._producer = existing_producer

        # Act
        result = await kafka_event_publisher.get_producer()

        # Assert
        assert result == existing_producer
        existing_producer.start.assert_not_called()

    async def test_get_producer_configures_serializers_correctly(self, kafka_event_publisher, test_settings):
        """Test that get_producer configures serializers correctly."""
        # Arrange
        with patch("user_verification_service.src.infrastructure.kafka.producer.AIOKafkaProducer") as mock_producer_class:
            mock_producer = AsyncMock(spec=AIOKafkaProducer)
            mock_producer_class.return_value = mock_producer

            # Act
            await kafka_event_publisher.get_producer()

            # Assert
            call_args = mock_producer_class.call_args
            assert "value_serializer" in call_args.kwargs
            assert "key_serializer" in call_args.kwargs
            assert callable(call_args.kwargs["value_serializer"])
            assert callable(call_args.kwargs["key_serializer"])

            # Test that serializers work correctly
            value_serializer = call_args.kwargs["value_serializer"]
            key_serializer = call_args.kwargs["key_serializer"]
            assert value_serializer("test") == "test"
            assert key_serializer("key") == "key"

    async def test_publish_single_event_successfully(self, kafka_event_publisher, user_verified_event, test_settings):
        """Test publishing a single event successfully."""
        # Arrange
        mock_producer = AsyncMock(spec=AIOKafkaProducer)
        kafka_event_publisher._producer = mock_producer
        expected_message = user_verified_event.to_kafka_message()

        # Act
        await kafka_event_publisher.publish(user_verified_event)

        # Assert
        mock_producer.send_and_wait.assert_called_once_with(
            topic=test_settings.kafka_topic_user_verified,
            **expected_message
        )

    async def test_publish_single_event_creates_producer_if_none_exists(self, kafka_event_publisher, user_verified_event, test_settings):
        """Test that publish creates producer if none exists."""
        # Arrange
        with patch("user_verification_service.src.infrastructure.kafka.producer.AIOKafkaProducer") as mock_producer_class:
            mock_producer = AsyncMock(spec=AIOKafkaProducer)
            mock_producer_class.return_value = mock_producer

            # Act
            await kafka_event_publisher.publish(user_verified_event)

            # Assert
            mock_producer_class.assert_called_once()
            mock_producer.start.assert_called_once()
            mock_producer.send_and_wait.assert_called_once()

    async def test_publish_single_event_handles_kafka_error(self, kafka_event_publisher, user_verified_event, mock_logger):
        """Test that publish handles Kafka errors correctly."""
        # Arrange
        mock_producer = AsyncMock(spec=AIOKafkaProducer)
        kafka_error = Exception("Kafka connection failed")
        mock_producer.send_and_wait.side_effect = kafka_error
        kafka_event_publisher._producer = mock_producer

        # Act & Assert
        with pytest.raises(Exception, match="Kafka connection failed"):
            await kafka_event_publisher.publish(user_verified_event)

        mock_logger.error.assert_called_once_with("Failed to publish event: Kafka connection failed")

    async def test_publish_single_event_uses_correct_message_format(self, kafka_event_publisher, user_verified_event, test_settings):
        """Test that publish uses correct message format from event."""
        # Arrange
        mock_producer = AsyncMock(spec=AIOKafkaProducer)
        kafka_event_publisher._producer = mock_producer

        # Act
        await kafka_event_publisher.publish(user_verified_event)

        # Assert
        call_args = mock_producer.send_and_wait.call_args
        assert call_args.kwargs["topic"] == test_settings.kafka_topic_user_verified
        assert "key" in call_args.kwargs
        assert "value" in call_args.kwargs
        assert "headers" in call_args.kwargs

    async def test_publish_batch_events_successfully(self, kafka_event_publisher, multiple_user_verified_events, test_settings):
        """Test publishing multiple events in batch successfully."""
        # Arrange
        mock_producer = AsyncMock(spec=AIOKafkaProducer)
        kafka_event_publisher._producer = mock_producer

        # Mock successful futures for all events
        mock_futures = [AsyncMock() for _ in multiple_user_verified_events]
        mock_producer.send.side_effect = mock_futures

        # Act
        await kafka_event_publisher.publish_batch(multiple_user_verified_events)

        # Assert
        assert mock_producer.send.call_count == len(multiple_user_verified_events)
        for i, event in enumerate(multiple_user_verified_events):
            expected_message = event.to_kafka_message()
            mock_producer.send.assert_any_call(
                topic=test_settings.kafka_topic_user_verified,
                **expected_message
            )

    async def test_publish_batch_events_creates_producer_if_none_exists(self, kafka_event_publisher, multiple_user_verified_events):
        """Test that publish_batch creates producer if none exists."""
        # Arrange
        with patch("user_verification_service.src.infrastructure.kafka.producer.AIOKafkaProducer") as mock_producer_class:
            mock_producer = AsyncMock(spec=AIOKafkaProducer)
            mock_producer_class.return_value = mock_producer
            mock_futures = [AsyncMock() for _ in multiple_user_verified_events]
            mock_producer.send.side_effect = mock_futures

            # Act
            await kafka_event_publisher.publish_batch(multiple_user_verified_events)

            # Assert
            mock_producer_class.assert_called_once()
            mock_producer.start.assert_called_once()
            assert mock_producer.send.call_count == len(multiple_user_verified_events)

    async def test_publish_batch_events_handles_partial_failures(self, kafka_event_publisher, multiple_user_verified_events, mock_logger):
        """Test that publish_batch handles partial failures correctly."""
        # Arrange
        mock_producer = AsyncMock(spec=AIOKafkaProducer)
        kafka_event_publisher._producer = mock_producer

        # Mock mixed success and failure results
        success_future = AsyncMock()
        failure_exception = Exception("Send failed")
        mock_producer.send.side_effect = [success_future, failure_exception, success_future]

        # Act & Assert
        with pytest.raises(Exception, match="Batch publish partially failed"):
            await kafka_event_publisher.publish_batch(multiple_user_verified_events)

        mock_logger.error.assert_called_once_with("Batch publish had 1 failures")

    async def test_publish_batch_events_handles_all_failures(self, kafka_event_publisher, multiple_user_verified_events, mock_logger):
        """Test that publish_batch handles all failures correctly."""
        # Arrange
        mock_producer = AsyncMock(spec=AIOKafkaProducer)
        kafka_event_publisher._producer = mock_producer

        # Mock all failures
        failure_exception = Exception("All sends failed")
        mock_producer.send.side_effect = [failure_exception] * len(multiple_user_verified_events)

        # Act & Assert
        with pytest.raises(Exception, match="Batch publish partially failed"):
            await kafka_event_publisher.publish_batch(multiple_user_verified_events)

        mock_logger.error.assert_called_once_with(f"Batch publish had {len(multiple_user_verified_events)} failures")

    async def test_publish_batch_empty_list_succeeds(self, kafka_event_publisher):
        """Test that publish_batch with empty list succeeds without error."""
        # Arrange
        mock_producer = AsyncMock(spec=AIOKafkaProducer)
        kafka_event_publisher._producer = mock_producer
        empty_events = []

        # Act
        await kafka_event_publisher.publish_batch(empty_events)

        # Assert
        mock_producer.send.assert_not_called()

    async def test_publish_batch_single_event_works(self, kafka_event_publisher, user_verified_event, test_settings):
        """Test that publish_batch works with single event."""
        # Arrange
        mock_producer = AsyncMock(spec=AIOKafkaProducer)
        kafka_event_publisher._producer = mock_producer
        mock_future = AsyncMock()
        mock_producer.send.return_value = mock_future

        # Act
        await kafka_event_publisher.publish_batch([user_verified_event])

        # Assert
        mock_producer.send.assert_called_once_with(
            topic=test_settings.kafka_topic_user_verified,
            **user_verified_event.to_kafka_message()
        )

    async def test_close_stops_producer_if_exists(self, kafka_event_publisher):
        """Test that close stops the producer if it exists."""
        # Arrange
        mock_producer = AsyncMock(spec=AIOKafkaProducer)
        kafka_event_publisher._producer = mock_producer

        # Act
        await kafka_event_publisher.close()

        # Assert
        mock_producer.stop.assert_called_once()

    async def test_close_does_nothing_if_no_producer(self, kafka_event_publisher):
        """Test that close does nothing if no producer exists."""
        # Arrange
        assert kafka_event_publisher._producer is None

        # Act
        await kafka_event_publisher.close()

        # Assert - no exception should be raised

    async def test_close_handles_producer_stop_error(self, kafka_event_publisher):
        """Test that close handles producer stop errors gracefully."""
        # Arrange
        mock_producer = AsyncMock(spec=AIOKafkaProducer)
        mock_producer.stop.side_effect = Exception("Stop failed")
        kafka_event_publisher._producer = mock_producer

        # Act & Assert - should raise exception since close doesn't handle errors
        with pytest.raises(Exception, match="Stop failed"):
            await kafka_event_publisher.close()
        mock_producer.stop.assert_called_once()

    async def test_publisher_uses_correct_kafka_settings(self, kafka_settings, mock_logger):
        """Test that publisher uses correct Kafka settings from configuration."""
        # Arrange
        publisher = KafkaEventPublisher(kafka_settings, mock_logger)

        with patch("user_verification_service.src.infrastructure.kafka.producer.AIOKafkaProducer") as mock_producer_class:
            mock_producer = AsyncMock(spec=AIOKafkaProducer)
            mock_producer_class.return_value = mock_producer

            # Act
            await publisher.get_producer()

            # Assert
            mock_producer_class.assert_called_once()
            call_args = mock_producer_class.call_args
            assert call_args.kwargs["bootstrap_servers"] == kafka_settings.kafka_bootstrap_servers
            assert call_args.kwargs["acks"] == kafka_settings.kafka_producer_config["acks"]
            assert call_args.kwargs["compression_type"] == kafka_settings.kafka_producer_config["compression_type"]
            assert callable(call_args.kwargs["value_serializer"])
            assert callable(call_args.kwargs["key_serializer"])

    async def test_publish_event_with_custom_timestamp(self, kafka_event_publisher, test_settings):
        """Test publishing event with custom timestamp."""
        # Arrange
        custom_timestamp = datetime(2023, 1, 1, 12, 0, 0)
        custom_event = UserVerifiedEvent(
            user_id="custom_user",
            network="ethereum",
            timestamp=custom_timestamp
        )
        mock_producer = AsyncMock(spec=AIOKafkaProducer)
        kafka_event_publisher._producer = mock_producer

        # Act
        await kafka_event_publisher.publish(custom_event)

        # Assert
        call_args = mock_producer.send_and_wait.call_args
        assert call_args.kwargs["topic"] == test_settings.kafka_topic_user_verified

        # Verify the message contains the custom timestamp
        expected_message = custom_event.to_kafka_message()
        assert call_args.kwargs["key"] == expected_message["key"]
        assert call_args.kwargs["value"] == expected_message["value"]

    async def test_publish_events_with_different_networks(self, kafka_event_publisher, test_settings):
        """Test publishing events with different network types."""
        # Arrange
        events = [
            UserVerifiedEvent(user_id="user1", network="ethereum"),
            UserVerifiedEvent(user_id="user2", network="bitcoin"),
            UserVerifiedEvent(user_id="user3", network="tron")
        ]
        mock_producer = AsyncMock(spec=AIOKafkaProducer)
        kafka_event_publisher._producer = mock_producer
        mock_futures = [AsyncMock() for _ in events]
        mock_producer.send.side_effect = mock_futures

        # Act
        await kafka_event_publisher.publish_batch(events)

        # Assert
        assert mock_producer.send.call_count == 3
        for event in events:
            expected_message = event.to_kafka_message()
            mock_producer.send.assert_any_call(
                topic=test_settings.kafka_topic_user_verified,
                **expected_message
            )

    async def test_publish_events_with_special_characters_in_user_id(self, kafka_event_publisher, test_settings):
        """Test publishing events with special characters in user_id."""
        # Arrange
        special_user_event = UserVerifiedEvent(
            user_id="user@domain.com",
            network="ethereum"
        )
        mock_producer = AsyncMock(spec=AIOKafkaProducer)
        kafka_event_publisher._producer = mock_producer

        # Act
        await kafka_event_publisher.publish(special_user_event)

        # Assert
        call_args = mock_producer.send_and_wait.call_args
        expected_message = special_user_event.to_kafka_message()
        assert call_args.kwargs["key"] == expected_message["key"]
        assert call_args.kwargs["value"] == expected_message["value"]

    async def test_concurrent_publish_operations(self, kafka_event_publisher, multiple_user_verified_events):
        """Test concurrent publish operations work correctly."""
        # Arrange
        mock_producer = AsyncMock(spec=AIOKafkaProducer)
        kafka_event_publisher._producer = mock_producer

        # Act
        tasks = [
            kafka_event_publisher.publish(event)
            for event in multiple_user_verified_events
        ]
        await asyncio.gather(*tasks)

        # Assert
        assert mock_producer.send_and_wait.call_count == len(multiple_user_verified_events)

    async def test_serializer_functions_work_correctly(self, kafka_event_publisher):
        """Test that the serializer functions work as expected."""
        # Arrange
        with patch("user_verification_service.src.infrastructure.kafka.producer.AIOKafkaProducer") as mock_producer_class:
            mock_producer = AsyncMock(spec=AIOKafkaProducer)
            mock_producer_class.return_value = mock_producer

            # Act
            await kafka_event_publisher.get_producer()

            # Assert
            call_args = mock_producer_class.call_args
            value_serializer = call_args.kwargs["value_serializer"]
            key_serializer = call_args.kwargs["key_serializer"]

            # Test serializers with different data types
            assert value_serializer("string") == "string"
            assert value_serializer(b"bytes") == b"bytes"
            assert key_serializer("key") == "key"
            assert key_serializer(b"key_bytes") == b"key_bytes"
