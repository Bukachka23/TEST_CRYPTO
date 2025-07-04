from datetime import datetime

from pydantic import BaseModel, Field


class UserVerifiedEvent(BaseModel):
    """User verified event."""

    event: str = "user.verified"
    user_id: str
    network: str
    timestamp: datetime = Field(default_factory=datetime.now)

    def to_kafka_message(self) -> dict:
        """Convert event to kafka message."""
        return {
            "key": self.user_id.encode("utf-8"),
            "value": self.model_dump_json().encode("utf-8"),
            "headers": [
                ("event_type", b"user.verified"),
                ("timestamp", str(self.timestamp.timestamp()).encode())
            ]
        }
