from wallet_service.core.exceptions import InvalidNetworkException
from wallet_service.domain.interfaces.wallet_generator import IWalletGenerator
from wallet_service.domain.models.wallet import NetworkType
from wallet_service.infrastructure.crypto.generators.bitcoin_generator import (
    BitcoinWalletGenerator,
)
from wallet_service.infrastructure.crypto.generators.ethereum_generator import (
    EthereumWalletGenerator,
)
from wallet_service.infrastructure.crypto.generators.tron_generator import (
    TronWalletGenerator,
)


class WalletGeneratorFactory:
    """Factory for creating wallet generators."""

    def __init__(self) -> None:
        self._generators = {}
        self._generator_classes = {
            NetworkType.ETHEREUM: EthereumWalletGenerator,
            NetworkType.TRON: TronWalletGenerator,
            NetworkType.BITCOIN: BitcoinWalletGenerator
        }

    def get_generator(self, network: NetworkType) -> IWalletGenerator:
        """Get or create generator for network"""
        if network not in self._generators:
            generator_class = self._generator_classes.get(network)
            if not generator_class:
                raise InvalidNetworkException(f"No generator available for network: {network}")

            self._generators[network] = generator_class()

        return self._generators[network]
