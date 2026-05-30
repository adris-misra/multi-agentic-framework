"""Shared fixtures for unit tests."""

from __future__ import annotations

import uuid
from typing import Any
from unittest.mock import AsyncMock

import pytest

from industrial_agents.agents.base import (
    AgentDecision,
    AgentMessage,
    ContextBrokerProtocol,
    GovernanceProtocol,
)


@pytest.fixture()
def trace_id() -> str:
    return str(uuid.uuid4())


@pytest.fixture()
def sample_message(trace_id: str) -> AgentMessage:
    return AgentMessage(
        sender="test",
        intent="check motor vibration anomaly",
        trace_id=trace_id,
    )


@pytest.fixture()
def mock_context_broker() -> ContextBrokerProtocol:
    broker = AsyncMock(spec=ContextBrokerProtocol)
    broker.validate_zone.return_value = True
    broker.resolve_path.return_value = {"node_id": "ns=2;i=1001", "value": 42.0}
    return broker  # type: ignore[return-value]


@pytest.fixture()
def mock_governance() -> GovernanceProtocol:
    gov = AsyncMock(spec=GovernanceProtocol)
    gov.sign_decision.return_value = "fake-signature-abc123"
    gov.check_policy.return_value = True
    return gov  # type: ignore[return-value]


@pytest.fixture()
def sample_decision(trace_id: str) -> AgentDecision:
    return AgentDecision(
        agent="test_agent",
        action="log_anomaly",
        rationale="Vibration exceeded 2σ threshold",
        confidence=0.92,
        purdue_zone=3,
        reversibility="reversible",
        trace_id=trace_id,
        inputs_hash="abc" * 20 + "ab",
        timestamp_utc="2026-05-29T00:00:00Z",
    )


@pytest.fixture()
def mock_llm() -> Any:
    llm = AsyncMock()
    llm.complete.return_value = {
        "content": [{"type": "text", "text": "Anomaly detected in spindle motor."}],
        "model": "test-model",
        "stop_reason": "end_turn",
        "usage": {"input_tokens": 100, "output_tokens": 50},
    }
    return llm
