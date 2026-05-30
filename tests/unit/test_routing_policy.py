"""Unit tests for RoutingPolicy."""

from __future__ import annotations

import pytest

from industrial_agents.agents.base import AgentMessage, AgentRole
from industrial_agents.orchestration.routing_policy import RoutingPolicy, RoutingRule


@pytest.fixture
def policy() -> RoutingPolicy:
    return RoutingPolicy()


class TestRoutingPolicy:
    def test_safety_intent_routes_to_safety_agent(
        self, policy: RoutingPolicy, trace_id: str
    ) -> None:
        msg = AgentMessage(sender="cli", intent="e-stop triggered on line 3", trace_id=trace_id)
        assert policy.route(msg) == AgentRole.SAFETY_GUARDRAIL

    def test_anomaly_intent_routes_to_anomaly_agent(
        self, policy: RoutingPolicy, trace_id: str
    ) -> None:
        msg = AgentMessage(
            sender="cli", intent="vibration anomaly on spindle motor", trace_id=trace_id
        )
        assert policy.route(msg) == AgentRole.ANOMALY_ROOT_CAUSE

    def test_work_order_routes_correctly(self, policy: RoutingPolicy, trace_id: str) -> None:
        msg = AgentMessage(
            sender="cli", intent="create work order for PM on press 4", trace_id=trace_id
        )
        assert policy.route(msg) == AgentRole.WORK_ORDER_MES

    def test_telemetry_intent(self, policy: RoutingPolicy, trace_id: str) -> None:
        msg = AgentMessage(
            sender="cli", intent="get OPC UA tag value for sensor ns=2;i=1001", trace_id=trace_id
        )
        assert policy.route(msg) == AgentRole.TELEMETRY_HISTORIAN

    def test_sop_intent_routes_to_tacit_knowledge(
        self, policy: RoutingPolicy, trace_id: str
    ) -> None:
        msg = AgentMessage(
            sender="cli", intent="what is the procedure for changeover?", trace_id=trace_id
        )
        assert policy.route(msg) == AgentRole.TACIT_KNOWLEDGE_CURATOR

    def test_unknown_intent_falls_back_to_operational_intent(
        self, policy: RoutingPolicy, trace_id: str
    ) -> None:
        msg = AgentMessage(sender="cli", intent="hello", trace_id=trace_id)
        assert policy.route(msg) == AgentRole.OPERATIONAL_INTENT

    def test_safety_requires_hitl(self, policy: RoutingPolicy, trace_id: str) -> None:
        msg = AgentMessage(sender="cli", intent="emergency stop", trace_id=trace_id)
        assert policy.requires_hitl(msg) is True

    def test_telemetry_does_not_require_hitl(self, policy: RoutingPolicy, trace_id: str) -> None:
        msg = AgentMessage(sender="cli", intent="get sensor reading", trace_id=trace_id)
        assert policy.requires_hitl(msg) is False

    def test_safety_beats_anomaly_by_priority(self, policy: RoutingPolicy, trace_id: str) -> None:
        msg = AgentMessage(
            sender="cli",
            intent="hazardous vibration anomaly — emergency shutdown",
            trace_id=trace_id,
        )
        # safety_first rule has priority 100 > anomaly 80
        assert policy.route(msg) == AgentRole.SAFETY_GUARDRAIL

    def test_custom_rules_override_defaults(self, trace_id: str) -> None:
        custom = [
            RoutingRule(
                name="custom_telemetry",
                intent_pattern=r"foo",
                target_role=AgentRole.TELEMETRY_HISTORIAN,
                priority=99,
            )
        ]
        p = RoutingPolicy(rules=custom)
        msg = AgentMessage(sender="cli", intent="foo bar", trace_id=trace_id)
        assert p.route(msg) == AgentRole.TELEMETRY_HISTORIAN
