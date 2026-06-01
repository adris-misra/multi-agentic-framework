"""Anomaly & Root-Cause Agent — multivariate anomaly detection + FMEA traversal."""

from __future__ import annotations

import datetime
import hashlib
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

_SYSTEM_PROMPT = """You are the Anomaly & Root-Cause agent for an industrial facility.
Given sensor data or an anomaly description, return a JSON object with:
- anomaly_detected: bool
- anomaly_type: string (e.g. "vibration_spike", "thermal_runaway", "pressure_drop")
- confidence: float 0.0-1.0
- root_cause: string (most likely explanation)
- fmea_reference: string or null (FMEA failure mode ID if applicable)
- recommended_action: string
- severity: "low" | "medium" | "high" | "critical"
- affected_assets: list of asset IDs

Use FMEA methodology. Be concise and specific.
"""


class AnomalyRootCauseAgent(BaseIndustrialAgent):
    role = AgentRole.ANOMALY_ROOT_CAUSE
    capabilities = [
        AgentCapability(
            name="detect_anomaly",
            description=(
                "Detect anomalies in time-series data using Matrix Profile + Isolation Forest"
            ),
            inputs={"series": "list[dict]", "asset_id": "string"},
            outputs={"anomaly_detected": "bool", "anomaly_type": "string", "confidence": "float"},
            purdue_zone_required=3,
            reversibility="reversible",
        ),
        AgentCapability(
            name="fmea_traversal",
            description="Traverse FMEA tree to find root cause for a given failure mode",
            inputs={"failure_description": "string", "asset_class": "string"},
            outputs={"root_cause": "string", "fmea_reference": "string"},
            purdue_zone_required=3,
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
        log.info(
            "anomaly_handle",
            intent=message.intent,
            trace_id=message.trace_id,
        )

        messages = [
            {"role": "system", "content": _SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (f"Intent: {message.intent}\nPayload: {json.dumps(message.payload)}"),
            },
        ]

        response = await self._llm.complete(
            messages,
            temperature=0.1,
            max_tokens=1024,
        )

        raw_text = next(
            (b["text"] for b in response.get("content", []) if b.get("type") == "text"),
            "{}",
        )

        try:
            analysis = json.loads(raw_text)
        except Exception:
            analysis = {
                "anomaly_detected": False,
                "anomaly_type": "unknown",
                "confidence": 0.0,
                "root_cause": "LLM parse error",
                "fmea_reference": None,
                "recommended_action": "Escalate to maintenance engineer",
                "severity": "low",
                "affected_assets": [],
            }

        confidence = float(analysis.get("confidence", 0.0))
        severity = analysis.get("severity", "low")
        anomaly_detected = bool(analysis.get("anomaly_detected", False))

        if anomaly_detected and severity in {"high", "critical"}:
            inputs_hash = hashlib.sha256(
                json.dumps(message.payload, sort_keys=True).encode()
            ).hexdigest()

            decision = AgentDecision(
                agent=self.name,
                action=f"anomaly_alert:{analysis.get('anomaly_type', 'unknown')}",
                rationale=analysis.get("root_cause", ""),
                confidence=confidence,
                purdue_zone=3,
                reversibility="reversible",
                trace_id=message.trace_id,
                inputs_hash=inputs_hash,
                timestamp_utc=datetime.datetime.now(datetime.UTC)
                .replace(tzinfo=None)
                .isoformat()
                + "Z",
            )
            await self.emit_decision(decision)

        return AgentMessage(
            sender=self.name,
            recipient=message.sender,
            intent="anomaly_analysis",
            payload=analysis,
            confidence=confidence,
            trace_id=message.trace_id,
            correlation_id=message.correlation_id,
        )
