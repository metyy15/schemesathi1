"""
Source trust registry for SchemeSathi.

Design rationale
----------------
SchemeSathi must never present aggregator content as if it were a government
publication. The product principle from the skill guide is: *every scheme
recommendation links to an official source*.

So we do not "believe" secondary sites the way a government portal is
believed. Instead we classify every source into a trust tier and carry that
tier all the way through to the UI:

  Tier 1 - OFFICIAL      .gov.in / .nic.in / statutory bodies
                          confidence: high,   verification: verified
  Tier 2 - COMMUNITY     established public aggregators and exam-prep
                          publishers (Jagran Josh, ClearIAS, Adda247, Testbook,
                          Adithya Info Hub, Sarkari Result)
                          confidence: medium, verification: needs_verification
  Tier 3 - UNVERIFIED    anything else
                          confidence: low,    verification: needs_verification

Tier 2 sources exist so that a scheme whose official portal sits behind a
login, a CAPTCHA, or heavy bot protection is still *discoverable*. They are
used to find the scheme, to gather draft eligibility wording, and to locate
the official application link - but the scheme is always flagged so the
citizen knows to confirm on the official portal before applying.

No source ever bypasses a login, CAPTCHA, paywall, or robots restriction.
We only read pages that are publicly served to an ordinary reader.
"""
from typing import List, Dict, Any, Optional
from urllib.parse import urlparse

# --------------------------------------------------------------------------
# Tier definitions
# --------------------------------------------------------------------------

TIER_OFFICIAL = "official"
TIER_COMMUNITY = "community"
TIER_UNVERIFIED = "unverified"

TIER_CONFIDENCE = {
    TIER_OFFICIAL: "high",
    TIER_COMMUNITY: "medium",
    TIER_UNVERIFIED: "low",
}

TIER_VERIFICATION = {
    TIER_OFFICIAL: "verified",
    TIER_COMMUNITY: "needs_verification",
    TIER_UNVERIFIED: "needs_verification",
}

TIER_LABELS = {
    TIER_OFFICIAL: "Official Government Source",
    TIER_COMMUNITY: "Community Source - Verify on Official Portal",
    TIER_UNVERIFIED: "Unverified Source",
}

TIER_DESCRIPTIONS = {
    TIER_OFFICIAL: "Published by the responsible government department.",
    TIER_COMMUNITY: (
        "Published by a well-known public aggregator rather than the department "
        "itself. Used to surface the scheme and provide draft rules. Confirm "
        "eligibility, deadlines and benefits on the official portal before applying."
    ),
    TIER_UNVERIFIED: (
        "Not a recognised official or community publisher. Treated as a lead only "
        "and never used on its own to produce a recommendation."
    ),
}

# --------------------------------------------------------------------------
# Tier 1 - official government publishers
# --------------------------------------------------------------------------

OFFICIAL_DOMAINS: List[str] = [
    "india.gov.in",
    "gov.in",
    "nic.in",
    "nsp.gov.in",
    "scholarships.gov.in",
    "dbtbharat.gov.in",
    "pmindia.gov.in",
    "myscheme.gov.in",
    "digitalindia.gov.in",
    "education.gov.in",
    "social welfare.gov.in",
    "welfare.gov.in",
    "rural.gov.in",
    "kvk.gov.in",
    "agriculture.gov.in",
    "msme.gov.in",
    "morth.nic.in",
    "uidai.gov.in",
    "digilocker.gov.in",
    "nrega.nic.in",
    "apnihealth.in",
]

# --------------------------------------------------------------------------
# Tier 2 - established community aggregators and exam-prep publishers
# --------------------------------------------------------------------------
# These are used strictly as a fallback discovery lane for schemes whose
# official portal is behind strong authentication. Their content is tagged
# Tier 2 everywhere it is rendered and never upgrades a scheme's official
# source link on its own.
# --------------------------------------------------------------------------

COMMUNITY_DOMAINS: List[str] = [
    "jagranjosh.com",
    "clearias.com",
    "adda247.com",
    "testbook.com",
    "addaiminfo.com",          # Adithya Info Hub
    "sarkariresult.com",
]

# Domains that specifically publish application deadlines and results.
COMMUNITY_DEADLINE_DOMAINS: List[str] = [
    "sarkariresult.com",
    "jagranjosh.com",
    "addaiminfo.com",
]


def _host(url: str) -> str:
    try:
        parsed = urlparse(url if "//" in url else f"//{url}")
        return (parsed.netloc or "").lower().split(":")[0]
    except Exception:
        return ""


def _matches(host: str, domain: str) -> bool:
    """Match a host against a domain, including subdomains.

    'gov.in' matches 'nsp.gov.in' and 'data.gov.in'.
    'jagranjosh.com' matches 'www.jagranjosh.com'.
    """
    if not host:
        return False
    host = host.lower()
    domain = domain.lower()
    if domain.startswith("*."):
        domain = domain[2:]
    return host == domain or host.endswith("." + domain)


class SourceRegistry:
    """Classifies a URL into a trust tier and supplies allowlists."""

    def classify(self, url: str) -> str:
        host = _host(url)
        if not host:
            return TIER_UNVERIFIED
        for domain in OFFICIAL_DOMAINS:
            if _matches(host, domain):
                return TIER_OFFICIAL
        for domain in COMMUNITY_DOMAINS:
            if _matches(host, domain):
                return TIER_COMMUNITY
        return TIER_UNVERIFIED

    def is_official(self, url: str) -> bool:
        return self.classify(url) == TIER_OFFICIAL

    def is_community(self, url: str) -> bool:
        return self.classify(url) == TIER_COMMUNITY

    def is_allowed(self, url: str) -> bool:
        """Allowed means: a recognised publisher, official or community."""
        return self.classify(url) in (TIER_OFFICIAL, TIER_COMMUNITY)

    def confidence_for(self, url: str) -> str:
        return TIER_CONFIDENCE[self.classify(url)]

    def verification_for(self, url: str) -> str:
        return TIER_VERIFICATION[self.classify(url)]

    def label_for(self, url: str) -> str:
        return TIER_LABELS[self.classify(url)]

    def describe(self, url: str) -> Dict[str, Any]:
        tier = self.classify(url)
        return {
            "url": url,
            "host": _host(url),
            "tier": tier,
            "tier_label": TIER_LABELS[tier],
            "tier_description": TIER_DESCRIPTIONS[tier],
            "source_confidence": TIER_CONFIDENCE[tier],
            "verification_status": TIER_VERIFICATION[tier],
            "is_official": tier == TIER_OFFICIAL,
        }

    def official_only(self) -> List[str]:
        return list(OFFICIAL_DOMAINS)

    def community_only(self) -> List[str]:
        return list(COMMUNITY_DOMAINS)

    def all_allowed(self) -> List[str]:
        return list(OFFICIAL_DOMAINS) + list(COMMUNITY_DOMAINS)


source_registry = SourceRegistry()
