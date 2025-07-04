import hashlib
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from uuid import UUID


class NetworkType(str, Enum):
    """Supported networks."""

    ETHEREUM = "ethereum"
    TRON = "tron"
    BITCOIN = "bitcoin"


@dataclass
class Wallet:
    """Domain model for wallet"""

    user_id: str
    network: NetworkType
    wallet_address: str
    derivation_index: int
    id: UUID | None = None
    created_at: datetime = field(default_factory=datetime.now)
    last_accessed_at: datetime | None = None

    _address_checksum: str | None = None
    _derivation_path: str | None = None

    def __post_init__(self):
        """Validate wallet on creation"""
        self._validate_address()
        self._generate_checksum()

    def _validate_address(self):
        """Validate address format based on network"""
        validators = {
            NetworkType.ETHEREUM: self._validate_ethereum_address,
            NetworkType.TRON: self._validate_tron_address,
            NetworkType.BITCOIN: self._validate_bitcoin_address
        }

        validator = validators.get(self.network)
        if validator and not validator():
            raise ValueError(f"Invalid {self.network} address format")

    def _validate_ethereum_address(self) -> bool:
        """Validate Ethereum address format"""
        return (
                self.wallet_address.startswith("0x") and
                len(self.wallet_address) == 42
        )

    def _validate_tron_address(self) -> bool:
        """Validate Tron address format"""
        return (
                self.wallet_address.startswith("T") and
                len(self.wallet_address) == 34
        )

    def _validate_bitcoin_address(self) -> bool:
        """Validate Bitcoin address format"""
        return 26 <= len(self.wallet_address) <= 35

    def _generate_checksum(self):
        """Generate address checksum for integrity"""
        self._address_checksum = (hashlib.sha256(f"{self.user_id}:{self.network}:{self.wallet_address}".encode())
                                  .hexdigest())
