
"""
guardrails/output_filter.py — cheap, rule-based check on final output.

Distinct from validation/validator.py (Stage 6, not yet built): that stage
is about output QUALITY/CORRECTNESS. This file is narrowly about output
SAFETY LEAKAGE -- does the response contain evidence that something
upstream (Stage 0, Stage 1, or a future real model call) got bypassed.
E.g. the model acknowledging a jailbreak, or a credential-shaped string
that shouldn't be in any legitimate response.

No AI, fail closed: an internal error is treated as a failed check, same
philosophy as Stage 0.
"""
from __future__ import annotations
import re
from dataclasses import dataclass


@dataclass
class OutputFilterResult:
    passed: bool
    reasons: list[str]


_LEAK_PATTERNS: dict[str, str] = {
    "explicit_jailbreak_ack": r"\b(dan mode|jailbreak mode)\s+(activated|enabled)\b",
    "credential_pattern": r"\b(sk-[a-zA-Z0-9]{20,}|AKIA[0-9A-Z]{16})\b",
    "system_prompt_leak": r"\byou are\s+claude,?\s+(created|made)\s+by\s+anthropic\b.{0,80}\b(instructions|prompt|rules)\b",
}


def check_output(output_text: str) -> OutputFilterResult:
    try:
        if output_text is None:
            return OutputFilterResult(False, ["empty_output"])
        reasons = [name for name, pat in _LEAK_PATTERNS.items() if re.search(pat, output_text, re.IGNORECASE)]
        return OutputFilterResult(len(reasons) == 0, reasons)
    except Exception:
        return OutputFilterResult(False, ["filter_internal_error"])
