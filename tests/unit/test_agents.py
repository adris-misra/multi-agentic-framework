"""Unit tests for all 10 industrial agents."""

from __future__ import annotations

import json
from typing import Any
from unittest.mock import AsyncMock

import pytest

from industrial_agents.agents.base import AgentDecision, AgentMessage
from industrial_agents.agents.governance_lineage import GovernanceLineageAgent
from industrial_agents.agents.hitl_supervisor import HITLSupervisorAgent
from industrial_agents.agents.operational_intent import OperationalIntentAgent
from industrial_agents.agents.telemetry_historian import TelemetryHistorianAgent
from industrial_agents.agents.uns_context_broker import UNSContextBrokerAgent
from industrial_agents.agents.work_order_mes import WorkOrderMESAgent


def _make_agent(cls: type, name: str, llm: Any, broker: Any, gov: Any, **kwargs: Any) -> Any:
    return cls(name=name, llm=llm, context_broker=broker, governance=gov, **kwargs)


class TestOperationalIntentAgent:
    @pytest.mark.asyncio()
    async def test_parse_intent_returns_message(
        self,
        mock_llm: AsyncMock,
        mock_context_broker: Any,
        mock_governance: Any,
        sample_message: AgentMessage,
    ) -> None:
        mock_llm.complete.return_value = {
            "content": [
                {
                    "type": "text",
                    "text": json.dumps(
                        {
                            "intent_type": "diagnose_anomaly",
                            "confidence": 0.91,
                            "entities": {"asset": "motor_1"},
                            "language": "en",
                            "normalized_query": "check motor vibration anomaly",
                        }
                    ),
                }
            ],
            "model": "test",
            "stop_reason": "end_turn",
            "usage": {},
        }
        agent = _make_agent(
            OperationalIntentAgent, "oi", mock_llm, mock_context_broker, mock_governance
        )
        result = await agent.handle(sample_message)
        assert isinstance(result, AgentMessage)
        assert result.intent == "diagnose_anomaly"
        assert result.confidence == pytest.approx(0.91)

    @pytest.mark.asyncio()
    async def test_parse_intent_fallback_on_bad_json(
        self,
        mock_llm: AsyncMock,
        mock_context_broker: Any,
        mock_governance: Any,
        sample_message: AgentMessage,
    ) -> None:
        mock_llm.complete.return_value = {
            "content": [{"type": "text", "text": "not json"}],
            "model": "test",
            "stop_reason": "end_turn",
            "usage": {},
        }
        agent = _make_agent(
            OperationalIntentAgent, "oi", mock_llm, mock_context_broker, mock_governance
        )
        result = await agent.handle(sample_message)
        assert isinstance(result, AgentMessage)
        assert result.intent == "unknown"


class TestUNSContextBrokerAgent:
    def test_resolve_sparkplug_path(
        self, mock_llm: Any, mock_context_broker: Any, mock_governance: Any
    ) -> None:
        agent = _make_agent(
            UNSContextBrokerAgent, "uns", mock_llm, mock_context_broker, mock_governance
        )
        r = agent.resolve_path("spBv1.0/Chicago/NDATA/line1/motor1")
        assert r.sparkplug is True
        assert r.resolved is True
        assert r.group_id == "Chicago"
        assert r.edge_node_id == "line1"
        assert r.device_id == "motor1"

    def test_resolve_isa95_path(
        self, mock_llm: Any, mock_context_broker: Any, mock_governance: Any
    ) -> None:
        agent = _make_agent(
            UNSContextBrokerAgent, "uns", mock_llm, mock_context_broker, mock_governance
        )
        r = agent.resolve_path("acme/chicago/area1/line1/cell1/motor1")
        assert r.sparkplug is False
        assert r.resolved is True

    def test_resolve_unknown_path(
        self, mock_llm: Any, mock_context_broker: Any, mock_governance: Any
    ) -> None:
        agent = _make_agent(
            UNSContextBrokerAgent, "uns", mock_llm, mock_context_broker, mock_governance
        )
        r = agent.resolve_path("not-a-valid-path-at-all!")
        assert r.resolved is False

    def test_validate_zone_blocks_low_zone(
        self, mock_llm: Any, mock_context_broker: Any, mock_governance: Any
    ) -> None:
        agent = _make_agent(
            UNSContextBrokerAgent,
            "uns",
            mock_llm,
            mock_context_broker,
            mock_governance,
            write_gate_zone_threshold=2,
        )
        assert agent.validate_zone(agent_zone=3, target_zone=1) is False

    def test_validate_zone_allows_zone3(
        self, mock_llm: Any, mock_context_broker: Any, mock_governance: Any
    ) -> None:
        agent = _make_agent(
            UNSContextBrokerAgent, "uns", mock_llm, mock_context_broker, mock_governance
        )
        assert agent.validate_zone(agent_zone=3, target_zone=3) is True


class TestHITLSupervisorAgent:
    @pytest.mark.asyncio()
    async def test_routes_when_below_threshold(
        self,
        mock_llm: Any,
        mock_context_broker: Any,
        mock_governance: Any,
        trace_id: str,
    ) -> None:
        agent = _make_agent(
            HITLSupervisorAgent,
            "hitl",
            mock_llm,
            mock_context_broker,
            mock_governance,
            confidence_threshold=0.85,
        )
        low_conf_msg = AgentMessage(
            sender="anomaly",
            intent="check fault",
            trace_id=trace_id,
            confidence=0.60,
        )
        result = await agent.handle(low_conf_msg)
        assert isinstance(result, AgentMessage)
        assert result.intent == "hitl_pending"
        assert result.payload["routed"] is True

    @pytest.mark.asyncio()
    async def test_passes_when_above_threshold(
        self,
        mock_llm: Any,
        mock_context_broker: Any,
        mock_governance: Any,
        trace_id: str,
    ) -> None:
        agent = _make_agent(
            HITLSupervisorAgent,
            "hitl",
            mock_llm,
            mock_context_broker,
            mock_governance,
            confidence_threshold=0.85,
        )
        high_conf_msg = AgentMessage(
            sender="anomaly",
            intent="check fault",
            trace_id=trace_id,
            confidence=0.95,
        )
        result = await agent.handle(high_conf_msg)
        assert isinstance(result, AgentMessage)
        assert result.intent == "hitl_not_required"


class TestGovernanceLineageAgent:
    def test_sign_decision_without_key(
        self,
        mock_llm: Any,
        mock_context_broker: Any,
        mock_governance: Any,
        sample_decision: AgentDecision,
    ) -> None:
        agent = _make_agent(
            GovernanceLineageAgent,
            "gov",
            mock_llm,
            mock_context_broker,
            mock_governance,
            signing_key_path=None,
        )
        sig = agent.sign_decision(sample_decision)
        assert sig.startswith("unsigned:")

    @pytest.mark.asyncio()
    async def test_emit_lineage_stores_event(
        self,
        mock_llm: Any,
        mock_context_broker: Any,
        mock_governance: Any,
        sample_decision: AgentDecision,
    ) -> None:
        agent = _make_agent(
            GovernanceLineageAgent,
            "gov",
            mock_llm,
            mock_context_broker,
            mock_governance,
        )
        await agent.emit_lineage(sample_decision)
        assert len(agent._audit_log) == 1
        event = agent._audit_log[0]
        assert event["run"]["runId"] == sample_decision.trace_id


class TestTelemetryHistorianAgent:
    @pytest.mark.asyncio()
    async def test_returns_telemetry_message(
        self,
        mock_llm: AsyncMock,
        mock_context_broker: Any,
        mock_governance: Any,
        trace_id: str,
    ) -> None:
        mock_llm.complete.return_value = {
            "content": [
                {
                    "type": "text",
                    "text": json.dumps(
                        {
                            "tag": "acme/chicago/line1/motor1/vibration",
                            "value": 1.23,
                            "quality": "good",
                            "timestamp_utc": "2026-05-29T00:00:00Z",
                            "source": "opcua",
                            "units": "mm/s",
                        }
                    ),
                }
            ],
            "model": "test",
            "stop_reason": "end_turn",
            "usage": {},
        }
        agent = _make_agent(
            TelemetryHistorianAgent, "tel", mock_llm, mock_context_broker, mock_governance
        )
        msg = AgentMessage(
            sender="cli",
            intent="read vibration",
            trace_id=trace_id,
            payload={"tag": "acme/chicago/line1/motor1/vibration"},
        )
        result = await agent.handle(msg)
        assert isinstance(result, AgentMessage)
        assert result.payload.get("quality") == "good"
        assert result.confidence == pytest.approx(0.9)


class TestWorkOrderMESAgent:
    @pytest.mark.asyncio()
    async def test_create_work_order(
        self,
        mock_llm: AsyncMock,
        mock_context_broker: Any,
        mock_governance: Any,
        trace_id: str,
    ) -> None:
        mock_llm.complete.return_value = {
            "content": [
                {
                    "type": "text",
                    "text": json.dumps(
                        {
                            "work_order_id": "WO-abc123",
                            "asset_id": "motor_1",
                            "work_type": "corrective",
                            "priority": "high",
                            "description": "Replace bearing",
                            "estimated_hours": 3.0,
                            "required_skills": ["mechanic"],
                            "required_parts": [{"part_number": "BRG-001", "quantity": 2}],
                            "safety_precautions": ["LOTO required"],
                            "idempotency_key": "abc123",
                        }
                    ),
                }
            ],
            "model": "test",
            "stop_reason": "end_turn",
            "usage": {},
        }
        agent = _make_agent(WorkOrderMESAgent, "wo", mock_llm, mock_context_broker, mock_governance)
        msg = AgentMessage(
            sender="cli",
            intent="replace bearing on motor 1",
            trace_id=trace_id,
            payload={"asset_id": "motor_1", "description": "Replace bearing", "action": "create"},
        )
        result = await agent.handle(msg)
        assert isinstance(result, AgentMessage)
        assert result.intent == "work_order_created"
        assert "work_order" in result.payload

    @pytest.mark.asyncio()
    async def test_idempotent_on_second_call(
        self,
        mock_llm: AsyncMock,
        mock_context_broker: Any,
        mock_governance: Any,
        trace_id: str,
    ) -> None:
        mock_llm.complete.return_value = {
            "content": [{"type": "text", "text": json.dumps({"work_order_id": "WO-x"})}],
            "model": "test",
            "stop_reason": "end_turn",
            "usage": {},
        }
        agent = _make_agent(WorkOrderMESAgent, "wo", mock_llm, mock_context_broker, mock_governance)
        payload = {"asset_id": "motor_1", "description": "Same job", "action": "create"}
        msg1 = AgentMessage(sender="cli", intent="x", trace_id=trace_id, payload=payload)
        msg2 = AgentMessage(sender="cli", intent="x", trace_id=trace_id, payload=payload)

        await agent.handle(msg1)
        result2 = await agent.handle(msg2)
        assert isinstance(result2, AgentMessage)
        assert result2.payload.get("idempotent") is True
        assert mock_llm.complete.call_count == 1
