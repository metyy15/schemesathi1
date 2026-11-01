"""
Eligibility Certificate generation.

IMPORTANT DESIGN NOTE
----------------------
SchemeSathi cannot issue a *government* certificate. It is not a government
authority and a certificate it produces carries no legal or administrative
validity. What we generate is an **Eligibility Assessment Certificate** -
a signed, evidence-backed summary of what our rules engine found, which is
genuinely useful for a citizen (it says what you qualify for, what is
missing, and which official portal to confirm on) but is clearly and
prominently labelled as a SchemeSathi assessment, not an official document.

We deliberately:
  - stamp every certificate "NOT A GOVERNMENT ISSUED DOCUMENT"
  - never claim approval, sanction, or entitlement
  - list the exact official source and last-verified timestamp
  - include a verification hash so tampering is detectable
  - generate it as a real PDF so it is printable and shareable
"""
from typing import Dict, Any, List, Optional
import hashlib
import json
import os
from datetime import datetime

from app.core.config import settings

CERT_DIR = os.path.join(settings.LOCAL_STORAGE_DIR, "certificates")


def _sha256(payload: str) -> str:
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def build_certificate_payload(
    user: Dict[str, Any],
    results: List[Dict[str, Any]],
    generated_at: Optional[datetime] = None,
) -> Dict[str, Any]:
    """Build the deterministic certificate record + verification hash."""
    generated_at = generated_at or datetime.utcnow()

    eligible = [r for r in results if r.get("outcome") == "potentially_eligible"]
    needs_info = [r for r in results if r.get("outcome") == "needs_more_info"]
    not_eligible = [r for r in results if r.get("outcome") == "likely_not_eligible"]

    body = {
        "certificate_type": "eligibility_assessment",
        "certificate_id": None,
        "generated_at": generated_at.isoformat(),
        "holder": {
            "name": user.get("full_name"),
            "email": user.get("email"),
            "state": user.get("state"),
            "district": user.get("district"),
        },
        "summary": {
            "potentially_eligible": len(eligible),
            "needs_more_information": len(needs_info),
            "likely_not_eligible": len(not_eligible),
            "total_evaluated": len(results),
        },
        "schemes": [
            {
                "name": r.get("scheme_name"),
                "outcome": r.get("outcome"),
                "match_score": r.get("match_score"),
                "official_source_url": r.get("official_source_url"),
                "application_url": r.get("application_url"),
                "benefit_description": r.get("benefit_description"),
                "last_checked": r.get("last_checked"),
                "source_tier": r.get("source_tier", "official"),
                "source_tier_label": r.get("source_tier_label"),
                "matched_conditions": [
                    c for c in (r.get("condition_results") or []) if c.get("status") == "matched"
                ],
                "missing_conditions": [
                    c
                    for c in (r.get("condition_results") or [])
                    if c.get("status") == "needs_more_info"
                ],
                "failed_conditions": [
                    c
                    for c in (r.get("condition_results") or [])
                    if c.get("status") == "not_matched"
                ],
            }
            for r in results
        ],
    }

    # Deterministic id + hash over the meaningful body.
    canonical = json.dumps(body, sort_keys=True, default=str)
    digest = _sha256(canonical)
    body["certificate_id"] = f"SS-EA-{generated_at.strftime('%Y%m%d')}-{digest[:10].upper()}"
    body["verification_hash"] = digest
    body["disclaimer"] = (
        "This is a SchemeSathi Eligibility Assessment Certificate. It is NOT a "
        "certificate issued by any Government of India department, and it is not "
        "valid for any official purpose. It records the result of an automated "
        "comparison between a citizen's confirmed profile and published scheme "
        "rules. It does not grant, approve, sanction, or guarantee any benefit, "
        "payment, or entitlement. The relevant department makes the final decision."
    )
    return body


def render_certificate_pdf(payload: Dict[str, Any]) -> bytes:
    """
    Render the certificate to a PDF.

    Uses ReportLab if available; otherwise falls back to a minimal
    hand-built PDF writer so the endpoint never hard-fails.
    """
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.units import mm
        from reportlab.lib import colors
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.platypus import (
            SimpleDocTemplate,
            Paragraph,
            Spacer,
            Table,
            TableStyle,
            PageBreak,
        )
        from reportlab.lib.enums import TA_CENTER
        import io

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            leftMargin=18 * mm,
            rightMargin=18 * mm,
            topMargin=16 * mm,
            bottomMargin=16 * mm,
            title=f"SchemeSathi Eligibility Assessment {payload['certificate_id']}",
            author="SchemeSathi",
        )

        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            "TitleX",
            parent=styles["Title"],
            fontName="Helvetica-Bold",
            fontSize=19,
            leading=23,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#131b2e"),
            spaceAfter=2,
        )
        sub_style = ParagraphStyle(
            "SubX",
            parent=styles["Normal"],
            fontSize=9,
            leading=12,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#45464d"),
        )
        h2 = ParagraphStyle(
            "H2X",
            parent=styles["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=11.5,
            leading=14,
            textColor=colors.HexColor("#131b2e"),
            spaceBefore=9,
            spaceAfter=4,
        )
        body_style = ParagraphStyle(
            "BodyX",
            parent=styles["Normal"],
            fontSize=8.6,
            leading=12,
            textColor=colors.HexColor("#191c1e"),
        )
        small = ParagraphStyle(
            "SmallX",
            parent=styles["Normal"],
            fontSize=7.4,
            leading=9.6,
            textColor=colors.HexColor("#45464d"),
        )
        warn = ParagraphStyle(
            "WarnX",
            parent=styles["Normal"],
            fontSize=8,
            leading=11,
            textColor=colors.HexColor("#93000a"),
            alignment=TA_CENTER,
        )

        story = []

        # Header band
        header = Table(
            [
                [
                    Paragraph(
                        "<b>SchemeSathi</b><br/>Government Benefits Navigator",
                        sub_style,
                    ),
                    Paragraph(
                        f"<b>Eligibility Assessment Certificate</b><br/>{payload['certificate_id']}",
                        sub_style,
                    ),
                ]
            ],
            colWidths=[doc.width * 0.5, doc.width * 0.5],
        )
        header.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#eceef0")),
                    ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#c6c6cd")),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("TOPPADDING", (0, 0), (-1, -1), 8),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ]
            )
        )
        story.append(header)
        story.append(Spacer(1, 8))

        story.append(
            Paragraph(
                "<b>NOT A GOVERNMENT ISSUED DOCUMENT</b> - This assessment is produced "
                "by SchemeSathi, an independent information tool. It carries no legal or "
                "administrative validity and must not be presented as an official "
                "certificate, sanction, or approval.",
                warn,
            )
        )
        story.append(Spacer(1, 10))

        holder = payload["holder"]
        story.append(Paragraph("Certificate Holder", h2))
        holder_rows = [
            ["Name", holder.get("name") or "-"],
            ["Email", holder.get("email") or "-"],
            ["State / District", f"{holder.get('state') or '-'} / {holder.get('district') or '-'}"],
            ["Generated At (UTC)", payload["generated_at"]],
            ["Certificate ID", payload["certificate_id"]],
            ["Verification Hash", payload["verification_hash"]],
        ]
        t = Table(holder_rows, colWidths=[doc.width * 0.30, doc.width * 0.70])
        t.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f2f4f6")),
                    ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#c6c6cd")),
                    ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 8.4),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("TOPPADDING", (0, 0), (-1, -1), 5),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ]
            )
        )
        story.append(t)

        s = payload["summary"]
        story.append(Paragraph("Assessment Summary", h2))
        srows = [
            ["Potentially Eligible", str(s["potentially_eligible"])],
            ["Needs More Information", str(s["needs_more_information"])],
            ["Likely Not Eligible", str(s["likely_not_eligible"])],
            ["Total Schemes Evaluated", str(s["total_evaluated"])],
        ]
        t2 = Table(srows, colWidths=[doc.width * 0.70, doc.width * 0.30])
        t2.setStyle(
            TableStyle(
                [
                    ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#c6c6cd")),
                    ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f2f4f6")),
                    ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 8.4),
                    ("TOPPADDING", (0, 0), (-1, -1), 5),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ]
            )
        )
        story.append(t2)

        if payload["schemes"]:
            story.append(Paragraph("Schemes Assessed", h2))
            for sch in payload["schemes"]:
                label = {
                    "potentially_eligible": "Potentially Eligible",
                    "needs_more_info": "Needs More Information",
                    "likely_not_eligible": "Likely Not Eligible",
                }.get(sch.get("outcome"), sch.get("outcome"))
                tier = sch.get("source_tier_label") or "Official Government Source"
                story.append(Paragraph(f"<b>{sch.get('name')}</b>", body_style))
                story.append(
                    Paragraph(
                        f"Assessment: <b>{label}</b> &nbsp;|&nbsp; "
                        f"Source: {tier}<br/>"
                        f"Official link: {sch.get('official_source_url') or 'not yet confirmed'}<br/>"
                        f"Application: {sch.get('application_url') or 'not yet confirmed'}<br/>"
                        f"Last verified: {sch.get('last_checked') or 'not recorded'}",
                        small,
                    )
                )
                if sch.get("matched_conditions"):
                    items = "<br/>".join(
                        f"- {c.get('condition')} (your value: {c.get('your_value')})"
                        for c in sch["matched_conditions"]
                    )
                    story.append(Paragraph(f"Conditions matched:<br/>{items}", small))
                if sch.get("missing_conditions"):
                    items = "<br/>".join(
                        f"- {c.get('condition')}" for c in sch["missing_conditions"]
                    )
                    story.append(Paragraph(f"Still required:<br/>{items}", small))
                if sch.get("failed_conditions"):
                    items = "<br/>".join(
                        f"- {c.get('condition')} (your value: {c.get('your_value')}, required: {c.get('required')})"
                        for c in sch["failed_conditions"]
                    )
                    story.append(Paragraph(f"Not matched:<br/>{items}", small))
                story.append(Spacer(1, 7))

        story.append(Spacer(1, 6))
        story.append(Paragraph("Important Notice", h2))
        story.append(Paragraph(payload["disclaimer"], small))
        story.append(
            Paragraph(
                "Conditions were evaluated with a deterministic rules engine against "
                "published scheme conditions. Where a source was a community publisher "
                "rather than the department itself, the record is marked as requiring "
                "verification. Always confirm eligibility, deadlines, benefits and the "
                "application process on the official government portal before applying.",
                small,
            )
        )

        doc.build(story)
        return buffer.getvalue()

    except Exception as exc:  # pragma: no cover - fallback path
        return _minimal_pdf(payload, str(exc))


def _minimal_pdf(payload: Dict[str, Any], note: str = "") -> bytes:
    """Fallback hand-built single-page PDF if ReportLab is unavailable."""
    import io

    def esc(s: str) -> str:
        return (
            str(s)
            .replace("\\", r"\\")
            .replace("(", r"\(")
            .replace(")", r"\)")
        )

    lines = [
        "SchemeSathi - Eligibility Assessment Certificate",
        f"Certificate ID: {payload['certificate_id']}",
        f"Holder: {payload['holder'].get('name') or payload['holder'].get('email')}",
        f"Generated (UTC): {payload['generated_at']}",
        "",
        "NOT A GOVERNMENT ISSUED DOCUMENT - no legal or administrative validity.",
        "",
        "Summary:",
        f"  Potentially eligible: {payload['summary']['potentially_eligible']}",
        f"  Needs more information: {payload['summary']['needs_more_information']}",
        f"  Likely not eligible: {payload['summary']['likely_not_eligible']}",
        "",
        "Schemes assessed:",
    ]
    for sch in payload["schemes"]:
        lines.append(f"  - {sch.get('name')} [{sch.get('outcome')}]")
        lines.append(f"    source: {sch.get('official_source_url') or 'not confirmed'}")
    lines.extend(
        [
            "",
            "Verification hash: " + payload["verification_hash"],
            "",
            payload["disclaimer"][:700],
        ]
    )
    if note:
        lines.append("")
        lines.append(f"(reportlab unavailable: {note})")

    content_parts = ["BT", "/F1 10 Tf", "50 790 Td", "11 TL"]
    for line in lines:
        content_parts.append(f"({esc(line)}) Tj")
        content_parts.append("T*")
    content_parts.append("ET")
    stream = "\n".join(content_parts).encode("latin-1", "replace")

    objects = []
    objects.append(b"<< /Type /Catalog /Pages 2 0 R >>")
    objects.append(b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>")
    objects.append(
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] "
        b"/Resources << /Font << /F1 5 0 R >> >> /Contents 4 0 R >>"
    )
    objects.append(
        b"<< /Length " + str(len(stream)).encode() + b" >>\nstream\n" + stream + b"\nendstream"
    )
    objects.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")

    out = io.BytesIO()
    out.write(b"%PDF-1.4\n")
    offsets = []
    for i, obj in enumerate(objects, start=1):
        offsets.append(out.tell())
        out.write(f"{i} 0 obj\n".encode())
        out.write(obj)
        out.write(b"\nendobj\n")
    xref_pos = out.tell()
    out.write(f"xref\n0 {len(objects)+1}\n".encode())
    out.write(b"0000000000 65535 f \n")
    for off in offsets:
        out.write(f"{off:010d} 00000 n \n".encode())
    out.write(
        f"trailer\n<< /Size {len(objects)+1} /Root 1 0 R >>\nstartxref\n{xref_pos}\n%%EOF".encode()
    )
    return out.getvalue()


def certificate_filename(payload: Dict[str, Any]) -> str:
    return f"SchemeSathi_Eligibility_{payload['certificate_id']}.pdf"


certificate_service = type(
    "CertificateService",
    (),
    {
        "build_payload": staticmethod(build_certificate_payload),
        "render_pdf": staticmethod(render_certificate_pdf),
        "filename": staticmethod(certificate_filename),
    },
)()
