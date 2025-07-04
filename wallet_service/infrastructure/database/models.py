from datetime import datetime
from uuid import uuid4

from sqlalchemy import Column, DateTime, Integer, String
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class WalletModel(Base):
    """Wallet database model."""
    __tablename__ = "wallets"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(String, nullable=False, index=True)
    network = Column(String, nullable=False, index=True)
    wallet_address = Column(String, nullable=False, unique=True)
    derivation_index = Column(Integer, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    last_accessed_at = Column(DateTime, nullable=True)
    version = Column(Integer, nullable=False, default=1)
