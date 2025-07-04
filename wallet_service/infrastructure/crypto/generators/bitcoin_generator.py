import asyncio

from bitcoinlib.keys import HDKey

from wallet_service.core.base import CryptoConfigs
from wallet_service.infrastructure.crypto.generators.base import BaseWalletGenerator


class BitcoinWalletGenerator(BaseWalletGenerator):
    """Bitcoin wallet generator using bitcoinlib"""

    def __init__(self):
        super().__init__("m/44'/0'/0'/0")

    async def generate_address(self, seed: bytes, path: str) -> str:
        """Generate Bitcoin address"""
        loop = asyncio.get_event_loop()

        def generate():
            hd_key = HDKey.from_seed(seed)
            child_key = hd_key.derive_path(path)
            address = child_key.address()

            return address

        address = await loop.run_in_executor(None, generate)
        return address

    async def validate_address(self, address: str) -> bool:
        """Validate Bitcoin address"""
        if len(address) < 26 or len(address) > 35:
            return False

        valid_chars = CryptoConfigs.valid_chars
        return all(c in valid_chars for c in address)
