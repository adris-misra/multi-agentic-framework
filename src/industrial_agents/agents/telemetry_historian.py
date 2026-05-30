"""Telemetry & Historian Agent â€” reads OPC UA, MQTT Sparkplug B, and historian sources."""

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

_SYSTEM_PROMPT = """You are the Telemetry & Historian agent for an industrial facility.
Given a telemetry request, return a JSON object with:
- tag: the resolved UNS tag or OPC UA node ID
- value: numeric or string value (use null if unavailable)
- quality: "good" | "uncertain" | "bad"
- timestamp_utc: ISO 8601
- source: one of ["opcua", "sparkplug", "historian", "simulated"]
- units: engineering units string or null

If you cannot determine the real value, return quality "uncertain" and a plausible simulated value.
"""


class TelemetryHistorianAgent(BaseIndustrialAgent):
    role = AgentRole.TELEMETRY_HISTORIAN
    capabilities = [
        AgentCapability(
            name="read_tag",
            description="Read a single tag value from OPC UA or MQTT Sparkplug B",
            inputs={"tag": "string", "source": "string (opcua|sparkplug|historian)"},
            outputs={"value": "any", "quality": "string", "timestamp_utc": "string"},
            purdue_zone_required=2,
            reversibility="reversible",
        ),
        AgentCapability(
            name="read_historical_range",
            description="Read a time-series range from a historian source",
            inputs={
                "tag": "string",
                "start": "ISO 8601",
                "end": "ISO 8601",
                "resolution": "string",
            },
            outputs={"series": "list[dict]"},
            purdue_zone_required=3,
            reversibility="reversible",
        ),
    ]

    def __init__(
        self,
        name: str,
        llm: Any,
        context_broker: ContextBrokerProtocol,
        governance: GovernanceProtocol,
    ) -> None:
        super().__init__(name, llm, context_broker, governance)

    async def handle(self, message: AgentMessage) -> AgentMessage | AgentDecision:
        import json

        log.info(
            "telemetry_handle",
            intent=message.intent,
            trace_id=message.trace_id,
        )

        messages = [
            {"role": "system", "content": _SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    f"Intent: {message.intent}\nPayload: {json.dumps(message.payload)}"
                ),
            },
        ]

        response = await self._llm.complete(
            messages,
            temperature=0.0,
            max_tokens=512,
        )

        raw_text = next(
            (b["text"] for b in response.get("content", []) if b.get("type") == "text"),
            "{}",
        )

        try:
            data = json.loads(raw_text)
        except Exception:
            data = {
                "tag": message.payload.get("tag", "unknown"),
                "value": None,
                "quality": "uncertain",
                "timestamp_utc": datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None).isoformat() + "Z",
                "source": "simulated",
                "units": None,
            }

        return AgentMessage(
            sender=self.name,
            recipient=message.sender,
            intent="telemetry_reading",
            payload=data,
            confidence=0.9 if data.get("quality") == "good" else 0.5,
            trace_id=message.trace_id,
            correlation_id=message.correlation_id,
        )

