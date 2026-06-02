"""Base agent contracts for the Industrial Agentic Intelligence Framework."""

from __future__ import annotations

import hashlib
import json
from abc import ABC, abstractmethod
from enum import StrEnum
from typing import TYPE_CHECKING, Any, Protocol, Self, runtime_checkable

from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from industrial_agents.agents._llm import LLMProvider


class AgentRole(StrEnum):
    OPERATIONAL_INTENT = "operational_intent"
    UNS_CONTEXT_BROKER = "uns_context_broker"
    TELEMETRY_HISTORIAN = "telemetry_historian"
    ANOMALY_ROOT_CAUSE = "anomaly_root_cause"
    TACIT_KNOWLEDGE_CURATOR = "tacit_knowledge_curator"
    SAFETY_GUARDRAIL = "safety_guardrail"
    WORK_ORDER_MES = "work_order_mes"
    GOVERNANCE_LINEAGE = "governance_lineage"
    HITL_SUPERVISOR = "hitl_supervisor"
    SHOP_FLOOR_COPILOT = "shop_floor_copilot"


class AgentCapability(BaseModel):
    name: str
    description: str
    inputs: dict[str, str]
    outputs: dict[str, str]
    purdue_zone_required: int = Field(ge=0, le=5)
    reversibility: str = Field(pattern=r"^(reversible|soft|irreversible)$")


class AgentMessage(BaseModel):
    sender: str
    recipient: str | None = None
    intent: str
    payload: dict[str, Any] = Field(default_factory=dict)
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    trace_id: str
    correlation_id: str | None = None

    def inputs_hash(self: Self) -> str:
        canonical = json.dumps(
            {"sender": self.sender, "intent": self.intent, "payload": self.payload},
            sort_keys=True,
        )
        return hashlib.sha256(canonical.encode()).hexdigest()


class AgentDecision(BaseModel):
    agent: str
    action: str
    rationale: str
    confidence: float = Field(ge=0.0, le=1.0)
    purdue_zone: int = Field(ge=0, le=5)
    reversibility: str = Field(pattern=r"^(reversible|soft|irreversible)$")
    trace_id: str
    inputs_hash: str
    timestamp_utc: str
    signature: str | None = None


@runtime_checkable
class ContextBrokerProtocol(Protocol):
    async def resolve_path(self: Self, path: str) -> dict[str, Any]: ...

    async def validate_zone(self: Self, agent_zone: int, target_zone: int) -> bool: ...

    async def publish(self: Self, topic: str, payload: dict[str, Any]) -> None: ...


@runtime_checkable
class GovernanceProtocol(Protocol):
    async def emit_lineage(self: Self, decision: AgentDecision) -> None: ...

    async def sign_decision(self: Self, decision: AgentDecision) -> str: ...

    async def check_policy(self: Self, action: str, context: dict[str, Any]) -> bool: ...


class BaseIndustrialAgent(ABC):
    name: str
    role: AgentRole
    capabilities: list[AgentCapability]

    def __init__(
        self: Self,
        name: str,
        llm: LLMProvider,
        context_broker: ContextBrokerProtocol,
        governance: GovernanceProtocol,
    ) -> None:
        self.name = name
        self._llm = llm
        self._context_broker = context_broker
        self._governance = governance

    @abstractmethod
    async def handle(self: Self, message: AgentMessage) -> AgentMessage | AgentDecision: ...

    async def emit_decision(self: Self, decision: AgentDecision) -> None:
        decision.signature = await self._governance.sign_decision(decision)
        await self._governance.emit_lineage(decision)
