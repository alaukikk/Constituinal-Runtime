
"""
Stage 3/5 deterministic tier — real implementation. Calculator + simple
static fact lookup, no AI.

Security note: deliberately does NOT use eval() or any other code-execution
mechanism to handle arithmetic. A strict regex only matches a single
`number operator number` shape; anything else (including text crafted to
look like a Python expression) simply doesn't match and falls through to a
costlier tier. Safe by construction, not by attempted sanitization.

Conservative by design: this tier should only ever answer when it can do so
RELIABLY (ARCHITECTURE.md Stage 3 #1 -- "the cheapest tier that can reliably
handle it"). Anything ambiguous, multi-step, or outside the narrow patterns
below returns None rather than guessing.
"""
from __future__ import annotations
import re
from typing import Optional

# Single binary operation only, e.g. "2 + 2", "10 / 4". Deliberately does NOT
# support chained operations (e.g. "2 + 2 * 3") -- operator precedence bugs
# are an easy way for a "deterministic" tier to silently give a wrong answer.
_ARITHMETIC_RE = re.compile(r"^\s*(-?\d+(?:\.\d+)?)\s*([+\-*/])\s*(-?\d+(?:\.\d+)?)\s*\??\s*$")

_STATIC_FACTS = {
    "what is the capital of france": "Paris",
    "what is the capital of japan": "Tokyo",
    "how many days are in a week": "7",
    "how many months are in a year": "12",
}


def _try_arithmetic(text: str) -> Optional[str]:
    match = _ARITHMETIC_RE.match(text.strip())
    if not match:
        return None
    left, op, right = match.groups()
    a, b = float(left), float(right)
    if op == "+":
        result = a + b
    elif op == "-":
        result = a - b
    elif op == "*":
        result = a * b
    elif op == "/":
        if b == 0:
            return None  # fall through rather than crash or claim an answer
        result = a / b
    else:
        return None
    return str(int(result)) if result.is_integer() else str(result)


def try_deterministic(request_text: str) -> Optional[str]:
    text = (request_text or "").strip()
    if not text:
        return None
    arithmetic = _try_arithmetic(text)
    if arithmetic is not None:
        return arithmetic
    return _STATIC_FACTS.get(text.lower().rstrip("?").strip())
