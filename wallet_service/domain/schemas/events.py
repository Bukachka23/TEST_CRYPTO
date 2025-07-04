from datetime import datetime

from pydantic import BaseModel, Field


class UserVerifiedEvent(BaseModel):
    """Incoming event schema"""

    event: str
    user_id: str
    network: str
    timestamp: datetime | None = None


class WalletCreatedEvent(BaseModel):
    """Outgoing event schema"""

    event: str = "wallet.created"
    user_id: str
    network: str
    wallet_address: str
    timestamp: datetime = Field(default_factory=datetime.now)

    def to_kafka_message(self) -> dict:
        """Convert to Kafka message format"""
        return {
            "key": f"{self.user_id}:{self.network}".encode(),
            "value": self.model_dump_json().encode("utf-8"),
            "headers": [
                ("event_type", b"wallet.created"),
                ("timestamp", str(self.timestamp.timestamp()).encode()),
                ("network", self.network.encode())
            ]
        }
