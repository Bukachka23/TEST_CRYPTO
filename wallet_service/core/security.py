import base64

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


def decrypt_mnemonic(encrypted_mnemonic: str, encryption_key: str) -> str:
    """Decrypt mnemonic with Fernet encryption."""
    kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=b"wallet-service-salt", iterations=100000)
    key = base64.urlsafe_b64encode(kdf.derive(encryption_key.encode()))

    f = Fernet(key)
    decrypted = f.decrypt(encrypted_mnemonic.encode())

    return decrypted.decode()
