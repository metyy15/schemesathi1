from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.core.config import settings
from app.core.deps import get_current_user
from app.models.document import Document
from app.models.consent import Consent
from app.models.user import User
import os
import aiofiles
import uuid
from datetime import datetime, timedelta

router = APIRouter()

ALLOWED_MIME = {"application/pdf", "image/jpeg", "image/png", "image/jpg"}
ALLOWED_EXT = {".pdf", ".jpg", ".jpeg", ".png"}

# Extracted from the file extension, not the client-supplied MIME type.
EXT_MIME = {
    ".pdf": "application/pdf",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
}

DOCUMENT_TYPES = [
    "income_certificate",
    "domicile_certificate",
    "marksheet",
    "disability_certificate",
    "landholding_record",
    "bank_passbook",
    "aadhaar",
    "other",
]


def _has_consent(db: Session, user_id: str, purpose: str) -> bool:
    consent = (
        db.query(Consent)
        .filter(
            Consent.user_id == user_id,
            Consent.purpose == purpose,
            Consent.granted.is_(True),
        )
        .order_by(Consent.granted_at.desc())
        .first()
    )
    return consent is not None


@router.post("/upload")
async def upload_document(
    document_type: str = Form("other"),
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Upload a document into private storage. Requires the citizen to have
    granted the 'document_upload' consent purpose first."""
    if not _has_consent(db, current_user.id, "document_upload"):
        raise HTTPException(
            status_code=403,
            detail=(
                "Consent required. Please grant the document upload consent "
                "before uploading certificates."
            ),
        )

    if document_type not in DOCUMENT_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported document_type. Allowed: {', '.join(DOCUMENT_TYPES)}",
        )

    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in ALLOWED_EXT:
        raise HTTPException(
            status_code=400,
            detail="Unsupported file type. Only PDF, JPG and PNG are accepted.",
        )
    mime = EXT_MIME[ext]
    if file.content_type and file.content_type not in ALLOWED_MIME:
        raise HTTPException(
            status_code=400,
            detail="Unsupported content type. Only PDF, JPG and PNG are accepted.",
        )

    content = await file.read()
    max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    if len(content) > max_bytes:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum size is {settings.MAX_UPLOAD_SIZE_MB} MB.",
        )
    if not content:
        raise HTTPException(status_code=400, detail="Empty file.")

    os.makedirs(settings.LOCAL_STORAGE_DIR, exist_ok=True)
    storage_key = f"{current_user.id}/{uuid.uuid4()}{ext}"
    file_path = os.path.join(settings.LOCAL_STORAGE_DIR, storage_key)
    os.makedirs(os.path.dirname(file_path), exist_ok=True)

    async with aiofiles.open(file_path, "wb") as out_file:
        await out_file.write(content)

    doc = Document(
        user_id=current_user.id,
        filename=file.filename,
        document_type=document_type,
        storage_key=storage_key,
        mime_type=mime,
        file_size=len(content),
        status="uploaded",
        retention_date=datetime.utcnow() + timedelta(days=365),
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    return {
        "document_id": doc.id,
        "status": doc.status,
        "filename": doc.filename,
        "document_type": doc.document_type,
        "size_bytes": doc.file_size,
        "retention_date": doc.retention_date,
    }


@router.get("/mine")
def list_my_documents(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    docs = (
        db.query(Document)
        .filter(Document.user_id == current_user.id)
        .order_by(Document.created_at.desc())
        .all()
    )
    return [
        {
            "id": d.id,
            "filename": d.filename,
            "document_type": d.document_type,
            "status": d.status,
            "size_bytes": d.file_size,
            "created_at": d.created_at,
            "processed_at": d.processed_at,
            "retention_date": d.retention_date,
        }
        for d in docs
    ]


@router.delete("/{document_id}")
def delete_document(
    document_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Remove a document from storage and the database (right to erasure)."""
    doc = (
        db.query(Document)
        .filter(Document.id == document_id, Document.user_id == current_user.id)
        .first()
    )
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    file_path = os.path.join(settings.LOCAL_STORAGE_DIR, doc.storage_key)
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
    except Exception:
        pass  # File already gone is fine.

    db.delete(doc)
    db.commit()
    return {"status": "deleted", "document_id": document_id}
