class WalletServiceException(Exception):
    """Base exception for wallet service"""

    status_code: int = 500
    detail: str = "Internal server error"


class WalletAlreadyExistsException(WalletServiceException):
    """Wallet already exists for this user and network."""

    status_code = 409
    detail = "Wallet already exists for this user and network"


class WalletNotFoundException(WalletServiceException):
    """Wallet not found."""

    status_code = 404
    detail = "Wallet not found"


class InvalidNetworkException(WalletServiceException):
    """Invalid or unsupported network."""

    status_code = 400
    detail = "Invalid or unsupported network"


class WalletGenerationException(WalletServiceException):
    """Failed to generate wallet."""

    status_code = 500
    detail = "Failed to generate wallet"


class MnemonicSecurityException(WalletServiceException):
    """Mnemonic security violation."""

    status_code = 500
    detail = "Mnemonic security violation"
