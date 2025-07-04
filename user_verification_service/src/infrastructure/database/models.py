from datetime import datetime
from uuid import uuid4

from sqlalchemy import Column, DateTime, Integer, String
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class VerificationModel(Base):
    __tablename__ = "verifications"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(String, nullable=False, index=True)
    network = Column(String, nullable=False, index=True)
    document_hash = Column(String, nullable=False)
    status = Column(String, nullable=False, default="pending")
    verified_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    version = Column(Integer, nullable=False, default=1)

    class Config:
        use_enum_values = True
