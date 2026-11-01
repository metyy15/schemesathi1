from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import Base, engine
from app.api import (
    auth,
    consent,
    documents,
    ocr,
    profile,
    schemes,
    eligibility,
    monitoring,
    notifications,
    certificate,
)

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="SchemeSathi API",
    description=(
        "India's Government Benefits Navigator - AI-powered scheme discovery "
        "and eligibility checking. SchemeSathi is an information tool, not a "
        "government authority."
    ),
    version="0.2.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(consent.router, prefix="/api/consent", tags=["Consent"])
app.include_router(documents.router, prefix="/api/documents", tags=["Documents"])
app.include_router(ocr.router, prefix="/api/ocr", tags=["OCR"])
app.include_router(profile.router, prefix="/api/profile", tags=["Profile"])
app.include_router(schemes.router, prefix="/api/schemes", tags=["Schemes"])
app.include_router(eligibility.router, prefix="/api/eligibility", tags=["Eligibility"])
app.include_router(certificate.router, prefix="/api/certificate", tags=["Certificate"])
app.include_router(monitoring.router, prefix="/api/monitoring", tags=["Monitoring"])
app.include_router(notifications.router, prefix="/api/notifications", tags=["Notifications"])


@app.get("/")
def root():
    return {
        "message": "SchemeSathi API",
        "version": "0.2.0",
        "status": "running",
        "disclaimer": (
            "SchemeSathi is an information tool, not a government authority. "
            "No guarantee of eligibility, approval, or benefit payment. "
            "Certificates issued by this system are SchemeSathi assessments, "
            "not government-issued documents."
        ),
    }


@app.get("/health")
def health():
    return {
        "status": "healthy",
        "tinyfish_configured": bool(settings.TINYFISH_API_KEY),
        "llm_configured": bool(settings.GEMINI_API_KEY),
    }
