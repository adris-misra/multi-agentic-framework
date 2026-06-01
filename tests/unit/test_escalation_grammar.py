"""Unit tests for EscalationEvent and EscalationRouter."""

from __future__ import annotations

import pytest

from industrial_agents.orchestration.escalation_grammar import (
    EscalationEvent,
    EscalationLevel,
    EscalationReason,
    EscalationRouter,
)


@pytest.fixture()
def router() -> EscalationRouter:
    return EscalationRouter(hitl_threshold=0.85)


class TestEscalationEvent:
    def test_critical_is_blocking(self, trace_id: str) -> None:
        event = EscalationEvent(
            agent="safety",
            level=EscalationLevel.CRITICAL,
            reason=EscalationReason.SAFETY_INTERLOCK,
            message="E-stop triggered",
            trace_id=trace_id,
            confidence=0.99,
        )
        assert event.is_blocking() is True

    def test_warning_is_not_blocking(self, trace_id: str) -> None:
        event = EscalationEvent(
            agent="anomaly",
            level=EscalationLevel.WARNING,
            reason=EscalationReason.LOW_CONFIDENCE,
            message="Low confidence",
            trace_id=trace_id,
            confidence=0.70,
        )
        assert event.is_blocking() is False

    def test_low_confidence_requires_hitl(self, trace_id: str) -> None:
        event = EscalationEvent(
            agent="anomaly",
            level=EscalationLevel.WARNING,
            reason=EscalationReason.LOW_CONFIDENCE,
            message="Low confidence",
            trace_id=trace_id,
            confidence=0.70,
        )
        assert event.requires_hitl() is True

    def test_zone_violation_does_not_require_hitl(self, trace_id: str) -> None:
        event = EscalationEvent(
            agent="mes",
            level=EscalationLevel.ALERT,
            reason=EscalationReason.PURDUE_ZONE_VIOLATION,
            message="Zone violation",
            trace_id=trace_id,
            confidence=0.95,
        )
        assert event.requires_hitl() is False


class TestEscalationRouter:
    def test_blocks_on_critical(self, router: EscalationRouter, trace_id: str) -> None:
        event = EscalationEvent(
            agent="safety",
            level=EscalationLevel.CRITICAL,
            reason=EscalationReason.SAFETY_INTERLOCK,
            message="E-stop",
            trace_id=trace_id,
            confidence=0.99,
        )
        assert router.evaluate(event) is True

    def test_blocks_on_low_confidence_hitl_required(
        self, router: EscalationRouter, trace_id: str
    ) -> None:
        event = EscalationEvent(
            agent="mes",
            level=EscalationLevel.WARNING,
            reason=EscalationReason.IRREVERSIBLE_ACTION,
            message="Irreversible write",
            trace_id=trace_id,
            confidence=0.70,  # below 0.85
        )
        assert router.evaluate(event) is True

    def test_does_not_block_above_threshold(self, router: EscalationRouter, trace_id: str) -> None:
        event = EscalationEvent(
            agent="telemetry",
            level=EscalationLevel.INFO,
            reason=EscalationReason.LOW_CONFIDENCE,
            message="Slightly uncertain",
            trace_id=trace_id,
            confidence=0.90,  # above 0.85
        )
        assert router.evaluate(event) is False

    def test_custom_threshold(self, trace_id: str) -> None:
        router = EscalationRouter(hitl_threshold=0.50)
        event = EscalationEvent(
            agent="x",
            level=EscalationLevel.WARNING,
            reason=EscalationReason.HUMAN_REQUIRED,
            message="Human needed",
            trace_id=trace_id,
            confidence=0.60,  # above custom threshold
        )
        assert router.evaluate(event) is False
