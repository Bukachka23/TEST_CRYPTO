from datetime import datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from user_verification_service.src.domain.models.verification import NetworkType, UserVerification, VerificationStatus
from user_verification_service.src.infrastructure.database.models import VerificationModel
from user_verification_service.src.infrastructure.repositories.verification_repository import VerificationRepository


class TestVerificationRepository:
    """Test cases for VerificationRepository."""

    def test_repository_initialization(self, mock_async_session):
        """Test that repository initializes correctly with session."""
        # Arrange & Act
        repository = VerificationRepository(mock_async_session)

        # Assert
        assert repository.session == mock_async_session

    async def test_save_verification_successfully(self, verification_repository, mock_async_session, valid_user_verification):
        """Test saving a new verification to database."""
        # Arrange
        expected_id = uuid4()

        def mock_add(db_verification):
            db_verification.id = expected_id

        mock_async_session.add = MagicMock(side_effect=mock_add)
        mock_async_session.flush = AsyncMock()

        # Act
        result = await verification_repository.save(valid_user_verification)

        # Assert
        assert result.id == expected_id
        assert result.user_id == valid_user_verification.user_id
        assert result.network == valid_user_verification.network
        assert result.document_hash == valid_user_verification.document_hash
        mock_async_session.add.assert_called_once()
        mock_async_session.flush.assert_called_once()

    async def test_save_verification_creates_correct_database_model(self, verification_repository, mock_async_session, valid_user_verification):
        """Test that save creates VerificationModel with correct attributes."""
        # Arrange
        expected_id = uuid4()

        def mock_add(db_verification):
            db_verification.id = expected_id

        mock_async_session.add = MagicMock(side_effect=mock_add)
        mock_async_session.flush = AsyncMock()

        # Act
        await verification_repository.save(valid_user_verification)

        # Assert
        mock_async_session.add.assert_called_once()
        added_model = mock_async_session.add.call_args[0][0]
        assert isinstance(added_model, VerificationModel)
        assert added_model.user_id == valid_user_verification.user_id
        assert added_model.network == valid_user_verification.network.value
        assert added_model.document_hash == valid_user_verification.document_hash
        assert added_model.status == valid_user_verification.status.value
        assert added_model.verified_at == valid_user_verification.verified_at
        assert added_model.created_at == valid_user_verification.created_at

    async def test_save_verification_with_verified_status(self, verification_repository, mock_async_session, valid_user_verification):
        """Test saving verification with verified status."""
        # Arrange
        valid_user_verification.verify()
        expected_id = uuid4()

        def mock_add(db_verification):
            db_verification.id = expected_id

        mock_async_session.add = MagicMock(side_effect=mock_add)
        mock_async_session.flush = AsyncMock()

        # Act
        result = await verification_repository.save(valid_user_verification)

        # Assert
        added_model = mock_async_session.add.call_args[0][0]
        assert added_model.status == VerificationStatus.VERIFIED.value
        assert added_model.verified_at == valid_user_verification.verified_at
        assert result.status == VerificationStatus.VERIFIED
        assert result.id == expected_id

    async def test_save_verification_database_error_propagates(self, verification_repository, mock_async_session, valid_user_verification):
        """Test that database errors during save are propagated."""
        # Arrange
        mock_async_session.add = MagicMock()
        mock_async_session.flush = AsyncMock(side_effect=Exception("Database error"))

        # Act & Assert
        with pytest.raises(Exception, match="Database error"):
            await verification_repository.save(valid_user_verification)

    async def test_get_by_user_and_network_found(self, verification_repository, mock_async_session, verification_model):
        """Test retrieving existing verification by user and network."""
        # Arrange
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = verification_model
        mock_async_session.execute = AsyncMock(return_value=mock_result)

        # Act
        result = await verification_repository.get_by_user_and_network("test_user_123", "ethereum")

        # Assert
        assert result is not None
        assert result.user_id == "test_user_123"
        assert result.network == NetworkType.ETHEREUM
        assert result.document_hash == "abc123def456"
        assert result.status == VerificationStatus.PENDING
        mock_async_session.execute.assert_called_once()

    async def test_get_by_user_and_network_not_found(self, verification_repository, mock_async_session):
        """Test retrieving non-existent verification returns None."""
        # Arrange
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_async_session.execute = AsyncMock(return_value=mock_result)

        # Act
        result = await verification_repository.get_by_user_and_network("nonexistent_user", "ethereum")

        # Assert
        assert result is None
        mock_async_session.execute.assert_called_once()

    async def test_get_by_user_and_network_query_structure(self, verification_repository, mock_async_session):
        """Test that get_by_user_and_network constructs correct SQL query."""
        # Arrange
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_async_session.execute = AsyncMock(return_value=mock_result)

        # Act
        await verification_repository.get_by_user_and_network("test_user", "bitcoin")

        # Assert
        mock_async_session.execute.assert_called_once()
        call_args = mock_async_session.execute.call_args[0][0]
        assert hasattr(call_args, "whereclause")

    async def test_get_by_user_and_network_database_error_propagates(self, verification_repository, mock_async_session):
        """Test that database errors during get are propagated."""
        # Arrange
        mock_async_session.execute = AsyncMock(side_effect=Exception("Database connection error"))

        # Act & Assert
        with pytest.raises(Exception, match="Database connection error"):
            await verification_repository.get_by_user_and_network("test_user", "ethereum")

    async def test_update_status_successfully(self, verification_repository, mock_async_session):
        """Test updating verification status successfully."""
        # Arrange
        verification_id = uuid4()
        new_status = VerificationStatus.VERIFIED
        mock_async_session.execute = AsyncMock()

        # Act
        await verification_repository.update_status(verification_id, new_status)

        # Assert
        mock_async_session.execute.assert_called_once()
        call_args = mock_async_session.execute.call_args[0][0]
        assert hasattr(call_args, "table")

    async def test_update_status_with_different_statuses(self, verification_repository, mock_async_session):
        """Test updating verification with different status values."""
        # Arrange
        verification_id = uuid4()
        statuses = [VerificationStatus.PENDING, VerificationStatus.VERIFIED, VerificationStatus.FAILED]
        mock_async_session.execute = AsyncMock()

        for status in statuses:
            # Act
            await verification_repository.update_status(verification_id, status)

            # Assert
            mock_async_session.execute.assert_called()

    async def test_update_status_database_error_propagates(self, verification_repository, mock_async_session):
        """Test that database errors during update are propagated."""
        # Arrange
        verification_id = uuid4()
        mock_async_session.execute = AsyncMock(side_effect=Exception("Update failed"))

        # Act & Assert
        with pytest.raises(Exception, match="Update failed"):
            await verification_repository.update_status(verification_id, VerificationStatus.VERIFIED)

    def test_to_domain_conversion_complete_model(self, verification_repository, verified_verification_model):
        """Test converting complete database model to domain model."""
        # Arrange
        # verified_verification_model fixture provides complete model

        # Act
        result = verification_repository._to_domain(verified_verification_model)

        # Assert
        assert isinstance(result, UserVerification)
        assert result.id == verified_verification_model.id
        assert result.user_id == verified_verification_model.user_id
        assert result.network == NetworkType(verified_verification_model.network)
        assert result.document_hash == verified_verification_model.document_hash
        assert result.status == VerificationStatus(verified_verification_model.status)
        assert result.verified_at == verified_verification_model.verified_at
        assert result.created_at == verified_verification_model.created_at

    def test_to_domain_conversion_minimal_model(self, verification_repository, verification_model):
        """Test converting minimal database model to domain model."""
        # Arrange
        # verification_model fixture provides minimal model

        # Act
        result = verification_repository._to_domain(verification_model)

        # Assert
        assert isinstance(result, UserVerification)
        assert result.id == verification_model.id
        assert result.user_id == verification_model.user_id
        assert result.network == NetworkType(verification_model.network)
        assert result.document_hash == verification_model.document_hash
        assert result.status == VerificationStatus(verification_model.status)
        assert result.verified_at is None
        assert result.created_at == verification_model.created_at

    def test_to_domain_conversion_all_network_types(self, verification_repository):
        """Test converting models with different network types."""
        # Arrange
        networks = ["ethereum", "bitcoin", "tron"]

        for network in networks:
            db_model = VerificationModel(
                id=uuid4(),
                user_id="test_user",
                network=network,
                document_hash="hash123",
                status="pending",
                verified_at=None,
                created_at=datetime.now(),
                version=1
            )

            # Act
            result = verification_repository._to_domain(db_model)

            # Assert
            assert result.network == NetworkType(network)

    def test_to_domain_conversion_all_status_types(self, verification_repository):
        """Test converting models with different status types."""
        # Arrange
        statuses = ["pending", "verified", "failed"]

        for status in statuses:
            db_model = VerificationModel(
                id=uuid4(),
                user_id="test_user",
                network="ethereum",
                document_hash="hash123",
                status=status,
                verified_at=None,
                created_at=datetime.now(),
                version=1
            )

            # Act
            result = verification_repository._to_domain(db_model)

            # Assert
            assert result.status == VerificationStatus(status)

    def test_to_domain_conversion_with_special_characters(self, verification_repository):
        """Test converting model with special characters in fields."""
        # Arrange
        db_model = VerificationModel(
            id=uuid4(),
            user_id="user@example.com",
            network="ethereum",
            document_hash="abc123!@#$%^&*()",
            status="pending",
            verified_at=None,
            created_at=datetime.now(),
            version=1
        )

        # Act
        result = verification_repository._to_domain(db_model)

        # Assert
        assert result.user_id == "user@example.com"
        assert result.document_hash == "abc123!@#$%^&*()"

    async def test_get_by_user_and_network_with_special_characters(self, verification_repository, mock_async_session):
        """Test retrieving verification with special characters in user_id."""
        # Arrange
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_async_session.execute = AsyncMock(return_value=mock_result)

        # Act
        result = await verification_repository.get_by_user_and_network("user@domain.com", "ethereum")

        # Assert
        assert result is None
        mock_async_session.execute.assert_called_once()

    async def test_save_verification_preserves_original_object(self, verification_repository, mock_async_session, valid_user_verification):
        """Test that save operation doesn't modify original verification object except for ID."""
        # Arrange
        original_user_id = valid_user_verification.user_id
        original_network = valid_user_verification.network
        original_document_hash = valid_user_verification.document_hash
        original_status = valid_user_verification.status
        original_verified_at = valid_user_verification.verified_at
        original_created_at = valid_user_verification.created_at

        expected_id = uuid4()

        def mock_add(db_verification):
            db_verification.id = expected_id

        mock_async_session.add = MagicMock(side_effect=mock_add)
        mock_async_session.flush = AsyncMock()

        # Act
        result = await verification_repository.save(valid_user_verification)

        # Assert
        assert valid_user_verification.user_id == original_user_id
        assert valid_user_verification.network == original_network
        assert valid_user_verification.document_hash == original_document_hash
        assert valid_user_verification.status == original_status
        assert valid_user_verification.verified_at == original_verified_at
        assert valid_user_verification.created_at == original_created_at
        assert result.id == expected_id

    async def test_repository_handles_empty_strings(self, verification_repository, mock_async_session):
        """Test repository handles empty string values correctly."""
        # Arrange
        verification = UserVerification(
            user_id="",
            network=NetworkType.ETHEREUM,
            document_hash=""
        )
        expected_id = uuid4()

        def mock_add(db_verification):
            db_verification.id = expected_id

        mock_async_session.add = MagicMock(side_effect=mock_add)
        mock_async_session.flush = AsyncMock()

        # Act
        result = await verification_repository.save(verification)

        # Assert
        added_model = mock_async_session.add.call_args[0][0]
        assert added_model.user_id == ""
        assert added_model.document_hash == ""
        assert result.user_id == ""
        assert result.document_hash == ""
        assert result.id == expected_id
