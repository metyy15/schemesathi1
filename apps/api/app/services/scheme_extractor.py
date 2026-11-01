"""
Scheme discovery and extraction.

Two discovery lanes:
  1. Official lane   - searches restricted to official government domains.
  2. Community lane  - searches established public aggregators. Used when the
                       official portal is behind strong authentication so the
                       scheme is still *discoverable*. Community content is
                       always tagged Tier 2 and flagged needs_verification.

Extraction never bypasses logins, CAPTCHAs, paywalls, or robots rules. We
only read pages publicly served to an ordinary reader.
"""
from typing import List, Dict, Any, Optional
from app.services.tinyfish_client import tinyfish_client
from app.services.llm_service import llm_service
from app.services.source_registry import (
    source_registry,
    TIER_OFFICIAL,
    TIER_COMMUNITY,
)
import json


class SchemeExtractor:
    # ---------------------------------------------------------------- search

    async def discover_schemes(
        self,
        query: str = "government schemes India scholarships welfare benefits",
        include_community: bool = True,
    ) -> List[Dict[str, Any]]:
        """Discover candidate scheme pages across both lanes."""
        results = await tinyfish_client.search(query)
        items = []
        if isinstance(results, dict):
            items = results.get("results") or results.get("data") or []

        candidates: List[Dict[str, Any]] = []
        seen = set()

        for item in items:
            url = item.get("url") or item.get("link") or ""
            if not url or url in seen:
                continue
            tier = source_registry.classify(url)
            if tier == TIER_OFFICIAL:
                seen.add(url)
                candidates.append(self._candidate(item, url, tier))
            elif tier == TIER_COMMUNITY and include_community:
                seen.add(url)
                candidates.append(self._candidate(item, url, tier))

        # Official first, then community
        candidates.sort(key=lambda c: 0 if c["source_tier"] == TIER_OFFICIAL else 1)
        return candidates

    async def discover_official_only(self, query: str) -> List[Dict[str, Any]]:
        return await self.discover_schemes(query, include_community=False)

    async def discover_community_only(self, query: str) -> List[Dict[str, Any]]:
        """Community fallback lane for schemes with locked-down official portals."""
        results = await tinyfish_client.search(
            f"{query} site:jagranjosh.com OR site:clearias.com OR site:adda247.com "
            f"OR site:testbook.com OR site:addaiminfo.com OR site:sarkariresult.com"
        )
        items = []
        if isinstance(results, dict):
            items = results.get("results") or results.get("data") or []

        out: List[Dict[str, Any]] = []
        seen = set()
        for item in items:
            url = item.get("url") or item.get("link") or ""
            if not url or url in seen:
                continue
            if not source_registry.is_community(url):
                continue
            seen.add(url)
            out.append(self._candidate(item, url, TIER_COMMUNITY))
        return out

    def _candidate(self, item: Dict[str, Any], url: str, tier: str) -> Dict[str, Any]:
        meta = source_registry.describe(url)
        return {
            "title": item.get("title") or item.get("name"),
            "url": url,
            "snippet": item.get("snippet") or item.get("description") or item.get("content"),
            "source_tier": tier,
            "source_tier_label": meta["tier_label"],
            "source_tier_description": meta["tier_description"],
            "source_confidence": meta["source_confidence"],
            "verification_status": meta["verification_status"],
            "is_official": tier == TIER_OFFICIAL,
        }

    # -------------------------------------------------------------- extract

    async def extract_from_url(self, url: str) -> Dict[str, Any]:
        """Fetch and normalise one scheme page into a structured record."""
        tier = source_registry.classify(url)
        meta = source_registry.describe(url)

        content = ""
        fetched = await tinyfish_client.fetch(url)
        if isinstance(fetched, dict):
            content = fetched.get("content") or fetched.get("text") or fetched.get("data") or ""

        if not content:
            # Browser-agent fallback for multi-step public info pages.
            agent_res = await tinyfish_client.run_agent(
                goal=(
                    "Extract government scheme details: name, eligibility criteria, "
                    "benefit amount, required documents, application deadlines, "
                    "application process, and the official application URL."
                ),
                url=url,
            )
            content = self._stringify(agent_res)

        extracted: Dict[str, Any] = {}
        if llm_service.enabled and content:
            extracted = await self._llm_extract(content, url, tier) or {}

        if not extracted.get("name") or extracted.get("name") == "Unknown Scheme":
            extracted = self._fallback_extract(content, url, extracted)

        # Stamp source trust onto the record.
        extracted["official_source_url"] = extracted.get("official_source_url") or url
        extracted["source_url"] = url
        extracted["source_tier"] = tier
        extracted["source_tier_label"] = meta["tier_label"]
        extracted["source_tier_description"] = meta["tier_description"]
        extracted["source_confidence"] = meta["source_confidence"]
        extracted["verification_status"] = meta["verification_status"]
        extracted["is_official"] = meta["is_official"]

        if tier == TIER_COMMUNITY:
            # A community page never closes a scheme on its own.
            extracted["verification_status"] = "needs_verification"
            extracted["official_application_confirmed"] = False
            extracted["review_note"] = (
                "Rules were read from a community publisher because the official "
                "portal is not publicly readable. Confirm every value on the "
                "official government portal before applying."
            )
        elif tier == TIER_OFFICIAL:
            extracted["official_application_confirmed"] = True

        return extracted

    async def _llm_extract(self, content: str, url: str, tier: str) -> Optional[Dict[str, Any]]:
        source_note = (
            "This page is an official government publication."
            if tier == TIER_OFFICIAL
            else "This page is a community aggregator, NOT an official government publication. "
            "Mark any field you cannot literally read from the page as null."
        )
        prompt = f"""Extract structured government scheme information from the page content below.

{source_note}

Return JSON with exactly these fields:
  name, scope ("central"|"state"|"district"), state, ministry_department,
  benefit_description, benefit_amount,
  eligibility_conditions: [ {{condition_type, operator, value, description, is_required}} ],
  exclusions: [string],
  required_documents: [string],
  application_opening (YYYY-MM-DD or null), application_closing (YYYY-MM-DD or null),
  application_url, official_source_url ("{url}").

Rules:
- condition_type is one of: income, state, age, gender, category, education,
  occupation, landholding, disability, residence, course, year, other
- operator is one of: ==, <=, >=, <, >, in, exists
- Copy values verbatim from the page. If a value is absent, use null.
- Never invent income limits, dates, or benefits.
- description must quote or closely paraphrase the source wording.

Page content:
{content[:12000]}
"""
        return await llm_service.extract_structured(prompt)

    def _fallback_extract(self, content: str, url: str, base: Dict[str, Any]) -> Dict[str, Any]:
        title = base.get("name")
        if not title:
            for line in (content or "").splitlines():
                line = line.strip()
                if len(line) > 8 and len(line) < 160:
                    title = line
                    break
        return {
            **base,
            "name": title or "Unnamed Scheme",
            "official_source_url": url,
            "eligibility_conditions": base.get("eligibility_conditions", []),
            "required_documents": base.get("required_documents", []),
            "benefit_description": base.get("benefit_description", ""),
            "verification_status": "needs_verification",
        }

    def _stringify(self, obj: Any) -> str:
        if isinstance(obj, str):
            return obj
        try:
            return json.dumps(obj, indent=2, default=str)
        except Exception:
            return str(obj)


scheme_extractor = SchemeExtractor()
