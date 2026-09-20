from __future__ import annotations
import re

_PATTERNS=(
    (re.compile(r"(?i)(authorization\s*:\s*bearer\s+)[^\s,]+"), r"\1[REDACTED]"),
    (re.compile(r"(?i)(\b(?:api[_ -]?key|ark[_ -]?key|token)\s*[=:]\s*)[^\s,]+"), r"\1[REDACTED]"),
)
def redact_secrets(value: str) -> str:
    for pattern,replacement in _PATTERNS: value=pattern.sub(replacement,value)
    return value
