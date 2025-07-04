import asyncio

from eth_account.hdaccount import Mnemonic
from wallet_service.core.exceptions import WalletGenerationException
from wallet_service.domain.interfaces.wallet_generator import IWalletGenerator


class BaseWalletGenerator(IWalletGenerator):
    """Base class for wallet generators with common functionality"""

    def __init__(self, base_derivation_path: str):
        self.base_derivation_path = base_derivation_path
        self._path_cache = {}

    def get_derivation_path(self, index: int) -> str:
        """Get cached derivation path"""
        if index not in self._path_cache:
            self._path_cache[index] = f"{self.base_derivation_path}/{index}"
        return self._path_cache[index]

    async def generate(self, mnemonic: str, user_id: str, derivation_index: int) -> str:
        """Template method for wallet generation"""
        seed = await self._derive_seed(mnemonic, user_id)
        path = self.get_derivation_path(derivation_index)
        address = await self.generate_address(seed, path)

        if not await self.validate_address(address):
            raise WalletGenerationException(f"Generated invalid address: {address}")

        return address

    async def _derive_seed(self, mnemonic: str, user_id: str) -> bytes:
        """Derive seed with user-specific salt for security"""
        passphrase = f"wallet-service:{user_id}"

        loop = asyncio.get_event_loop()
        seed = await loop.run_in_executor(None, Mnemonic.to_seed, mnemonic, passphrase)
        return seed
