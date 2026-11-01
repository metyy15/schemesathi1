from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import Optional

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.scheme import Scheme
from app.models.source_snapshot import SourceSnapshot
from app.models.notification import Notification
from app.models.eligibility_result import EligibilityResult
from app.services.tinyfish_client import tinyfish_client
from app.services.source_registry import source_registry
import hashlib
from datetime import datetime

router = APIRouter()


@router.post("/check-updates")
async def check_updates(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Manual 'Check for updates' action.

    Re-reads each scheme's source page, compares the content hash against the
    last snapshot, and records any change. Only schemes whose tier is official
    can close a verification gap; community-sourced schemes are re-checked too
    but remain flagged.
    """
    schemes = db.query(Scheme).all()
    updates_found = []
    checked = 0
    errors = []

    for scheme in schemes:
        url = scheme.source_url or scheme.official_source_url
        if not url:
            continue
        checked += 1

        fetched = await tinyfish_client.fetch(url)
        content = ""
        if isinstance(fetched, dict):
            if fetched.get("error"):
                errors.append({"scheme": scheme.name, "error": fetched["error"]})
                continue
            content = fetched.get("content") or fetched.get("text") or ""
        if not content:
            continue

        content_hash = hashlib.sha256(content.encode()).hexdigest()
        last = (
            db.query(SourceSnapshot)
            .filter(SourceSnapshot.source_url == url)
            .order_by(SourceSnapshot.detected_at.desc())
            .first()
        )

        if last and last.content_hash_new and last.content_hash_new != content_hash:
            snapshot = SourceSnapshot(
                source_url=url,
                content_hash_old=last.content_hash_new,
                content_hash_new=content_hash,
                content_old=last.content_new,
                content_new=content[:5000],
                changed="true",
            )
            db.add(snapshot)

            tier = scheme.source_tier or source_registry.classify(url)
            updates_found.append(
                {
                    "scheme_id": scheme.id,
                    "scheme_name": scheme.name,
                    "url": url,
                    "source_tier": tier,
                    "source_tier_label": scheme.source_tier_label,
                    "change_detected": True,
                    "what_changed": "Page content differs from the last saved snapshot.",
                    "why_it_matters": (
                        "Eligibility conditions, benefits, or deadlines on this page "
                        "may have been amended. Re-check the scheme and confirm on "
                        "the official portal."
                    ),
                    "checked_at": datetime.utcnow().isoformat(),
                }
            )

            # Notify users who were matched against this scheme.
            affected = (
                db.query(EligibilityResult)
                .filter(EligibilityResult.scheme_id == scheme.id)
                .distinct(EligibilityResult.user_id)
                .all()
            )
            for res in affected:
                db.add(
                    Notification(
                        user_id=res.user_id,
                        type="rule_change",
                        title=f"Update detected: {scheme.name}",
                        message=(
                            "The source page for this scheme changed since we last "
                            "checked. Open the scheme to see what may be different."
                        ),
                        data={
                            "scheme_id": scheme.id,
                            "url": url,
                            "source_tier": tier,
                        },
                    )
                )
        elif not last:
            db.add(
                SourceSnapshot(
                    source_url=url,
                    content_hash_new=content_hash,
                    content_new=content[:5000],
                    changed="false",
                )
            )

    db.commit()
    return {
        "checked": checked,
        "updates_found": updates_found,
        "update_count": len(updates_found),
        "errors": errors,
        "notice": (
            "SchemeSathi runs periodic checks, not real-time monitoring. "
            "Always confirm on the official portal before acting on a change."
        ),
    }
