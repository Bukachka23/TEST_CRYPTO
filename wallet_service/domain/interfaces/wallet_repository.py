from abc import ABC, abstractmethod
from uuid import UUID

from wallet_service.domain.models.wallet import Wallet


class IWalletRepository(ABC):
    """Repository interface for wallets"""

    @abstractmethod
    async def create(self, wallet: Wallet) -> Wallet:
        """Create new wallet"""

    @abstractmethod
    async def get_by_user_and_network(self, user_id: str, network: str) -> Wallet | None:
        """Get wallet by user and network"""

    @abstractmethod
    async def get_next_derivation_index(self, network: str) -> int:
        """Get next available derivation index"""

    @abstractmethod
    async def exists(self, user_id: str, network: str) -> bool:
        """Check if wallet exists"""

    @abstractmethod
    async def update_last_accessed(self, wallet_id: UUID) -> None:
        """Update last accessed timestamp"""
