"""AutoGen GroupChat orchestration wrapper for industrial agents."""

from __future__ import annotations

import uuid
from typing import Any

import structlog

from industrial_agents.agents.base import (
    AgentDecision,
    AgentMessage,
    AgentRole,
    BaseIndustrialAgent,
    ContextBrokerProtocol,
    GovernanceProtocol,
)
from industrial_agents.orchestration.escalation_grammar import (
    EscalationEvent,
    EscalationLevel,
    EscalationReason,
    EscalationRouter,
)
from industrial_agents.orchestration.routing_policy import RoutingPolicy

log = structlog.get_logger(__name__)


class IndustrialGroupChat:
    """Thin wrapper that routes AgentMessages through registered agents.

    AutoGen's GroupChat is used under the hood for multi-agent turn management;
    this class adds UNS-mediated routing, Purdue zone enforcement, and
    confidence-threshold HITL gating on top.
    """

    def __init__(
        self,
        agents: list[BaseIndustrialAgent],
        context_broker: ContextBrokerProtocol,
        governance: GovernanceProtocol,
        routing_policy: RoutingPolicy | None = None,
        escalation_router: EscalationRouter | None = None,
        max_rounds: int = 10,
    ) -> None:
        self._agents: dict[AgentRole, BaseIndustrialAgent] = {}
        for agent in agents:
            if hasattr(agent, "role"):
                self._agents[agent.role] = agent

        self._context_broker = context_broker
        self._governance = governance
        self._routing = routing_policy or RoutingPolicy()
        self._escalation = escalation_router or EscalationRouter()
        self._max_rounds = max_rounds

    def _resolve_agent(self, role: AgentRole) -> BaseIndustrialAgent | None:
        return self._agents.get(role)

    async def run(
        self,
        initial_message: AgentMessage,
    ) -> list[AgentMessage | AgentDecision]:
        trace_id = initial_message.trace_id or str(uuid.uuid4())
        history: list[AgentMessage | AgentDecision] = [initial_message]
        current: AgentMessage = initial_message

        log.info(
            "groupchat_start",
            trace_id=trace_id,
            intent=initial_message.intent,
        )

        for round_num in range(self._max_rounds):
            target_role = self._routing.route(current)
            agent = self._resolve_agent(target_role)

            if agent is None:
                log.warning(
                    "no_agent_for_role",
                    role=target_role,
                    trace_id=trace_id,
                    round=round_num,
                )
                break

            log.debug(
                "groupchat_round",
                round=round_num,
                agent=agent.name,
                intent=current.intent,
                trace_id=trace_id,
            )

            result = await agent.handle(current)
            history.append(result)

            if isinstance(result, AgentDecision):
                if result.reversibility == "irreversible":
                    event = EscalationEvent(
                        agent=agent.name,
                        level=EscalationLevel.ALERT,
                        reason=EscalationReason.IRREVERSIBLE_ACTION,
                        message=f"Irreversible action proposed: {result.action}",
                        trace_id=trace_id,
                        confidence=result.confidence,
                    )
                    if self._escalation.evaluate(event):
                        log.warning(
                            "groupchat_halted_irreversible",
                            agent=agent.name,
                            trace_id=trace_id,
                        )
                        break
                # Decision reached — emit and stop
                await agent.emit_decision(result)
                log.info(
                    "groupchat_decision",
                    agent=agent.name,
                    action=result.action,
                    confidence=result.confidence,
                    trace_id=trace_id,
                )
                break

            # Continue conversation with returned message
            current = result
            if current.intent == "DONE":
                break

        log.info(
            "groupchat_end",
            trace_id=trace_id,
            rounds=round_num + 1,
            history_len=len(history),
        )
        return history
