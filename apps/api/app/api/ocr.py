from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
import os

from app.core.database import get_db
from app.core.config import settings
from app.core.deps import get_current_user
from app.models.document import Document
from app.models.user import User
from app.services.ocr_service import ocr_service

router = APIRouter()


@router.post("/process/{document_id}")
async def process_document(
    document_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Run OCR / text extraction on one of the citizen's own documents."""
    doc = (
        db.query(Document)
        .filter(Document.id == document_id, Document.user_id == current_user.id)
        .first()
    )
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    file_path = os.path.join(settings.LOCAL_STORAGE_DIR, doc.storage_key)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found in storage")

    doc.status = "processing"
    db.commit()

    if doc.mime_type == "application/pdf":
        result = await ocr_service.extract_from_pdf(file_path)
    else:
        result = await ocr_service.extract_from_image(file_path)

    if result.get("error"):
        doc.status = "failed"
        db.commit()
        raise HTTPException(
            status_code=500,
            detail=f"Text extraction failed: {result['error']}",
        )

    doc.status = "processed"
    doc.processed_at = datetime.utcnow()
    doc.extra = {
        **(doc.extra or {}),
        "ocr_engine": result.get("engine"),
        "extracted_fields": result.get("fields", {}),
        "text_length": len(result.get("text", "")),
    }
    db.commit()

    return {
        "document_id": doc.id,
        "status": doc.status,
        "extracted_text": result.get("text", ""),
        "suggested_fields": result.get("fields", {}),
        "engine": result.get("engine"),
        "notice": (
            "Extracted values are suggestions only. You must confirm or correct "
            "each value before it is used for matching."
        ),
    }
