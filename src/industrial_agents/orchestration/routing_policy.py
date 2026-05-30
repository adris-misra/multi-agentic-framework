"""Intent-based routing policy for the UNS group-chat."""

from __future__ import annotations

import re
from dataclasses import dataclass, field

import structlog

from industrial_agents.agents.base import AgentMessage, AgentRole

log = structlog.get_logger(__name__)


@dataclass
class RoutingRule:
    name: str
    # regex matched against AgentMessage.intent
    intent_pattern: str
    target_role: AgentRole
    priority: int = 0
    requires_hitl: bool = False
    _compiled: re.Pattern[str] = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self._compiled = re.compile(self.intent_pattern, re.IGNORECASE)

    def matches(self, intent: str) -> bool:
        return bool(self._compiled.search(intent))


# Default routing table (order = priority descending)
DEFAULT_RULES: list[RoutingRule] = [
    RoutingRule(
        name="safety_first",
        intent_pattern=r"(unsafe|hazard|emergency|alarm|stop|e-stop)",
        target_role=AgentRole.SAFETY_GUARDRAIL,
        priority=100,
        requires_hitl=True,
    ),
    RoutingRule(
        name="anomaly",
        intent_pattern=r"(anomal|fault|vibrat|root.?cause|diagnos|out.?of.?spec|deviation)",
        target_role=AgentRole.ANOMALY_ROOT_CAUSE,
        priority=80,
    ),
    RoutingRule(
        name="work_order",
        intent_pattern=r"(work.?order|maintenance|cmms|mes|dispatch|schedule|pm\b)",
        target_role=AgentRole.WORK_ORDER_MES,
        priority=70,
        requires_hitl=True,
    ),
    RoutingRule(
        name="tacit_knowledge",
        intent_pattern=r"(how.?to|procedure|sop|manual|best.?practice|expert|training)",
        target_role=AgentRole.TACIT_KNOWLEDGE_CURATOR,
        priority=60,
    ),
    RoutingRule(
        name="telemetry",
        intent_pattern=r"(telemetry|sensor|historian|opc|mqtt|tag|reading|value|trend)",
        target_role=AgentRole.TELEMETRY_HISTORIAN,
        priority=50,
    ),
    RoutingRule(
        name="governance",
        intent_pattern=r"(audit|lineage|compliance|cmmc|policy|sign|export)",
        target_role=AgentRole.GOVERNANCE_LINEAGE,
        priority=40,
    ),
    # Fallback: parse intent first
    RoutingRule(
        name="default",
        intent_pattern=r".*",
        target_role=AgentRole.OPERATIONAL_INTENT,
        priority=0,
    ),
]


class RoutingPolicy:
    def __init__(self, rules: list[RoutingRule] | None = None) -> None:
        self._rules = sorted(
            rules or DEFAULT_RULES, key=lambda r: r.priority, reverse=True
        )

    def route(self, message: AgentMessage) -> AgentRole:
        for rule in self._rules:
            if rule.matches(message.intent):
                log.debug(
                    "route_matched",
                    rule=rule.name,
                    intent=message.intent,
                    target=rule.target_role,
                )
                return rule.target_role
        return AgentRole.OPERATIONAL_INTENT

    def requires_hitl(self, message: AgentMessage) -> bool:
        for rule in self._rules:
            if rule.matches(message.intent) and rule.requires_hitl:
                return True
        return False
