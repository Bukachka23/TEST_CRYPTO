import base64
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from user_verification_service.src.core.config import Settings
from user_verification_service.src.core.logger import Logger
from user_verification_service.src.domain.interfaces.event_publisher import IEventPublisher
from user_verification_service.src.domain.interfaces.repository import IVerificationRepository
from user_verification_service.src.domain.models.verification import NetworkType, UserVerification
from user_verification_service.src.domain.schemas.events import UserVerifiedEvent
from user_verification_service.src.infrastructure.database.models import VerificationModel
from user_verification_service.src.infrastructure.kafka.producer import KafkaEventPublisher
from user_verification_service.src.infrastructure.repositories.verification_repository import VerificationRepository
from user_verification_service.src.services.verification_service import VerificationService


@pytest.fixture
def mock_repository():
    """Provides a mock repository for testing."""
    return AsyncMock(spec=IVerificationRepository)


@pytest.fixture
def mock_event_publisher():
    """Provides a mock event publisher for testing."""
    return AsyncMock(spec=IEventPublisher)


@pytest.fixture
def test_settings():
    """Provides test settings configuration."""
    return Settings(
        max_document_size_mb=5,
        max_concurrent_verifications=10,
        verification_delay_seconds=0.1
    )


@pytest.fixture
def mock_logger():
    """Provides a mock logger for testing."""
    return MagicMock(spec=Logger)


@pytest.fixture
def verification_service(mock_repository, mock_event_publisher, test_settings, mock_logger):
    """Provides a configured VerificationService instance."""
    return VerificationService(
        repository=mock_repository,
        event_publisher=mock_event_publisher,
        settings=test_settings,
        logger=mock_logger
    )


@pytest.fixture
def valid_document_base64():
    """Provides a valid base64 encoded document."""
    document_data = b"test document content"
    return base64.b64encode(document_data).decode("utf-8")


@pytest.fixture
def valid_user_verification():
    """Provides a valid UserVerification instance for testing."""
    return UserVerification(
        user_id="test_user_123",
        network=NetworkType.ETHEREUM,
        document_hash="abc123def456"
    )


@pytest.fixture
def verification_with_id():
    """Provides a UserVerification instance with ID set."""
    verification = UserVerification(
        user_id="test_user_456",
        network=NetworkType.BITCOIN,
        document_hash="xyz789uvw012"
    )
    verification.id = uuid4()
    return verification


@pytest.fixture
def existing_verified_user():
    """Provides an existing verified user verification."""
    verification = UserVerification(
        user_id="existing_user",
        network=NetworkType.ETHEREUM,
        document_hash="existing_hash"
    )
    verification.id = uuid4()
    verification.verify()
    return verification


@pytest.fixture
def existing_pending_user():
    """Provides an existing pending user verification."""
    verification = UserVerification(
        user_id="pending_user",
        network=NetworkType.ETHEREUM,
        document_hash="pending_hash"
    )
    verification.id = uuid4()
    return verification


@pytest.fixture
def valid_verification_request_data():
    """Provides valid data for VerificationRequest."""
    return {
        "user_id": "test_user_123",
        "network": "ethereum",
        "document": base64.b64encode(b"test document content").decode("utf-8")
    }


@pytest.fixture
def valid_verification_response_data():
    """Provides valid data for VerificationResponse."""
    return {
        "message": "Verification in progress",
        "verification_id": str(uuid4()),
        "status": "pending"
    }


@pytest.fixture
def sample_image_base64():
    """Provides a sample base64 encoded image."""
    return "iVBORw0KGgoAAAANSUhEUgAAAAUAAAAFCAYAAACNbyblAAAAHElEQVQI12P4//8/w38GIAXDIBKE0DHxgljNBAAO9TXL0Y4OHwAAAABJRU5ErkJggg=="


@pytest.fixture
def minimal_document_base64():
    """Provides a minimal valid base64 document."""
    return base64.b64encode(b"a").decode("utf-8")


@pytest.fixture
def large_document_base64():
    """Provides a large base64 document for testing limits."""
    large_data = b"x" * 1000000  # 1MB of data
    return base64.b64encode(large_data).decode("utf-8")


@pytest.fixture
def mock_async_session():
    """Provides a mock async database session for testing."""
    session = AsyncMock(spec=AsyncSession)
    return session


@pytest.fixture
def verification_repository(mock_async_session):
    """Provides a VerificationRepository instance with mocked session."""
    return VerificationRepository(mock_async_session)


@pytest.fixture
def verification_model():
    """Provides a sample VerificationModel for testing."""
    return VerificationModel(
        id=uuid4(),
        user_id="test_user_123",
        network="ethereum",
        document_hash="abc123def456",
        status="pending",
        verified_at=None,
        created_at=datetime.now(),
        version=1
    )


@pytest.fixture
def verified_verification_model():
    """Provides a verified VerificationModel for testing."""
    return VerificationModel(
        id=uuid4(),
        user_id="verified_user",
        network="bitcoin",
        document_hash="verified_hash",
        status="verified",
        verified_at=datetime.now(),
        created_at=datetime.now(),
        version=1
    )


@pytest.fixture
def mock_db_result():
    """Provides a mock database result for testing."""
    mock_result = MagicMock()
    return mock_result


@pytest.fixture
def user_verified_event():
    """Provides a UserVerifiedEvent for testing."""
    return UserVerifiedEvent(
        user_id="test_user_123",
        network="ethereum"
    )


@pytest.fixture
def multiple_user_verified_events():
    """Provides multiple UserVerifiedEvent instances for batch testing."""
    return [
        UserVerifiedEvent(user_id="user_1", network="ethereum"),
        UserVerifiedEvent(user_id="user_2", network="bitcoin"),
        UserVerifiedEvent(user_id="user_3", network="tron")
    ]


@pytest.fixture
def mock_kafka_producer():
    """Provides a mock AIOKafkaProducer for testing."""
    from aiokafka import AIOKafkaProducer
    producer = AsyncMock(spec=AIOKafkaProducer)
    producer.send_and_wait = AsyncMock()
    producer.send = AsyncMock()
    producer.start = AsyncMock()
    producer.stop = AsyncMock()
    return producer


@pytest.fixture
def kafka_event_publisher(test_settings, mock_logger):
    """Provides a KafkaEventPublisher instance for testing."""
    return KafkaEventPublisher(
        settings=test_settings,
        logger=mock_logger
    )


@pytest.fixture
def kafka_settings():
    """Provides Kafka-specific settings for testing."""
    return Settings(
        kafka_bootstrap_servers="localhost:9092",
        kafka_topic_user_verified="test.user.verified",
        kafka_producer_config={
            "acks": "all",
            "compression_type": "gzip",
            "max_batch_size": 16384,
            "linger_ms": 10
        }
    )
