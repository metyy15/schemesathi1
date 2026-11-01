from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.profile_fact import ProfileFact
from app.models.scheme import Scheme, SchemeCondition
from app.models.eligibility_result import EligibilityResult
from app.services.eligibility_engine import eligibility_engine
from app.services.llm_service import llm_service

router = APIRouter()


@router.post("/check")
async def check_eligibility(
    scheme_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Evaluate one scheme against the citizen's confirmed facts."""
    scheme = db.query(Scheme).filter(Scheme.id == scheme_id).first()
    if not scheme:
        raise HTTPException(status_code=404, detail="Scheme not found")

    facts = (
        db.query(ProfileFact)
        .filter(ProfileFact.user_id == current_user.id)
        .all()
    )
    fact_list = [
        {
            "field_name": f.field_name,
            "value": f.value,
            "source": f.source,
            "verified": f.verified,
        }
        for f in facts
    ]
    conditions = db.query(SchemeCondition).filter(SchemeCondition.scheme_id == scheme_id).all()
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

    result = eligibility_engine.evaluate(fact_list, cond_list)

    # If the rules came from a community source, never present a clean pass.
    if scheme.source_tier != "official" and result["outcome"] == "potentially_eligible":
        result["outcome"] = "needs_more_info"
        result["match_score"] = min(result["match_score"], 0.6)
        result["condition_results"].append(
            {
                "condition": "Source verification",
                "status": "needs_more_info",
                "reason": (
                    "Eligibility rules were read from a community publisher, not "
                    "from the department. Confirm on the official portal."
                ),
                "evidence_url": scheme.official_source_url,
            }
        )

    explanation = await llm_service.explain_match(
        fact_list,
        {"name": scheme.name, "official_source_url": scheme.official_source_url},
        result["condition_results"],
    )
    result["explanation"] = explanation
    result["scheme"] = {
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
        "source_tier": scheme.source_tier,
        "source_tier_label": scheme.source_tier_label,
        "verification_status": scheme.verification_status,
        "official_application_confirmed": scheme.official_application_confirmed,
        "last_checked": scheme.last_checked,
    }

    er = EligibilityResult(
        user_id=current_user.id,
        scheme_id=scheme_id,
        outcome=result["outcome"],
        match_score=result["match_score"],
        explanation=explanation,
        condition_results=result["condition_results"],
        meta={"source_tier": scheme.source_tier},
    )
    db.add(er)
    db.commit()

    return result


@router.post("/check-all")
async def check_all_schemes(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Evaluate every stored scheme and return the ranked shortlist."""
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
    out = []
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
        result = eligibility_engine.evaluate(fact_list, cond_list)
        if scheme.source_tier != "official" and result["outcome"] == "potentially_eligible":
            result["outcome"] = "needs_more_info"
            result["match_score"] = min(result["match_score"], 0.6)

        out.append(
            {
                "scheme_id": scheme.id,
                "scheme_name": scheme.name,
                "scope": scheme.scope,
                "state": scheme.state,
                "ministry_department": scheme.ministry_department,
                "benefit_description": scheme.benefit_description,
                "benefit_amount": scheme.benefit_amount,
                "official_source_url": scheme.official_source_url,
                "application_url": scheme.application_url,
                "required_documents": scheme.required_documents,
                "source_tier": scheme.source_tier,
                "source_tier_label": scheme.source_tier_label,
                "verification_status": scheme.verification_status,
                "official_application_confirmed": scheme.official_application_confirmed,
                "last_checked": scheme.last_checked,
                "outcome": result["outcome"],
                "match_score": result["match_score"],
                "condition_results": result["condition_results"],
                "disclaimer": result["disclaimer"],
            }
        )

    order = {"potentially_eligible": 0, "needs_more_info": 1, "likely_not_eligible": 2}
    out.sort(key=lambda r: (order.get(r["outcome"], 3), -(r["match_score"] or 0)))
    return {"count": len(out), "results": out}


@router.get("/results")
def get_results(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    results = (
        db.query(EligibilityResult)
        .filter(EligibilityResult.user_id == current_user.id)
        .order_by(EligibilityResult.evaluated_at.desc())
        .all()
    )
    out = []
    for r in results:
        scheme = db.query(Scheme).filter(Scheme.id == r.scheme_id).first()
        out.append(
            {
                "result_id": r.id,
                "scheme_id": r.scheme_id,
                "scheme_name": scheme.name if scheme else None,
                "outcome": r.outcome,
                "match_score": r.match_score,
                "explanation": r.explanation,
                "condition_results": r.condition_results,
                "official_source_url": scheme.official_source_url if scheme else None,
                "application_url": scheme.application_url if scheme else None,
                "source_tier": scheme.source_tier if scheme else None,
                "source_tier_label": scheme.source_tier_label if scheme else None,
                "benefit_description": scheme.benefit_description if scheme else None,
                "last_checked": scheme.last_checked if scheme else None,
                "evaluated_at": r.evaluated_at,
            }
        )
    return out
