from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.scheme import Scheme, SchemeCondition
from app.models.source_evidence import SourceEvidence
from app.services.scheme_extractor import scheme_extractor
from app.services.source_registry import source_registry, TIER_COMMUNITY

router = APIRouter()


class ExtractRequest(BaseModel):
    url: str


class DiscoverRequest(BaseModel):
    query: str = "government schemes India scholarships welfare benefits"
    include_community: bool = True


@router.post("/discover")
async def discover_schemes(
    req: DiscoverRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Discover candidate scheme pages.

    Official publishers are searched first. Established community aggregators
    are included as a labelled fallback so schemes whose official portal sits
    behind strong authentication remain discoverable.
    """
    results = await scheme_extractor.discover_schemes(
        req.query, include_community=req.include_community
    )
    official = [r for r in results if r["source_tier"] == "official"]
    community = [r for r in results if r["source_tier"] == "community"]
    return {
        "count": len(results),
        "official_count": len(official),
        "community_count": len(community),
        "results": results,
        "notice": (
            "Official sources are preferred. Community sources are shown for "
            "schemes whose official portal is not publicly readable and are "
            "always marked as requiring verification on the official portal."
        ),
    }


@router.get("/sources")
def list_sources(current_user: User = Depends(get_current_user)):
    """Expose the trust tiers the system uses."""
    return {
        "official": source_registry.official_only(),
        "community": source_registry.community_only(),
        "tier_labels": {
            "official": "Official Government Source",
            "community": "Community Source - Verify on Official Portal",
            "unverified": "Unverified Source",
        },
    }


@router.post("/extract")
async def extract_scheme(
    req: ExtractRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Fetch a scheme page, normalise it, and store it with its trust tier."""
    url = req.url.strip()
    tier = source_registry.classify(url)
    if tier == "unverified":
        raise HTTPException(
            status_code=400,
            detail=(
                "That URL is not a recognised official or community publisher. "
                "SchemeSathi only reads official government sites and a fixed "
                "list of established public aggregators."
            ),
        )

    extracted = await scheme_extractor.extract_from_url(url)

    scheme = Scheme(
        name=extracted.get("name") or "Unnamed Scheme",
        scope=extracted.get("scope"),
        state=extracted.get("state"),
        ministry_department=extracted.get("ministry_department"),
        benefit_description=extracted.get("benefit_description"),
        benefit_amount=extracted.get("benefit_amount"),
        application_url=extracted.get("application_url") or url,
        official_source_url=extracted.get("official_source_url") or url,
        source_url=extracted.get("source_url") or url,
        required_documents=extracted.get("required_documents", []),
        source_confidence=extracted.get("source_confidence", "medium"),
        verification_status=extracted.get("verification_status", "needs_verification"),
        source_tier=extracted.get("source_tier", tier),
        source_tier_label=extracted.get("source_tier_label"),
        official_application_confirmed=bool(
            extracted.get("official_application_confirmed", False)
        ),
        review_note=extracted.get("review_note"),
        extra={
            "exclusions": extracted.get("exclusions", []),
            "application_opening": extracted.get("application_opening"),
            "application_closing": extracted.get("application_closing"),
            "source_tier_description": extracted.get("source_tier_description"),
        },
    )
    db.add(scheme)
    db.commit()
    db.refresh(scheme)

    for cond in extracted.get("eligibility_conditions", []):
        db.add(
            SchemeCondition(
                scheme_id=scheme.id,
                condition_type=cond.get("condition_type", "other"),
                operator=cond.get("operator", "=="),
                value=str(cond.get("value", "")),
                description=cond.get("description"),
                evidence_url=url,
                evidence_excerpt=cond.get("evidence_excerpt"),
                evidence_tier=tier,
                is_required=cond.get("is_required", True),
            )
        )

    db.add(
        SourceEvidence(
            scheme_id=scheme.id,
            url=url,
            page_title=extracted.get("name"),
            source_tier=tier,
            source_tier_label=extracted.get("source_tier_label"),
        )
    )
    db.commit()

    return {
        "scheme_id": scheme.id,
        "source_tier": scheme.source_tier,
        "source_tier_label": scheme.source_tier_label,
        "verification_status": scheme.verification_status,
        "review_note": scheme.review_note,
        "extracted": extracted,
    }


@router.get("/list")
def list_schemes(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    schemes = db.query(Scheme).order_by(Scheme.created_at.desc()).all()
    return [
        {
            "id": s.id,
            "name": s.name,
            "scope": s.scope,
            "state": s.state,
            "ministry_department": s.ministry_department,
            "benefit_description": s.benefit_description,
            "benefit_amount": s.benefit_amount,
            "official_source_url": s.official_source_url,
            "application_url": s.application_url,
            "required_documents": s.required_documents,
            "source_confidence": s.source_confidence,
            "verification_status": s.verification_status,
            "source_tier": s.source_tier,
            "source_tier_label": s.source_tier_label,
            "official_application_confirmed": s.official_application_confirmed,
            "review_note": s.review_note,
            "last_checked": s.last_checked,
        }
        for s in schemes
    ]


@router.get("/{scheme_id}")
def get_scheme(
    scheme_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    scheme = db.query(Scheme).filter(Scheme.id == scheme_id).first()
    if not scheme:
        raise HTTPException(status_code=404, detail="Scheme not found")
    conditions = db.query(SchemeCondition).filter(SchemeCondition.scheme_id == scheme_id).all()
    evidence = db.query(SourceEvidence).filter(SourceEvidence.scheme_id == scheme_id).all()
    return {
        "id": scheme.id,
        "name": scheme.name,
        "scope": scheme.scope,
        "state": scheme.state,
        "ministry_department": scheme.ministry_department,
        "benefit_description": scheme.benefit_description,
        "benefit_amount": scheme.benefit_amount,
        "official_source_url": scheme.official_source_url,
        "application_url": scheme.application_url,
        "required_documents": scheme.required_documents,
        "source_confidence": scheme.source_confidence,
        "verification_status": scheme.verification_status,
        "source_tier": scheme.source_tier,
        "source_tier_label": scheme.source_tier_label,
        "official_application_confirmed": scheme.official_application_confirmed,
        "review_note": scheme.review_note,
        "last_checked": scheme.last_checked,
        "conditions": [
            {
                "id": c.id,
                "condition_type": c.condition_type,
                "operator": c.operator,
                "value": c.value,
                "description": c.description,
                "evidence_url": c.evidence_url,
                "evidence_tier": c.evidence_tier,
                "is_required": c.is_required,
            }
            for c in conditions
        ],
        "evidence": [
            {
                "id": e.id,
                "url": e.url,
                "page_title": e.page_title,
                "source_tier": e.source_tier,
                "source_tier_label": e.source_tier_label,
                "retrieved_at": e.retrieved_at,
            }
            for e in evidence
        ],
    }
