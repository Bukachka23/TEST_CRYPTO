from datetime import datetime, timedelta
from uuid import uuid4

from user_verification_service.src.domain.models.verification import (
    NetworkType,
    UserVerification,
    VerificationStatus,
)


class TestVerificationStatus:
    """Test cases for VerificationStatus enum."""

    def test_verification_status_values(self):
        # Arrange & Act & Assert
        assert VerificationStatus.PENDING == "pending"
        assert VerificationStatus.VERIFIED == "verified"
        assert VerificationStatus.FAILED == "failed"

    def test_verification_status_string_inheritance(self):
        # Arrange
        status = VerificationStatus.PENDING

        # Act & Assert
        assert isinstance(status, str)
        assert status == "pending"


class TestNetworkType:
    """Test cases for NetworkType enum."""

    def test_network_type_values(self):
        # Arrange & Act & Assert
        assert NetworkType.ETHEREUM == "ethereum"
        assert NetworkType.TRON == "tron"
        assert NetworkType.BITCOIN == "bitcoin"

    def test_network_type_string_inheritance(self):
        # Arrange
        network = NetworkType.ETHEREUM

        # Act & Assert
        assert isinstance(network, str)
        assert network == "ethereum"


class TestUserVerification:
    """Test cases for UserVerification domain model."""

    def test_user_verification_creation_with_required_fields(self):
        # Arrange
        user_id = "test_user_123"
        network = NetworkType.ETHEREUM
        document_hash = "abc123def456"

        # Act
        verification = UserVerification(
            user_id=user_id,
            network=network,
            document_hash=document_hash
        )

        # Assert
        assert verification.user_id == user_id
        assert verification.network == network
        assert verification.document_hash == document_hash
        assert verification.id is None
        assert verification.status == VerificationStatus.PENDING
        assert verification.verified_at is None
        assert isinstance(verification.created_at, datetime)

    def test_user_verification_creation_with_all_fields(self):
        # Arrange
        user_id = "test_user_456"
        network = NetworkType.TRON
        document_hash = "def456ghi789"
        verification_id = uuid4()
        status = VerificationStatus.VERIFIED
        verified_at = datetime.now()
        created_at = datetime.now() - timedelta(hours=1)

        # Act
        verification = UserVerification(
            user_id=user_id,
            network=network,
            document_hash=document_hash,
            id=verification_id,
            status=status,
            verified_at=verified_at,
            created_at=created_at
        )

        # Assert
        assert verification.user_id == user_id
        assert verification.network == network
        assert verification.document_hash == document_hash
        assert verification.id == verification_id
        assert verification.status == status
        assert verification.verified_at == verified_at
        assert verification.created_at == created_at

    def test_user_verification_default_created_at_is_recent(self):
        # Arrange
        before_creation = datetime.now()

        # Act
        verification = UserVerification(
            user_id="test_user",
            network=NetworkType.ETHEREUM,
            document_hash="hash123"
        )
        after_creation = datetime.now()

        # Assert
        assert before_creation <= verification.created_at <= after_creation

    def test_verify_method_updates_status_and_timestamp(self, valid_user_verification):
        # Arrange
        initial_status = valid_user_verification.status
        initial_verified_at = valid_user_verification.verified_at
        before_verify = datetime.now()

        # Act
        valid_user_verification.verify()
        after_verify = datetime.now()

        # Assert
        assert initial_status == VerificationStatus.PENDING
        assert initial_verified_at is None
        assert valid_user_verification.status == VerificationStatus.VERIFIED
        assert valid_user_verification.verified_at is not None
        assert before_verify <= valid_user_verification.verified_at <= after_verify

    def test_verify_method_on_already_verified_user(self, valid_user_verification):
        # Arrange
        valid_user_verification.verify()
        first_verified_at = valid_user_verification.verified_at

        # Act
        valid_user_verification.verify()
        second_verified_at = valid_user_verification.verified_at

        # Assert
        assert valid_user_verification.status == VerificationStatus.VERIFIED
        assert second_verified_at >= first_verified_at

    def test_verify_method_on_failed_verification(self, valid_user_verification):
        # Arrange
        valid_user_verification.fail()
        assert valid_user_verification.status == VerificationStatus.FAILED

        # Act
        valid_user_verification.verify()

        # Assert
        assert valid_user_verification.status == VerificationStatus.VERIFIED
        assert valid_user_verification.verified_at is not None

    def test_fail_method_updates_status_only(self, valid_user_verification):
        # Arrange
        initial_status = valid_user_verification.status
        initial_verified_at = valid_user_verification.verified_at

        # Act
        valid_user_verification.fail()

        # Assert
        assert initial_status == VerificationStatus.PENDING
        assert initial_verified_at is None
        assert valid_user_verification.status == VerificationStatus.FAILED
        assert valid_user_verification.verified_at is None

    def test_fail_method_on_verified_user(self, valid_user_verification):
        # Arrange
        valid_user_verification.verify()
        verified_at = valid_user_verification.verified_at

        # Act
        valid_user_verification.fail()

        # Assert
        assert valid_user_verification.status == VerificationStatus.FAILED
        assert valid_user_verification.verified_at == verified_at

    def test_fail_method_on_already_failed_verification(self, valid_user_verification):
        # Arrange
        valid_user_verification.fail()
        assert valid_user_verification.status == VerificationStatus.FAILED

        # Act
        valid_user_verification.fail()

        # Assert
        assert valid_user_verification.status == VerificationStatus.FAILED
        assert valid_user_verification.verified_at is None

    def test_user_verification_with_different_networks(self):
        # Arrange & Act
        ethereum_verification = UserVerification(
            user_id="user1",
            network=NetworkType.ETHEREUM,
            document_hash="hash1"
        )
        tron_verification = UserVerification(
            user_id="user1",
            network=NetworkType.TRON,
            document_hash="hash2"
        )
        bitcoin_verification = UserVerification(
            user_id="user1",
            network=NetworkType.BITCOIN,
            document_hash="hash3"
        )

        # Assert
        assert ethereum_verification.network == NetworkType.ETHEREUM
        assert tron_verification.network == NetworkType.TRON
        assert bitcoin_verification.network == NetworkType.BITCOIN

    def test_user_verification_dataclass_equality(self):
        # Arrange
        verification1 = UserVerification(
            user_id="user1",
            network=NetworkType.ETHEREUM,
            document_hash="hash1"
        )
        verification2 = UserVerification(
            user_id="user1",
            network=NetworkType.ETHEREUM,
            document_hash="hash1"
        )

        # Act & Assert
        assert verification1.user_id == verification2.user_id
        assert verification1.network == verification2.network
        assert verification1.document_hash == verification2.document_hash
        assert verification1.status == verification2.status

    def test_user_verification_with_empty_user_id(self):
        # Arrange & Act
        verification = UserVerification(
            user_id="",
            network=NetworkType.ETHEREUM,
            document_hash="hash123"
        )

        # Assert
        assert verification.user_id == ""
        assert verification.network == NetworkType.ETHEREUM

    def test_user_verification_with_empty_document_hash(self):
        # Arrange & Act
        verification = UserVerification(
            user_id="user123",
            network=NetworkType.ETHEREUM,
            document_hash=""
        )

        # Assert
        assert verification.user_id == "user123"
        assert verification.document_hash == ""

    def test_user_verification_state_transitions(self, valid_user_verification):
        # Arrange
        assert valid_user_verification.status == VerificationStatus.PENDING

        # Act & Assert: PENDING -> VERIFIED
        valid_user_verification.verify()
        assert valid_user_verification.status == VerificationStatus.VERIFIED
        assert valid_user_verification.verified_at is not None

        # Act & Assert: VERIFIED -> FAILED
        verified_at = valid_user_verification.verified_at
        valid_user_verification.fail()
        assert valid_user_verification.status == VerificationStatus.FAILED
        assert valid_user_verification.verified_at == verified_at

        # Act & Assert: FAILED -> VERIFIED
        valid_user_verification.verify()
        assert valid_user_verification.status == VerificationStatus.VERIFIED
        assert valid_user_verification.verified_at >= verified_at
