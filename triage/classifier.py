
"""
Stage 3 first-pass classifier — distinguishes "cheap tier suffices" vs
"needs AI" (Sprint 2 scope, per docs/EXECUTION_PLAN.md), not the full
reasoning-depth ladder yet (Sprint 4+).

The classifier is itself named attack surface (ARCHITECTURE.md Stage 3 #6)
-- see guardrails/adversarial/classifier_attack_suite.py, currently run
against Stage 0 and slated to retarget here at Sprint 6 once the full
routing/decision logic exists alongside it.
"""
from __future__ import annotations
from policy.schemas import RequestClassification, RequestType
from triage.taxonomy import SIGNAL_KEYWORDS, CHEAP_TIER_ELIGIBLE, CATEGORY_PRIORITY


def classify(request_text: str) -> RequestClassification:
    text = (request_text or "").lower()
    scores: dict[RequestType, int] = {}
    for category, keywords in SIGNAL_KEYWORDS.items():
        hits = sum(1 for kw in keywords if kw in text)
        if hits:
            scores[category] = hits

    if not scores:
        # No confident signal -> escalate up, per ARCHITECTURE.md Stage 3 #7
        # ("if classification fails/errors, default to the most conservative
        # tier, not the cheapest"). UNKNOWN + confidence 0.0 is never
        # cheap-tier eligible.
        return RequestClassification(category=RequestType.UNKNOWN, confidence=0.0, raw_text=request_text)

    # Select by CATEGORY_PRIORITY (most-conservative-first), NOT by which
    # category had the most keyword hits. A request that matches both
    # HIGH_STAKES and LOOKUP keywords must be classified HIGH_STAKES even if
    # LOOKUP's keywords appeared more often -- see taxonomy.py's comment on
    # CATEGORY_PRIORITY for why hit-count-wins is an exploitable design.
    best_category = next(cat for cat in CATEGORY_PRIORITY if cat in scores)
    confidence = min(0.4 + 0.15 * scores[best_category], 0.75)
    return RequestClassification(category=best_category, confidence=confidence, raw_text=request_text)


def is_cheap_tier_eligible(classification: RequestClassification, min_confidence: float = 0.4) -> bool:
    return classification.category in CHEAP_TIER_ELIGIBLE and classification.confidence >= min_confidence
