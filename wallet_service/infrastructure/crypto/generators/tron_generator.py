import asyncio
import hashlib

from tronpy import Tron
from tronpy.keys import PrivateKey
from wallet_service.infrastructure.crypto.generators.base import BaseWalletGenerator


class TronWalletGenerator(BaseWalletGenerator):
    """Tron wallet generator using tronpy"""

    def __init__(self):
        super().__init__("m/44'/195'/0'/0")
        self.tron = Tron()

    async def generate_address(self, seed: bytes, path: str) -> str:
        """Generate Tron address"""
        loop = asyncio.get_event_loop()

        def generate():
            derived_seed = hashlib.sha256(seed + path.encode()).digest()

            private_key = PrivateKey(derived_seed)
            address = private_key.public_key.to_base58check_address()

            return address

        address = await loop.run_in_executor(None, generate)
        return address

    async def validate_address(self, address: str) -> bool:
        """Validate Tron address"""
        return address.startswith("T") and len(address) == 34 and self.tron.is_address(address)
