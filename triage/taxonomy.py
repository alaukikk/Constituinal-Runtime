
"""
Signal vocabulary the Stage 3 classifier scores against, to decide
"cheap tier suffices" vs "needs AI" (the necessity gap from the LLM-Agents
Review paper, per docs/RESEARCH_TRACEABILITY.md). Sprint 2 scope: lexical
only -- not the full reasoning-depth ladder yet (that's Sprint 4+).

Kept separate from classifier.py's scoring logic on purpose: this file is
just data (what an attacker would need to manipulate to cause
misclassification), while classifier.py is the decision logic. Per
ARCHITECTURE.md Stage 3 #6, the classifier itself is attack surface --
separating vocabulary from scoring makes that surface easier to reason
about and test.
"""
from __future__ import annotations
from policy.schemas import RequestType

SIGNAL_KEYWORDS: dict[RequestType, list[str]] = {
    RequestType.LOOKUP: ["what is", "who is", "when did", "capital of", "define"],
    RequestType.COMPUTATION: ["calculate", "how much is", "sum of"],
    RequestType.CLASSIFICATION: ["categorize", "is this spam", "classify", "which category"],
    RequestType.GENERATION: ["write", "draft", "compose", "generate a", "create a story"],
    RequestType.JUDGMENT: ["should i", "is it better", "recommend", "which is best", "opinion on"],
    RequestType.HIGH_STAKES: ["legal advice", "medical diagnosis", "financial advice", "suicide", "self-harm"],
}

# Only categories where a WRONG cheap-tier answer is low-cost AND the
# question genuinely doesn't require judgment. Deliberately excludes every
# other category, even ones a keyword match could theoretically catch --
# e.g. HIGH_STAKES should never be cheap-tier eligible even if confidently
# classified, because confident classification isn't the same as safe to
# under-scrutinize.
CHEAP_TIER_ELIGIBLE = {RequestType.LOOKUP, RequestType.COMPUTATION}

# Tie-break order when a request matches keywords from MORE THAN ONE
# category (e.g. "what is the best medical diagnosis" hits both LOOKUP's
# "what is" and HIGH_STAKES's "medical diagnosis"). Most-conservative-first:
# the earliest matching category in this list wins, regardless of which
# category had more total keyword hits. This mirrors policy/engine.py's
# "most severe action wins" rule -- a safety-relevant category must never
# lose a tie-break just because a less risky category happened to match
# more words. Without this, a classifier attacker could dilute a dangerous
# request by padding it with LOOKUP-flavored phrasing.
CATEGORY_PRIORITY: list[RequestType] = [
    RequestType.HIGH_STAKES,
    RequestType.JUDGMENT,
    RequestType.CLASSIFICATION,
    RequestType.GENERATION,
    RequestType.COMPUTATION,
    RequestType.LOOKUP,
]
