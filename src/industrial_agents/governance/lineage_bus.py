"""Immutable OpenLineage lineage bus with Ed25519 signing."""

from __future__ import annotations

from typing import Any, Self

import structlog

from industrial_agents.agents.base import AgentDecision, GovernanceProtocol
from industrial_agents.agents.governance_lineage import GovernanceLineageAgent

log = structlog.get_logger(__name__)


class LineageBus(GovernanceProtocol):
    """Central governance bus that wires GovernanceLineageAgent as a Protocol impl.

    Used by BaseIndustrialAgent.emit_decision() for all agents in the group chat.
    """

    def __init__(
        self: Self,
        governance_agent: GovernanceLineageAgent | None = None,
        signing_key_path: str | None = None,
    ) -> None:
        self._agent = governance_agent
        self._signing_key_path = signing_key_path

    async def emit_lineage(self: Self, decision: AgentDecision) -> None:
        if self._agent is not None:
            await self._agent.emit_lineage(decision)
        else:
            log.info(
                "lineage_emit_no_agent",
                agent=decision.agent,
                action=decision.action,
                trace_id=decision.trace_id,
            )

    async def sign_decision(self: Self, decision: AgentDecision) -> str:
        if self._agent is not None:
            return self._agent.sign_decision(decision)
        # Fallback: unsigned placeholder
        import hashlib

        return "unsigned:" + hashlib.sha256(decision.inputs_hash.encode()).hexdigest()[:16]

    async def check_policy(self: Self, action: str, context: dict[str, Any]) -> bool:
        if (
            self._agent is not None
            and hasattr(self._agent, "_opa")
            and self._agent._opa is not None
        ):
            try:
                result = await self._agent._opa.query(
                    "data.industrial.safety.allow",
                    {"action": action, "context": context},
                )
                return bool(result.get("result", True))
            except Exception as exc:
                log.warning("lineage_bus_policy_check_error", error=str(exc))
        return True

    def get_audit_log(self: Self) -> list[dict[str, Any]]:
        if self._agent is not None:
            return list(self._agent._audit_log)
        return []
