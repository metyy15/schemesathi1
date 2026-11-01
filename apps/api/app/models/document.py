from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, JSON
from sqlalchemy.sql import func
import uuid
from app.core.database import Base


class Document(Base):
    __tablename__ = "documents"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    filename = Column(String, nullable=False)
    document_type = Column(String, nullable=True)  # income_certificate, domicile, marksheet, etc.
    storage_key = Column(String, nullable=False)
    mime_type = Column(String, nullable=True)
    file_size = Column(Integer, nullable=True)
    status = Column(String, default="uploaded")  # uploaded, processing, processed, failed
    retention_date = Column(DateTime(timezone=True), nullable=True)
    # Named `extra` because `metadata` is reserved by SQLAlchemy's declarative base.
    extra = Column(JSON, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    processed_at = Column(DateTime(timezone=True), nullable=True)
