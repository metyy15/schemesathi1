from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.profile_fact import ProfileFact
from app.models.document import Document
from app.models.user import User
from datetime import datetime

router = APIRouter()


class ProfileFactCreate(BaseModel):
    field_name: str
    value: str
    source: str = "manually_entered"
    document_id: Optional[str] = None
    confidence: Optional[float] = None
    verified: bool = False
    expiry_date: Optional[datetime] = None


class ProfileFactUpdate(BaseModel):
    value: Optional[str] = None
    verified: Optional[bool] = None
    expiry_date: Optional[datetime] = None


@router.post("/facts")
def add_fact(
    fact: ProfileFactCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if fact.source == "document_extracted":
        # Document-derived facts must reference one of the citizen's documents.
        if not fact.document_id:
            raise HTTPException(
                status_code=400,
                detail="document_id is required for document-extracted facts",
            )
        owns = (
            db.query(Document)
            .filter(Document.id == fact.document_id, Document.user_id == current_user.id)
            .first()
        )
        if not owns:
            raise HTTPException(status_code=404, detail="Document not found")

    pf = ProfileFact(
        user_id=current_user.id,
        field_name=fact.field_name,
        value=fact.value,
        source=fact.source,
        document_id=fact.document_id,
        confidence=fact.confidence,
        verified=fact.verified,
        expiry_date=fact.expiry_date,
    )
    db.add(pf)
    db.commit()
    db.refresh(pf)
    return _fact_out(pf)


@router.get("/facts")
def get_facts(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    facts = (
        db.query(ProfileFact)
        .filter(ProfileFact.user_id == current_user.id)
        .order_by(ProfileFact.created_at.desc())
        .all()
    )
    return [_fact_out(f) for f in facts]


@router.patch("/facts/{fact_id}")
def update_fact(
    fact_id: str,
    payload: ProfileFactUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    pf = (
        db.query(ProfileFact)
        .filter(ProfileFact.id == fact_id, ProfileFact.user_id == current_user.id)
        .first()
    )
    if not pf:
        raise HTTPException(status_code=404, detail="Fact not found")

    if payload.value is not None:
        pf.value = payload.value
        pf.source = "manually_entered"
        pf.verified = False
    if payload.verified is not None:
        pf.verified = payload.verified
        if payload.verified:
            pf.source = "user_confirmed"
    if payload.expiry_date is not None:
        pf.expiry_date = payload.expiry_date

    db.commit()
    db.refresh(pf)
    return _fact_out(pf)


@router.post("/facts/{fact_id}/confirm")
def confirm_fact(
    fact_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Citizen explicitly confirms an extracted value. Until this happens the
    value is never used for matching."""
    pf = (
        db.query(ProfileFact)
        .filter(ProfileFact.id == fact_id, ProfileFact.user_id == current_user.id)
        .first()
    )
    if not pf:
        raise HTTPException(status_code=404, detail="Fact not found")
    pf.verified = True
    pf.source = "user_confirmed"
    pf.updated_at = datetime.utcnow()
    db.commit()
    return _fact_out(pf)


@router.delete("/facts/{fact_id}")
def delete_fact(
    fact_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    pf = (
        db.query(ProfileFact)
        .filter(ProfileFact.id == fact_id, ProfileFact.user_id == current_user.id)
        .first()
    )
    if not pf:
        raise HTTPException(status_code=404, detail="Fact not found")
    db.delete(pf)
    db.commit()
    return {"status": "deleted", "fact_id": fact_id}


def _fact_out(pf: ProfileFact) -> dict:
    return {
        "id": pf.id,
        "field_name": pf.field_name,
        "value": pf.value,
        "source": pf.source,
        "document_id": pf.document_id,
        "confidence": pf.confidence,
        "verified": pf.verified,
        "expiry_date": pf.expiry_date,
        "updated_at": pf.updated_at,
    }
