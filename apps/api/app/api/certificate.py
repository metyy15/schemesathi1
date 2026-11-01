from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.profile_fact import ProfileFact
from app.models.scheme import Scheme, SchemeCondition
from app.models.eligibility_result import EligibilityResult
from app.services.eligibility_engine import eligibility_engine
from app.services.certificate_service import (
    build_certificate_payload,
    render_certificate_pdf,
    certificate_filename,
)

router = APIRouter()


@router.post("/generate")
async def generate_certificate(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Generate an Eligibility Assessment Certificate.

    This is a SchemeSathi assessment document. It is explicitly NOT a
    government-issued certificate and carries no legal or administrative
    validity - see the disclaimer baked into the payload and the PDF itself.
    """
    facts = db.query(ProfileFact).filter(ProfileFact.user_id == current_user.id).all()
    fact_list = [
        {
            "field_name": f.field_name,
            "value": f.value,
            "source": f.source,
            "verified": f.verified,
        }
        for f in facts
    ]

    schemes = db.query(Scheme).all()
    results = []
    for scheme in schemes:
        conditions = (
            db.query(SchemeCondition)
            .filter(SchemeCondition.scheme_id == scheme.id)
            .all()
        )
        cond_list = [
            {
                "condition_type": c.condition_type,
                "operator": c.operator,
                "value": c.value,
                "description": c.description,
                "is_required": c.is_required,
                "evidence_url": c.evidence_url,
                "evidence_excerpt": c.evidence_excerpt,
                "evidence_tier": c.evidence_tier,
            }
            for c in conditions
        ]
        evaluated = eligibility_engine.evaluate(fact_list, cond_list)
        if scheme.source_tier != "official" and evaluated["outcome"] == "potentially_eligible":
            evaluated["outcome"] = "needs_more_info"
            evaluated["match_score"] = min(evaluated["match_score"], 0.6)

        results.append(
            {
                "scheme_name": scheme.name,
                "outcome": evaluated["outcome"],
                "match_score": evaluated["match_score"],
                "official_source_url": scheme.official_source_url,
                "application_url": scheme.application_url,
                "benefit_description": scheme.benefit_description,
                "last_checked": scheme.last_checked,
                "source_tier": scheme.source_tier,
                "source_tier_label": scheme.source_tier_label,
                "condition_results": evaluated["condition_results"],
            }
        )

    if not results:
        raise HTTPException(
            status_code=400,
            detail="No schemes have been assessed yet. Run a discovery and check first.",
        )

    payload = build_certificate_payload(
        user={
            "full_name": current_user.full_name,
            "email": current_user.email,
            "state": current_user.state,
            "district": current_user.district,
        },
        results=results,
    )
    return payload


@router.get("/download")
async def download_certificate(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Return the certificate as a downloadable PDF."""
    from fastapi.responses import Response

    facts = db.query(ProfileFact).filter(ProfileFact.user_id == current_user.id).all()
    fact_list = [
        {
            "field_name": f.field_name,
            "value": f.value,
            "source": f.source,
            "verified": f.verified,
        }
        for f in facts
    ]

    schemes = db.query(Scheme).all()
    results = []
    for scheme in schemes:
        conditions = (
            db.query(SchemeCondition)
            .filter(SchemeCondition.scheme_id == scheme.id)
            .all()
        )
        cond_list = [
            {
                "condition_type": c.condition_type,
                "operator": c.operator,
                "value": c.value,
                "description": c.description,
                "is_required": c.is_required,
                "evidence_url": c.evidence_url,
                "evidence_tier": c.evidence_tier,
            }
            for c in conditions
        ]
        evaluated = eligibility_engine.evaluate(fact_list, cond_list)
        if scheme.source_tier != "official" and evaluated["outcome"] == "potentially_eligible":
            evaluated["outcome"] = "needs_more_info"
            evaluated["match_score"] = min(evaluated["match_score"], 0.6)
        results.append(
            {
                "scheme_name": scheme.name,
                "outcome": evaluated["outcome"],
                "match_score": evaluated["match_score"],
                "official_source_url": scheme.official_source_url,
                "application_url": scheme.application_url,
                "benefit_description": scheme.benefit_description,
                "last_checked": scheme.last_checked,
                "source_tier": scheme.source_tier,
                "source_tier_label": scheme.source_tier_label,
                "condition_results": evaluated["condition_results"],
            }
        )

    if not results:
        raise HTTPException(
            status_code=400,
            detail="No schemes have been assessed yet. Run a discovery and check first.",
        )

    payload = build_certificate_payload(
        user={
            "full_name": current_user.full_name,
            "email": current_user.email,
            "state": current_user.state,
            "district": current_user.district,
        },
        results=results,
    )
    pdf_bytes = render_certificate_pdf(payload)
    filename = certificate_filename(payload)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
