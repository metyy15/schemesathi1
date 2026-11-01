from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.consent import Consent
from app.models.user import User
from datetime import datetime

router = APIRouter()

CONSENT_VERSION = "1.0"

# Purposes a citizen can grant. Each maps to a concrete processing activity.
CONSENT_PURPOSES = {
    "document_upload": "Upload and read your certificates to extract profile facts",
    "ocr_processing": "Run text extraction (OCR) on the documents you upload",
    "profile_building": "Store the facts you confirm so we can match schemes",
    "scheme_monitoring": "Periodically re-check official sources for changes that affect you",
    "notifications": "Send you alerts about new schemes and deadline changes",
}


class ConsentRequest(BaseModel):
    purpose: str
    version: str = CONSENT_VERSION


@router.get("/purposes")
def list_purposes():
    return {
        "version": CONSENT_VERSION,
        "purposes": [
            {"purpose": key, "description": value}
            for key, value in CONSENT_PURPOSES.items()
        ],
    }


@router.get("/mine")
def my_consents(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    consents = (
        db.query(Consent)
        .filter(Consent.user_id == current_user.id)
        .order_by(Consent.created_at.desc())
        .all()
    )
    return [
        {
            "id": c.id,
            "purpose": c.purpose,
            "description": CONSENT_PURPOSES.get(c.purpose, c.purpose),
            "version": c.version,
            "granted": c.granted,
            "granted_at": c.granted_at,
            "withdrawn_at": c.withdrawn_at,
        }
        for c in consents
    ]


@router.post("/grant")
def grant_consent(
    req: ConsentRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if req.purpose not in CONSENT_PURPOSES:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown consent purpose. Allowed: {', '.join(CONSENT_PURPOSES)}",
        )

    existing = (
        db.query(Consent)
        .filter(
            Consent.user_id == current_user.id,
            Consent.purpose == req.purpose,
            Consent.version == req.version,
            Consent.granted.is_(True),
        )
        .order_by(Consent.granted_at.desc())
        .first()
    )
    if existing:
        return {"status": "granted", "consent_id": existing.id, "already": True}

    consent = Consent(
        user_id=current_user.id,
        purpose=req.purpose,
        version=req.version,
        granted=True,
        granted_at=datetime.utcnow(),
    )
    db.add(consent)
    db.commit()
    db.refresh(consent)
    return {"status": "granted", "consent_id": consent.id, "already": False}


@router.post("/withdraw")
def withdraw_consent(
    consent_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    consent = (
        db.query(Consent)
        .filter(Consent.id == consent_id, Consent.user_id == current_user.id)
        .first()
    )
    if not consent:
        raise HTTPException(status_code=404, detail="Consent not found")
    consent.granted = False
    consent.withdrawn_at = datetime.utcnow()
    db.commit()
    return {"status": "withdrawn", "consent_id": consent_id}


@router.post("/withdraw-purpose")
def withdraw_by_purpose(
    purpose: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Withdraw every active consent of a given purpose."""
    consents = (
        db.query(Consent)
        .filter(
            Consent.user_id == current_user.id,
            Consent.purpose == purpose,
            Consent.granted.is_(True),
        )
        .all()
    )
    for c in consents:
        c.granted = False
        c.withdrawn_at = datetime.utcnow()
    db.commit()
    return {"status": "withdrawn", "count": len(consents), "purpose": purpose}
