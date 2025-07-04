from datetime import datetime

from pydantic import BaseModel


class WalletResponse(BaseModel):
    """API response schema"""

    user_id: str
    network: str
    wallet_address: str
    created_at: datetime

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}
