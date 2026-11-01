from sqlalchemy import Column, String, Float, DateTime, ForeignKey, Text, JSON
from sqlalchemy.sql import func
import uuid
from app.core.database import Base


class EligibilityResult(Base):
    __tablename__ = "eligibility_results"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    scheme_id = Column(String, nullable=False, index=True)
    outcome = Column(String, nullable=False)  # potentially_eligible, needs_more_info, likely_not_eligible
    match_score = Column(Float, nullable=True)
    explanation = Column(Text, nullable=True)
    condition_results = Column(JSON, default=[])  # detailed breakdown
    evaluated_at = Column(DateTime(timezone=True), server_default=func.now())
    meta = Column(JSON, default={})
