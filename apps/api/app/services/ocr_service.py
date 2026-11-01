import os
from typing import Dict, Any
from PIL import Image
import pytesseract
from app.core.config import settings


class OCRService:
    def __init__(self):
        if settings.TESSERACT_CMD:
            pytesseract.pytesseract.tesseract_cmd = settings.TESSERACT_CMD

    async def extract_from_image(self, file_path: str) -> Dict[str, Any]:
        try:
            image = Image.open(file_path)
            text = pytesseract.image_to_string(image)
            return {
                "text": text,
                "engine": "tesseract",
                "fields": self._parse_basic_fields(text)
            }
        except Exception as e:
            return {"error": str(e), "text": "", "fields": {}}

    async def extract_from_pdf(self, file_path: str) -> Dict[str, Any]:
        try:
            import pdfplumber
            text = ""
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    text += page.extract_text() or ""
            return {
                "text": text,
                "engine": "pdfplumber",
                "fields": self._parse_basic_fields(text)
            }
        except Exception as e:
            return {"error": str(e), "text": "", "fields": {}}

    def _parse_basic_fields(self, text: str) -> Dict[str, Any]:
        fields = {}
        text_lower = text.lower()
        # Very basic heuristics - user must confirm
        if "income" in text_lower:
            fields["income_mentioned"] = True
        if "domicile" in text_lower or "residence" in text_lower:
            fields["domicile_mentioned"] = True
        if "marks" in text_lower or "percentage" in text_lower or "cgpa" in text_lower:
            fields["education_mentioned"] = True
        return fields


ocr_service = OCRService()
