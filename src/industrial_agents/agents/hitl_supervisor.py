"""HITL Supervisor Agent â€” confidence-threshold human routing via Slack/Teams/email."""

from __future__ import annotations

import datetime
from typing import Any

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

log = structlog.get_logger(__name__)


class HITLSupervisorAgent(BaseIndustrialAgent):
    role = AgentRole.HITL_SUPERVISOR
    capabilities = [
        AgentCapability(
            name="route_to_human",
            description="Route a decision to a human operator for review and approval",
            inputs={
                "decision": "dict",
                "channel": "slack|teams|email",
                "urgency": "low|medium|high|critical",
            },
            outputs={"routed": "bool", "notification_id": "string"},
            purdue_zone_required=4,
            reversibility="reversible",
        ),
    ]

    def __init__(
        self,
        name: str,
        llm: Any,
        context_broker: ContextBrokerProtocol,
        governance: GovernanceProtocol,
        confidence_threshold: float = 0.85,
        slack_webhook: str | None = None,
        teams_webhook: str | None = None,
        email_to: str | None = None,
    ) -> None:
        super().__init__(name, llm, context_broker, governance)
        self._threshold = confidence_threshold
        self._slack_webhook = slack_webhook
        self._teams_webhook = teams_webhook
        self._email_to = email_to
        self._pending: list[dict[str, Any]] = []

    def _needs_hitl(self, message: AgentMessage) -> bool:
        return message.confidence < self._threshold

    async def _notify_slack(self, text: str) -> bool:
        if self._slack_webhook is None:
            return False
        try:
            import aiohttp

            async with aiohttp.ClientSession() as session:
                resp = await session.post(
                    self._slack_webhook,
                    json={"text": text},
                    timeout=aiohttp.ClientTimeout(total=5),
                )
                return resp.status == 200
        except Exception as exc:
            log.warning("slack_notify_failed", error=str(exc))
            return False

    async def handle(self, message: AgentMessage) -> AgentMessage | AgentDecision:
        log.info(
            "hitl_supervisor_handle",
            confidence=message.confidence,
            threshold=self._threshold,
            trace_id=message.trace_id,
        )

        if not self._needs_hitl(message):
            return AgentMessage(
                sender=self.name,
                recipient=message.sender,
                intent="hitl_not_required",
                payload={"reason": f"Confidence {message.confidence:.2f} >= {self._threshold}"},
                confidence=1.0,
                trace_id=message.trace_id,
                correlation_id=message.correlation_id,
            )

        notification_id = f"HITL-{message.trace_id[:8]}"
        pending_entry: dict[str, Any] = {
            "notification_id": notification_id,
            "trace_id": message.trace_id,
            "intent": message.intent,
            "confidence": message.confidence,
            "payload": message.payload,
            "created_utc": datetime.datetime.now(datetime.UTC)
            .replace(tzinfo=None)
            .isoformat()
            + "Z",
            "status": "pending",
        }
        self._pending.append(pending_entry)

        notify_text = (
            f":warning: *HITL Review Required* [{notification_id}]\n"
            f"Intent: `{message.intent}`\n"
            f"Confidence: `{message.confidence:.2f}` (threshold: {self._threshold})\n"
            f"Trace: `{message.trace_id}`"
        )

        notified = await self._notify_slack(notify_text)

        log.warning(
            "hitl_routed_to_human",
            notification_id=notification_id,
            confidence=message.confidence,
            notified=notified,
            trace_id=message.trace_id,
        )

        return AgentMessage(
            sender=self.name,
            recipient=message.sender,
            intent="hitl_pending",
            payload={
                "notification_id": notification_id,
                "routed": True,
                "notified": notified,
                "reason": f"Confidence {message.confidence:.2f} below threshold {self._threshold}",
            },
            confidence=1.0,
            trace_id=message.trace_id,
            correlation_id=message.correlation_id,
        )
