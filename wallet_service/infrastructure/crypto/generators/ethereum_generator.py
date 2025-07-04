import asyncio

from eth_account import Account
from eth_utils import to_checksum_address
from wallet_service.infrastructure.crypto.generators.base import BaseWalletGenerator


class EthereumWalletGenerator(BaseWalletGenerator):
    """Ethereum wallet generator using eth_account"""

    def __init__(self):
        super().__init__("m/44'/60'/0'/0")
        Account.enable_unaudited_hdwallet_features()

    async def generate_address(self, seed: bytes, path: str) -> str:
        """Generate Ethereum address"""
        loop = asyncio.get_event_loop()

        def generate():
            import hashlib
            derived_key = hashlib.sha256(seed + path.encode()).digest()
            account = Account.from_key(derived_key)
            return to_checksum_address(account.address)

        address = await loop.run_in_executor(None, generate)
        return address

    async def validate_address(self, address: str) -> bool:
        """Validate Ethereum address"""
        return address == to_checksum_address(address)
