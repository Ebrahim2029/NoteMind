"""
Simple prompt/content sanitizer to reduce prompt injection and secrets leakage.
"""



import re
from typing import Dict


REDACTIONS = [
    (re.compile(r"(sk-[A-Za-z0-9]{20,})"), "[REDACTED_API_KEY]"),
    (re.compile(r"(?i)password\s*[:=]\s*\S+"), "password=[REDACTED]"),
]


def sanitize_text(text: str) -> str:
    """Redact obvious secrets; strip dangerous control patterns."""
    for pattern, replacement in REDACTIONS:
        text = pattern.sub(replacement, text)
    return text.strip()


def sanitize_metadata(meta: Dict[str, str]) -> Dict[str, str]:
    return {k: sanitize_text(v) for k, v in meta.items()}
