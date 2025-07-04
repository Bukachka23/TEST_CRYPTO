
from pydantic_settings import BaseSettings
from wallet_service.core.security import decrypt_mnemonic


class Settings(BaseSettings):
    """Configuration with security and performance settings."""

    app_name: str = "wallet-service"
    debug: bool = False
    api_version: str = "v1"

    mnemonic: str = "abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about"  # From environment variable
    mnemonic_encrypted: bool = False
    encryption_key: str | None = None

    # Database settings
    database_url: str = "postgresql+asyncpg://postgres:password@localhost:5432/wallet_service_db"
    db_pool_size: int = 30
    db_max_overflow: int = 10
    db_pool_pre_ping: bool = True
    db_pool_recycle: int = 3600
    db_echo: bool = False

    # Kafka settings
    kafka_bootstrap_servers: str = "localhost:9092"
    kafka_consumer_group: str = "wallet-service-group"
    kafka_topic_user_verified: str = "user.verified"
    kafka_topic_wallet_created: str = "wallet.created"

    # Kafka consumer config
    kafka_consumer_config: dict = {
        "auto_offset_reset": "earliest",
        "enable_auto_commit": False,
        "max_poll_records": 100,
        "session_timeout_ms": 30000,
        "heartbeat_interval_ms": 10000,
        "fetch_min_bytes": 1,
        "fetch_max_wait_ms": 500
    }

    # Kafka producer config
    kafka_producer_config: dict = {
        "acks": "all",
        "compression_type": "gzip",
        "max_batch_size": 16384,
        "linger_ms": 10,
        "enable_idempotence": True
    }

    # Cache settings
    cache_ttl_seconds: int = 3600
    cache_key_prefix: str = "wallet:"

    # Performance settings
    max_concurrent_generations: int = 50
    derivation_path_cache_size: int = 1000
    batch_processing_size: int = 10
    consumer_poll_timeout_ms: int = 1000

    # Crypto settings
    ethereum_derivation_path: str = "m/44'/60'/0'/0"
    bitcoin_derivation_path: str = "m/44'/0'/0'/0"
    tron_derivation_path: str = "m/44'/195'/0'/0"

    @classmethod
    def validate_mnemonic(cls, v):
        """Validate mnemonic phrase"""
        words = v.strip().split()
        if len(words) not in [12, 15, 18, 21, 24]:
            raise ValueError("Invalid mnemonic length")
        return v

    @property
    def decrypted_mnemonic(self) -> str:
        """Get decrypted mnemonic (cached)"""
        if not hasattr(self, "_decrypted_mnemonic"):
            if self.mnemonic_encrypted and self.encryption_key:
                self._decrypted_mnemonic = decrypt_mnemonic(
                    self.mnemonic,
                    self.encryption_key
                )
            else:
                self._decrypted_mnemonic = self.mnemonic
        return self._decrypted_mnemonic

    class Config:
        env_file = ".env"
        case_sensitive = False
