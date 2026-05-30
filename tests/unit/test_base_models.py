"""Unit tests for AgentCapability, AgentMessage, AgentDecision models."""

from __future__ import annotations

import uuid

import pytest
from pydantic import ValidationError

from industrial_agents.agents.base import AgentCapability, AgentDecision, AgentMessage


class TestAgentCapability:
    def test_valid_capability(self) -> None:
        cap = AgentCapability(
            name="read_opc_tag",
            description="Reads a single OPC UA tag value",
            inputs={"node_id": "string"},
            outputs={"value": "float", "quality": "string"},
            purdue_zone_required=2,
            reversibility="reversible",
        )
        assert cap.purdue_zone_required == 2

    def test_purdue_zone_out_of_range(self) -> None:
        with pytest.raises(ValidationError):
            AgentCapability(
                name="bad",
                description="bad",
                inputs={},
                outputs={},
                purdue_zone_required=6,  # max is 5
                reversibility="reversible",
            )

    def test_invalid_reversibility(self) -> None:
        with pytest.raises(ValidationError):
            AgentCapability(
                name="bad",
                description="bad",
                inputs={},
                outputs={},
                purdue_zone_required=3,
                reversibility="maybe",  # not in enum
            )


class TestAgentMessage:
    def test_defaults(self) -> None:
        msg = AgentMessage(sender="agent_a", intent="diagnose fault", trace_id="t1")
        assert msg.confidence == 1.0
        assert msg.recipient is None
        assert msg.correlation_id is None

    def test_confidence_bounds(self) -> None:
        with pytest.raises(ValidationError):
            AgentMessage(sender="a", intent="x", trace_id="t", confidence=1.5)

    def test_inputs_hash_deterministic(self) -> None:
        tid = str(uuid.uuid4())
        m1 = AgentMessage(sender="a", intent="foo", trace_id=tid, payload={"k": 1})
        m2 = AgentMessage(sender="a", intent="foo", trace_id=tid, payload={"k": 1})
        assert m1.inputs_hash() == m2.inputs_hash()

    def test_inputs_hash_differs_on_payload(self) -> None:
        tid = str(uuid.uuid4())
        m1 = AgentMessage(sender="a", intent="foo", trace_id=tid, payload={"k": 1})
        m2 = AgentMessage(sender="a", intent="foo", trace_id=tid, payload={"k": 2})
        assert m1.inputs_hash() != m2.inputs_hash()


class TestAgentDecision:
    def test_valid_decision(self, sample_decision: AgentDecision) -> None:
        assert sample_decision.signature is None
        assert sample_decision.reversibility == "reversible"

    def test_confidence_too_low(self) -> None:
        with pytest.raises(ValidationError):
            AgentDecision(
                agent="x",
                action="y",
                rationale="z",
                confidence=-0.1,
                purdue_zone=3,
                reversibility="reversible",
                trace_id="t",
                inputs_hash="h" * 64,
                timestamp_utc="2026-01-01T00:00:00Z",
            )

    def test_purdue_zone_bounds(self) -> None:
        with pytest.raises(ValidationError):
            AgentDecision(
                agent="x",
                action="y",
                rationale="z",
                confidence=0.9,
                purdue_zone=7,  # invalid
                reversibility="soft",
                trace_id="t",
                inputs_hash="h" * 64,
                timestamp_utc="2026-01-01T00:00:00Z",
            )
