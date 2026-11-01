from sqlalchemy import Column, String, DateTime, Text
from sqlalchemy.sql import func
import uuid
from app.core.database import Base


class SourceSnapshot(Base):
    __tablename__ = "source_snapshots"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    source_url = Column(String, nullable=False, index=True)
    content_hash_old = Column(String, nullable=True)
    content_hash_new = Column(String, nullable=True)
    content_old = Column(Text, nullable=True)
    content_new = Column(Text, nullable=True)
    changed = Column(String, default="false")
    detected_at = Column(DateTime(timezone=True), server_default=func.now())
    processed = Column(String, default="false")
