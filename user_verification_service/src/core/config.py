from pydantic import field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Configuration using Pydantic BaseSettings for validation and environment variable loading."""

    # Application settings
    app_name: str = "user_verification_service"
    debug: bool = False
    api_version: str = "v1"

    # Database settings
    database_url: str = "postgresql+asyncpg://postgres:password@localhost:5432/user_verification_db"
    db_pool_size: int = 20
    db_max_overflow: int = 0
    db_pool_pre_ping: bool = True
    db_echo: bool = False

    # Kafka settings
    kafka_bootstrap_servers: str = "localhost:9092"
    kafka_topic_user_verified: str = "user.verified"
    kafka_producer_config: dict = {
        "acks": "all",
        "compression_type": "gzip",
        "max_batch_size": 16384,
        "linger_ms": 10
    }

    # Performance settings
    verification_delay_seconds: float = 3.0
    max_concurrent_verifications: int = 100
    request_timeout_seconds: int = 30

    # Document processing
    max_document_size_mb: int = 10
    allowed_document_formats: list = ["jpg", "png", "pdf"]

    @field_validator("database_url")
    @classmethod
    def validate_database_url(cls, v):
        return v.replace("postgresql://", "postgresql+asyncpg://") if v.startswith("postgresql://") else v

    class Config:
        env_file = ".env"
        case_sensitive = False
