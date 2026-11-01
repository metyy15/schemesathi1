from sqlalchemy import Column, String, DateTime, Text, JSON
from sqlalchemy.sql import func
import uuid
from app.core.database import Base


class SourceEvidence(Base):
    __tablename__ = "source_evidence"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    scheme_id = Column(String, nullable=True, index=True)
    url = Column(String, nullable=False)
    page_title = Column(String, nullable=True)
    source_tier = Column(String, default="official")
    source_tier_label = Column(String, nullable=True)
    retrieved_at = Column(DateTime(timezone=True), server_default=func.now())
    content_snapshot = Column(Text, nullable=True)
    excerpt = Column(Text, nullable=True)
    content_hash = Column(String, nullable=True)
    meta = Column(JSON, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())
