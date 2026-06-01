"""Safety / Guardrail Agent — OPA policy engine, reversibility classifier, CMMC L2 gate."""

from __future__ import annotations

import datetime
import hashlib
import json
from typing import TYPE_CHECKING, Any, Self

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
    from industrial_agents.governance.opa_client import OPAClient

log = structlog.get_logger(__name__)

_SYSTEM_PROMPT = """You are the Safety & Guardrail agent for an industrial manufacturing facility.
Evaluate the proposed action for safety, reversibility, and CMMC L2 compliance.

Return a JSON object with:
- safe: bool
- allowed: bool
- reversibility: "reversible" | "soft" | "irreversible"
- cmmc_compliant: bool
- risk_level: "none" | "low" | "medium" | "high" | "critical"
- blocking_reasons: list of strings (empty if allowed)
- recommendations: list of strings

Apply these hard rules:
1. Any action on Purdue zone 0 or 1 assets requires explicit human approval -> allowed: false
2. Any irreversible action on production equipment -> allowed: false unless confidence > 0.95
3. Writing to CMMS/MES without proper authorization -> cmmc_compliant: false
4. E-stop or emergency actions -> safe: evaluate carefully, may be REQUIRED for safety
"""


class SafetyGuardrailAgent(BaseIndustrialAgent):
    role = AgentRole.SAFETY_GUARDRAIL
    capabilities = [
        AgentCapability(
            name="evaluate_action",
            description="Evaluate a proposed action for safety and policy compliance",
            inputs={
                "action": "string",
                "target_zone": "int",
                "reversibility": "string",
                "context": "dict",
            },
            outputs={
                "safe": "bool",
                "allowed": "bool",
                "reversibility": "string",
                "cmmc_compliant": "bool",
            },
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
        opa_client: OPAClient | None = None,
    ) -> None:
        super().__init__(name, llm, context_broker, governance)
        self._opa = opa_client

    async def _check_opa(self: Self, action: str, context: dict[str, Any]) -> bool | None:
        if self._opa is None:
            return None
        try:
            result = await self._opa.query(
                "data.industrial.safety.allow",
                {"action": action, "context": context},
            )
            return bool(result.get("result", False))
        except Exception as exc:
            log.warning("opa_check_failed", error=str(exc))
            return None

    async def handle(self: Self, message: AgentMessage) -> AgentMessage | AgentDecision:
        action = message.payload.get("action", message.intent)
        target_zone = int(message.payload.get("target_zone", 3))
        context = message.payload.get("context", {})

        log.info(
            "safety_guardrail_handle",
            action=action,
            target_zone=target_zone,
            trace_id=message.trace_id,
        )

        opa_result = await self._check_opa(action, context)

        messages = [
            {"role": "system", "content": _SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    f"Action: {action}\n"
                    f"Target Purdue zone: {target_zone}\n"
                    f"Context: {json.dumps(context)}\n"
                    f"OPA pre-check: {opa_result}"
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
            evaluation = json.loads(raw_text)
        except Exception:
            evaluation = {
                "safe": False,
                "allowed": False,
                "reversibility": "irreversible",
                "cmmc_compliant": False,
                "risk_level": "high",
                "blocking_reasons": ["LLM parse error — defaulting to deny"],
                "recommendations": ["Manual review required"],
            }

        if opa_result is False:
            evaluation["allowed"] = False
            evaluation["blocking_reasons"] = evaluation.get("blocking_reasons", []) + [
                "OPA policy block"
            ]

        allowed = bool(evaluation.get("allowed", False))
        confidence = 0.99 if not allowed else 0.9

        inputs_hash = hashlib.sha256(
            json.dumps({"action": action, "target_zone": target_zone}, sort_keys=True).encode()
        ).hexdigest()

        decision = AgentDecision(
            agent=self.name,
            action="allow" if allowed else "block",
            rationale="; ".join(evaluation.get("blocking_reasons", []) or ["Action approved"]),
            confidence=confidence,
            purdue_zone=4,
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
            intent="safety_evaluation",
            payload=evaluation,
            confidence=confidence,
            trace_id=message.trace_id,
            correlation_id=message.correlation_id,
        )
