from sqlalchemy import Column, String, Float, Integer, DateTime, ForeignKey, JSON, Boolean
from sqlalchemy.sql import func
import uuid
from app.core.database import Base


class ProfileFact(Base):
    __tablename__ = "profile_facts"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    field_name = Column(String, nullable=False)
    value = Column(String, nullable=False)
    source = Column(String, nullable=False)  # document_extracted, manually_entered, user_confirmed
    document_id = Column(String, ForeignKey("documents.id"), nullable=True)
    confidence = Column(Float, nullable=True)
    verified = Column(Boolean, default=False)
    page_number = Column(Integer, nullable=True)
    extraction_meta = Column(JSON, default={})
    expiry_date = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
