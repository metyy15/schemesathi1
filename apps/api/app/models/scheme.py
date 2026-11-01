from sqlalchemy import Column, String, DateTime, JSON, Text, Boolean
from sqlalchemy.sql import func
import uuid
from app.core.database import Base


class Scheme(Base):
    __tablename__ = "schemes"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    scheme_id_external = Column(String, nullable=True, index=True)
    name = Column(String, nullable=False)
    scope = Column(String, nullable=True)  # central, state, district
    state = Column(String, nullable=True)
    ministry_department = Column(String, nullable=True)
    benefit_description = Column(Text, nullable=True)
    benefit_amount = Column(String, nullable=True)
    application_url = Column(String, nullable=True)
    official_source_url = Column(String, nullable=False)
    required_documents = Column(JSON, default=[])
    application_opening = Column(DateTime(timezone=True), nullable=True)
    application_closing = Column(DateTime(timezone=True), nullable=True)
    source_confidence = Column(String, default="medium")
    verification_status = Column(String, default="needs_verification")
    # Trust tier of the page this record was read from:
    #   official | community | unverified
    source_tier = Column(String, default="official")
    source_tier_label = Column(String, nullable=True)
    source_url = Column(String, nullable=True)  # page actually read
    official_application_confirmed = Column(Boolean, default=False)
    review_note = Column(Text, nullable=True)
    last_checked = Column(DateTime(timezone=True), server_default=func.now())
    extra = Column(JSON, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class SchemeCondition(Base):
    __tablename__ = "scheme_conditions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    scheme_id = Column(String, nullable=False, index=True)
    condition_type = Column(String, nullable=False)  # income, state, education, age, etc.
    operator = Column(String, nullable=False)  # ==, <=, >=, in, etc.
    value = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    evidence_url = Column(String, nullable=True)
    evidence_excerpt = Column(Text, nullable=True)
    evidence_tier = Column(String, default="official")
    is_required = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
