"""PII redactor — scrubs personal identifiers from agent messages before logging."""

from __future__ import annotations

import re
from typing import Any

import structlog

log = structlog.get_logger(__name__)

_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("email", re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b")),
    ("ssn", re.compile(r"\b\d{3}-\d{2}-\d{4}\b")),
    ("phone", re.compile(r"\b(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b")),
    (
        "credit_card",
        re.compile(r"\b(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14}|3[47][0-9]{13})\b"),
    ),
]

_REDACTED = "[REDACTED]"


def redact_string(text: str) -> str:
    for label, pattern in _PATTERNS:
        count = len(pattern.findall(text))
        if count:
            log.debug("pii_redacted", type=label, count=count)
        text = pattern.sub(_REDACTED, text)
    return text


def redact_dict(data: dict[str, Any], depth: int = 0) -> dict[str, Any]:
    if depth > 5:
        return data
    result: dict[str, Any] = {}
    for k, v in data.items():
        if isinstance(v, str):
            result[k] = redact_string(v)
        elif isinstance(v, dict):
            result[k] = redact_dict(v, depth + 1)
        elif isinstance(v, list):
            result[k] = [
                redact_string(item)
                if isinstance(item, str)
                else redact_dict(item, depth + 1)
                if isinstance(item, dict)
                else item
                for item in v
            ]
        else:
            result[k] = v
    return result


class PIIRedactor:
    def redact(self, text: str) -> str:
        return redact_string(text)

    def redact_payload(self, payload: dict[str, Any]) -> dict[str, Any]:
        return redact_dict(payload)
