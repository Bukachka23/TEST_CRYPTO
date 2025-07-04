import asyncio
import base64
import hashlib
from unittest.mock import patch
from uuid import uuid4

import pytest
from user_verification_service.src.domain.models.verification import NetworkType, UserVerification, VerificationStatus
from user_verification_service.src.domain.schemas.events import UserVerifiedEvent
from user_verification_service.src.services.verification_service import VerificationService


class TestVerificationService:
    """Test cases for VerificationService."""

    async def test_verify_user_successful_new_verification(self, verification_service, mock_repository, valid_document_base64):
        # Arrange
        user_id = "test_user"
        network = "ethereum"
        mock_repository.get_by_user_and_network.return_value = None

        saved_verification = UserVerification(
            user_id=user_id,
            network=NetworkType.ETHEREUM,
            document_hash=hashlib.sha256(base64.b64decode(valid_document_base64)).hexdigest()
        )
        saved_verification.id = uuid4()
        mock_repository.save.return_value = saved_verification

        # Act
        result = await verification_service.verify_user(user_id, network, valid_document_base64)

        # Assert
        assert result.user_id == user_id
        assert result.network == NetworkType.ETHEREUM
        assert result.status == VerificationStatus.VERIFIED
        assert result.verified_at is not None
        mock_repository.get_by_user_and_network.assert_called_once_with(user_id, network)
        mock_repository.save.assert_called_once()
        mock_repository.update_status.assert_called_once_with(saved_verification.id, VerificationStatus.VERIFIED)

    async def test_verify_user_returns_existing_verified_user(self, verification_service, mock_repository, existing_verified_user, valid_document_base64):
        # Arrange
        user_id = "existing_user"
        network = "ethereum"
        mock_repository.get_by_user_and_network.return_value = existing_verified_user

        # Act
        result = await verification_service.verify_user(user_id, network, valid_document_base64)

        # Assert
        assert result == existing_verified_user
        assert result.status == VerificationStatus.VERIFIED
        mock_repository.get_by_user_and_network.assert_called_once_with(user_id, network)
        mock_repository.save.assert_not_called()
        mock_repository.update_status.assert_not_called()

    async def test_verify_user_processes_existing_pending_user(self, verification_service, mock_repository, existing_pending_user, valid_document_base64):
        # Arrange
        user_id = "pending_user"
        network = "ethereum"
        mock_repository.get_by_user_and_network.return_value = existing_pending_user

        saved_verification = UserVerification(
            user_id=user_id,
            network=NetworkType.ETHEREUM,
            document_hash=hashlib.sha256(base64.b64decode(valid_document_base64)).hexdigest()
        )
        saved_verification.id = uuid4()
        mock_repository.save.return_value = saved_verification

        # Act
        result = await verification_service.verify_user(user_id, network, valid_document_base64)

        # Assert
        assert result.user_id == user_id
        assert result.status == VerificationStatus.VERIFIED
        mock_repository.get_by_user_and_network.assert_called_once_with(user_id, network)
        mock_repository.save.assert_called_once()
        mock_repository.update_status.assert_called_once()

    async def test_verify_user_document_too_large_raises_error(self, verification_service, test_settings):
        # Arrange
        user_id = "test_user"
        network = "ethereum"
        large_document = b"x" * (test_settings.max_document_size_mb * 1024 * 1024 + 1)
        large_document_base64 = base64.b64encode(large_document).decode("utf-8")

        # Act & Assert
        with pytest.raises(ValueError, match="Document too large"):
            await verification_service.verify_user(user_id, network, large_document_base64)

    async def test_verify_user_with_empty_document(self, verification_service, mock_repository):
        # Arrange
        user_id = "test_user"
        network = "ethereum"
        empty_document_base64 = base64.b64encode(b"").decode("utf-8")
        mock_repository.get_by_user_and_network.return_value = None

        saved_verification = UserVerification(
            user_id=user_id,
            network=NetworkType.ETHEREUM,
            document_hash=hashlib.sha256(b"").hexdigest()
        )
        saved_verification.id = uuid4()
        mock_repository.save.return_value = saved_verification

        # Act
        result = await verification_service.verify_user(user_id, network, empty_document_base64)

        # Assert
        assert result.status == VerificationStatus.VERIFIED
        assert result.document_hash == hashlib.sha256(b"").hexdigest()

    async def test_verify_user_invalid_network_raises_error(self, verification_service, valid_document_base64):
        # Arrange
        user_id = "test_user"
        invalid_network = "invalid_network"

        # Act & Assert
        with pytest.raises(ValueError):
            await verification_service.verify_user(user_id, invalid_network, valid_document_base64)

    async def test_verify_user_creates_correct_document_hash(self, verification_service, mock_repository, valid_document_base64):
        # Arrange
        user_id = "test_user"
        network = "ethereum"
        mock_repository.get_by_user_and_network.return_value = None

        expected_hash = hashlib.sha256(base64.b64decode(valid_document_base64)).hexdigest()
        saved_verification = UserVerification(
            user_id=user_id,
            network=NetworkType.ETHEREUM,
            document_hash=expected_hash
        )
        saved_verification.id = uuid4()
        mock_repository.save.return_value = saved_verification

        # Act
        await verification_service.verify_user(user_id, network, valid_document_base64)

        # Assert
        save_call_args = mock_repository.save.call_args[0][0]
        assert save_call_args.document_hash == expected_hash

    async def test_verify_user_handles_different_networks(self, verification_service, mock_repository, valid_document_base64):
        # Arrange
        user_id = "test_user"
        networks = ["ethereum", "tron", "bitcoin"]
        mock_repository.get_by_user_and_network.return_value = None

        for network in networks:
            saved_verification = UserVerification(
                user_id=user_id,
                network=NetworkType(network),
                document_hash="test_hash"
            )
            saved_verification.id = uuid4()
            mock_repository.save.return_value = saved_verification

            # Act
            result = await verification_service.verify_user(user_id, network, valid_document_base64)

            # Assert
            assert result.network == NetworkType(network)

    async def test_verify_user_repository_save_failure_propagates(self, verification_service, mock_repository, valid_document_base64):
        # Arrange
        user_id = "test_user"
        network = "ethereum"
        mock_repository.get_by_user_and_network.return_value = None
        mock_repository.save.side_effect = Exception("Database error")

        # Act & Assert
        with pytest.raises(Exception, match="Database error"):
            await verification_service.verify_user(user_id, network, valid_document_base64)

    async def test_verify_user_repository_update_failure_propagates(self, verification_service, mock_repository, valid_document_base64):
        # Arrange
        user_id = "test_user"
        network = "ethereum"
        mock_repository.get_by_user_and_network.return_value = None

        saved_verification = UserVerification(
            user_id=user_id,
            network=NetworkType.ETHEREUM,
            document_hash="test_hash"
        )
        saved_verification.id = uuid4()
        mock_repository.save.return_value = saved_verification
        mock_repository.update_status.side_effect = Exception("Update error")

        # Act & Assert
        with pytest.raises(Exception, match="Update error"):
            await verification_service.verify_user(user_id, network, valid_document_base64)

    @patch("asyncio.create_task")
    async def test_verify_user_creates_event_publishing_task(self, mock_create_task, verification_service, mock_repository, valid_document_base64):
        # Arrange
        user_id = "test_user"
        network = "ethereum"
        mock_repository.get_by_user_and_network.return_value = None

        saved_verification = UserVerification(
            user_id=user_id,
            network=NetworkType.ETHEREUM,
            document_hash="test_hash"
        )
        saved_verification.id = uuid4()
        mock_repository.save.return_value = saved_verification

        # Act
        await verification_service.verify_user(user_id, network, valid_document_base64)

        # Assert
        mock_create_task.assert_called_once()

    async def test_publish_event_successful_first_attempt(self, verification_service, mock_event_publisher):
        # Arrange
        verification = UserVerification(
            user_id="test_user",
            network=NetworkType.ETHEREUM,
            document_hash="test_hash"
        )
        verification.verify()

        # Act
        await verification_service._publish_event(verification)

        # Assert
        mock_event_publisher.publish.assert_called_once()
        call_args = mock_event_publisher.publish.call_args[0][0]
        assert isinstance(call_args, UserVerifiedEvent)
        assert call_args.user_id == "test_user"
        assert call_args.network == "ethereum"

    async def test_publish_event_retry_on_failure_then_success(self, verification_service, mock_event_publisher, mock_logger):
        # Arrange
        verification = UserVerification(
            user_id="test_user",
            network=NetworkType.ETHEREUM,
            document_hash="test_hash"
        )
        verification.verify()

        mock_event_publisher.publish.side_effect = [
            Exception("First attempt failed"),
            None  # Second attempt succeeds
        ]

        # Act
        with patch("asyncio.sleep") as mock_sleep:
            await verification_service._publish_event(verification)

        # Assert
        assert mock_event_publisher.publish.call_count == 2
        mock_sleep.assert_called_once_with(1)  # 2^0 = 1

    async def test_publish_event_all_attempts_fail_logs_error(self, verification_service, mock_event_publisher, mock_logger):
        # Arrange
        verification = UserVerification(
            user_id="test_user",
            network=NetworkType.ETHEREUM,
            document_hash="test_hash"
        )
        verification.verify()

        mock_event_publisher.publish.side_effect = Exception("Persistent failure")

        # Act
        with patch("asyncio.sleep") as mock_sleep:
            await verification_service._publish_event(verification)

        # Assert
        assert mock_event_publisher.publish.call_count == 3
        mock_sleep.assert_any_call(1)  # 2^0 = 1
        mock_sleep.assert_any_call(2)  # 2^1 = 2
        mock_logger.error.assert_called_once()
        assert "Failed to publish event after 3 attempts" in mock_logger.error.call_args[0][0]

    async def test_publish_event_retry_timing_exponential_backoff(self, verification_service, mock_event_publisher):
        # Arrange
        verification = UserVerification(
            user_id="test_user",
            network=NetworkType.ETHEREUM,
            document_hash="test_hash"
        )
        verification.verify()

        mock_event_publisher.publish.side_effect = [
            Exception("First failure"),
            Exception("Second failure"),
            Exception("Third failure")
        ]

        # Act
        with patch("asyncio.sleep") as mock_sleep:
            await verification_service._publish_event(verification)

        # Assert
        mock_sleep.assert_any_call(1)  # 2^0 = 1
        mock_sleep.assert_any_call(2)  # 2^1 = 2
        assert mock_sleep.call_count == 2

    async def test_semaphore_limits_concurrent_verifications(self, verification_service, mock_repository, valid_document_base64):
        # Arrange
        user_id = "test_user"
        network = "ethereum"
        mock_repository.get_by_user_and_network.return_value = None

        saved_verification = UserVerification(
            user_id=user_id,
            network=NetworkType.ETHEREUM,
            document_hash="test_hash"
        )
        saved_verification.id = uuid4()
        mock_repository.save.return_value = saved_verification

        # Act
        tasks = []
        for i in range(15):  # More than max_concurrent_verifications (10)
            task = asyncio.create_task(
                verification_service.verify_user(f"{user_id}_{i}", network, valid_document_base64)
            )
            tasks.append(task)

        results = await asyncio.gather(*tasks)

        # Assert
        assert len(results) == 15
        for result in results:
            assert result.status == VerificationStatus.VERIFIED

    async def test_verification_service_initialization(self, mock_repository, mock_event_publisher, test_settings, mock_logger):
        # Arrange & Act
        service = VerificationService(
            repository=mock_repository,
            event_publisher=mock_event_publisher,
            settings=test_settings,
            logger=mock_logger
        )

        # Assert
        assert service.repository == mock_repository
        assert service.event_publisher == mock_event_publisher
        assert service.settings == test_settings
        assert service.logger == mock_logger
        assert service._semaphore._value == test_settings.max_concurrent_verifications

    async def test_verify_user_with_empty_user_id(self, verification_service, mock_repository, valid_document_base64):
        # Arrange
        user_id = ""
        network = "ethereum"
        mock_repository.get_by_user_and_network.return_value = None

        saved_verification = UserVerification(
            user_id=user_id,
            network=NetworkType.ETHEREUM,
            document_hash="test_hash"
        )
        saved_verification.id = uuid4()
        mock_repository.save.return_value = saved_verification

        # Act
        result = await verification_service.verify_user(user_id, network, valid_document_base64)

        # Assert
        assert result.user_id == ""
        assert result.status == VerificationStatus.VERIFIED

    async def test_verify_user_with_minimal_document(self, verification_service, mock_repository):
        # Arrange
        user_id = "test_user"
        network = "ethereum"
        minimal_document = base64.b64encode(b"a").decode("utf-8")
        mock_repository.get_by_user_and_network.return_value = None

        saved_verification = UserVerification(
            user_id=user_id,
            network=NetworkType.ETHEREUM,
            document_hash=hashlib.sha256(b"a").hexdigest()
        )
        saved_verification.id = uuid4()
        mock_repository.save.return_value = saved_verification

        # Act
        result = await verification_service.verify_user(user_id, network, minimal_document)

        # Assert
        assert result.status == VerificationStatus.VERIFIED
        assert result.document_hash == hashlib.sha256(b"a").hexdigest()
