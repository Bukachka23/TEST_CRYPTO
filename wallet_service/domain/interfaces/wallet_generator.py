from abc import ABC, abstractmethod


class IWalletGenerator(ABC):
    """Interface for wallet generation"""

    @abstractmethod
    async def generate(self, mnemonic: str, user_id: str, derivation_index: int) -> str:
        """Generate wallet address"""

    @abstractmethod
    def get_derivation_path(self, index: int) -> str:
        """Get derivation path for index"""

    @abstractmethod
    async def validate_address(self, address: str) -> bool:
        """Validate address format"""

    @abstractmethod
    async def generate_address(self, seed: bytes, path: str) -> str:
        """Generate address from seed and path"""
