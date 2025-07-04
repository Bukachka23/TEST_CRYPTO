import base64

from pydantic import BaseModel, ConfigDict, Field, field_validator


class VerificationResponse(BaseModel):
    """Verification response."""

    message: str
    verification_id: str
    status: str


class VerificationRequest(BaseModel):
    """Verification request."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "user_id": "user_id",
                "network": "ethereum",
                "document": "iVBORw0KGgoAAAANSUhEUgAAAAUAAAAFCAYAAACNbyblAAAAHElEQVQI12P4//8/w38GIAXDIBKE0DHxgljNBAAO9TXL0Y4OHwAAAABJRU5ErkJggg=="
            }
        }
    )

    user_id: str = Field(..., min_length=1, max_length=255)
    network: str = Field(..., min_length=1)
    document: str = Field(..., description="Base64 encoded document")

    @field_validator("document")
    @classmethod
    def validate_document_base64(cls, v):
        try:
            base64.b64decode(v)
            return v
        except Exception:
            raise ValueError("Invalid base64 encoding")

    @field_validator("network")
    @classmethod
    def validate_network(cls, v):
        if v.lower() not in ["ethereum", "tron", "bitcoin"]:
            raise ValueError(f"Unsupported network: {v}")
        return v.lower()
