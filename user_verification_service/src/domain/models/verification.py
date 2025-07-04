from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from uuid import UUID


class VerificationStatus(str, Enum):
    """User verification status."""

    PENDING = "pending"
    VERIFIED = "verified"
    FAILED = "failed"


class NetworkType(str, Enum):
    """Supported networks."""

    ETHEREUM = "ethereum"
    TRON = "tron"
    BITCOIN = "bitcoin"


@dataclass
class UserVerification:
    """Domain model for user verification"""

    user_id: str
    network: NetworkType
    document_hash: str
    id: UUID | None = None
    status: VerificationStatus = VerificationStatus.PENDING
    verified_at: datetime | None = None
    created_at: datetime = field(default_factory=datetime.now)

    def verify(self):
        """Domain logic for verification"""
        self.status = VerificationStatus.VERIFIED
        self.verified_at = datetime.now()

    def fail(self):
        """Domain logic for failed verification"""
        self.status = VerificationStatus.FAILED
