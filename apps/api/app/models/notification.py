from sqlalchemy import Column, String, DateTime, ForeignKey, Text, JSON
from sqlalchemy.sql import func
import uuid
from app.core.database import Base


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    type = Column(String, nullable=False)  # new_scheme, rule_change, deadline, document_expiry
    title = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    data = Column(JSON, default={})
    read = Column(String, default="false")
    delivery_status = Column(JSON, default={"in_app": "sent"})
    created_at = Column(DateTime(timezone=True), server_default=func.now())
