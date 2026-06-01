"""Escalation grammar: typed escalation events emitted by agents."""

from __future__ import annotations

from enum import StrEnum
from typing import Any, Self

import structlog
from pydantic import BaseModel, Field

log = structlog.get_logger(__name__)


class EscalationLevel(StrEnum):
    INFO = "info"
    WARNING = "warning"
    ALERT = "alert"
    CRITICAL = "critical"
    EMERGENCY = "emergency"


class EscalationReason(StrEnum):
    LOW_CONFIDENCE = "low_confidence"
    POLICY_BLOCK = "policy_block"
    PURDUE_ZONE_VIOLATION = "purdue_zone_violation"
    IRREVERSIBLE_ACTION = "irreversible_action"
    ANOMALY_DETECTED = "anomaly_detected"
    SAFETY_INTERLOCK = "safety_interlock"
    HUMAN_REQUIRED = "human_required"
    TIMEOUT = "timeout"


class EscalationEvent(BaseModel):
    agent: str
    level: EscalationLevel
    reason: EscalationReason
    message: str
    trace_id: str
    confidence: float = Field(ge=0.0, le=1.0)
    context: dict[str, Any] = Field(default_factory=dict)
    resolved: bool = False

    def is_blocking(self: Self) -> bool:
        return self.level in {EscalationLevel.CRITICAL, EscalationLevel.EMERGENCY}

    def requires_hitl(self: Self) -> bool:
        return self.reason in {
            EscalationReason.LOW_CONFIDENCE,
            EscalationReason.IRREVERSIBLE_ACTION,
            EscalationReason.SAFETY_INTERLOCK,
            EscalationReason.HUMAN_REQUIRED,
        }


class EscalationRouter:
    """Routes EscalationEvents to the appropriate handler (HITL, logging, etc.)."""

    def __init__(self: Self, hitl_threshold: float = 0.85) -> None:
        self._hitl_threshold = hitl_threshold

    def evaluate(self: Self, event: EscalationEvent) -> bool:
        """Return True if execution should be halted pending HITL resolution."""
        if event.is_blocking():
            log.warning(
                "escalation_blocking",
                agent=event.agent,
                level=event.level,
                reason=event.reason,
                trace_id=event.trace_id,
            )
            return True

        if event.confidence < self._hitl_threshold and event.requires_hitl():
            log.info(
                "escalation_hitl_required",
                agent=event.agent,
                confidence=event.confidence,
                threshold=self._hitl_threshold,
                trace_id=event.trace_id,
            )
            return True

        log.debug(
            "escalation_non_blocking",
            agent=event.agent,
            level=event.level,
            trace_id=event.trace_id,
        )
        return False
