"""Shop-Floor Copilot Agent — role-aware operator surface (feeds the Streamlit UI)."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Self

import structlog

from industrial_agents.agents.base import (
    AgentCapability,
    AgentDecision,
    AgentMessage,
    AgentRole,
    BaseIndustrialAgent,
    ContextBrokerProtocol,
    GovernanceProtocol,
)

if TYPE_CHECKING:
    from industrial_agents.agents._llm import LLMProvider

log = structlog.get_logger(__name__)

_ROLES = {"operator", "maintenance_tech", "supervisor", "engineer", "admin"}

_SYSTEM_PROMPT = """You are the Shop-Floor Copilot for industrial manufacturing operators.
Your job is to translate complex agent responses into clear, actionable plain-English summaries
appropriate for the operator's role and skill level.

Given a context object, return a JSON with:
- summary: string (plain-English 1-3 sentence summary appropriate for the role)
- action_items: list of strings (numbered steps if action is needed)
- urgency: "info" | "action_required" | "urgent" | "emergency"
- safe_to_proceed: bool
- next_step: string (single sentence)

Adjust vocabulary: operators speak factory floor language, engineers want technical detail,
supervisors want business impact.
"""

_ROLE_GUIDANCE = {
    "operator": "Use simple, clear language. No jargon. Focus on what to do next.",
    "maintenance_tech": "Include technical details about the equipment and procedure.",
    "supervisor": "Focus on production impact, downtime risk, and recommended decision.",
    "engineer": "Include confidence scores, data sources, and technical root cause.",
    "admin": "Provide full context including compliance and governance implications.",
}


class ShopFloorCopilotAgent(BaseIndustrialAgent):
    role = AgentRole.SHOP_FLOOR_COPILOT
    capabilities = [
        AgentCapability(
            name="compose_response",
            description="Compose a role-aware plain-English response for the operator UI",
            inputs={"context": "dict", "role": "string", "locale": "string"},
            outputs={"summary": "string", "action_items": "list", "urgency": "string"},
            purdue_zone_required=4,
            reversibility="reversible",
        ),
    ]

    def __init__(
        self: Self,
        name: str,
        llm: LLMProvider,
        context_broker: ContextBrokerProtocol,
        governance: GovernanceProtocol,
    ) -> None:
        super().__init__(name, llm, context_broker, governance)

    async def handle(self: Self, message: AgentMessage) -> AgentMessage | AgentDecision:
        role = message.payload.get("role", "operator")
        if role not in _ROLES:
            role = "operator"

        context_data = message.payload.get("context", message.payload)
        role_guidance = _ROLE_GUIDANCE.get(role, _ROLE_GUIDANCE["operator"])

        log.info(
            "shop_floor_copilot_handle",
            role=role,
            trace_id=message.trace_id,
        )

        messages = [
            {
                "role": "system",
                "content": _SYSTEM_PROMPT + f"\n\nRole guidance: {role_guidance}",
            },
            {
                "role": "user",
                "content": (
                    f"Operator role: {role}\n"
                    f"Intent: {message.intent}\n"
                    f"Context: {json.dumps(context_data, default=str)}"
                ),
            },
        ]

        response = await self._llm.complete(messages, temperature=0.3, max_tokens=1024)
        raw_text = next(
            (b["text"] for b in response.get("content", []) if b.get("type") == "text"),
            "{}",
        )

        try:
            composed = json.loads(raw_text)
        except Exception:
            composed = {
                "summary": raw_text[:500],
                "action_items": [],
                "urgency": "info",
                "safe_to_proceed": True,
                "next_step": "Review with your supervisor.",
            }

        return AgentMessage(
            sender=self.name,
            recipient=message.sender,
            intent="copilot_response",
            payload={"response": composed, "role": role},
            confidence=0.9,
            trace_id=message.trace_id,
            correlation_id=message.correlation_id,
        )
