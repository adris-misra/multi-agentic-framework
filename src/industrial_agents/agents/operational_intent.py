"""Operational Intent Agent — parses operator NL queries into typed Intent objects."""

from __future__ import annotations

import datetime
import uuid
from typing import Any

import structlog
from pydantic import BaseModel, Field

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

_SYSTEM_PROMPT = """You are the Operational Intent agent for an industrial manufacturing facility.
Parse the operator's natural language query into a structured JSON intent.

Respond ONLY with a JSON object with these fields:
- intent_type: one of ["read_telemetry", "diagnose_anomaly", "create_work_order",
                        "query_knowledge", "safety_check", "governance_export", "unknown"]
- confidence: float 0.0-1.0
- entities: dict of extracted entities (asset_id, signal, location, etc.)
- language: ISO 639-1 code (en, es, vi supported)
- normalized_query: the query in English if translated

Supported languages: English (en), Spanish (es), Vietnamese (vi).
"""

_SUPPORTED_LANGUAGES = {"en", "es", "vi"}


class ParsedIntent(BaseModel):
    intent_type: str
    confidence: float = Field(ge=0.0, le=1.0)
    entities: dict[str, Any] = Field(default_factory=dict)
    language: str = "en"
    normalized_query: str = ""


class OperationalIntentAgent(BaseIndustrialAgent):
    role = AgentRole.OPERATIONAL_INTENT
    capabilities = [
        AgentCapability(
            name="parse_nl_intent",
            description="Parse operator natural-language query into typed Intent",
            inputs={"query": "string", "language": "string (optional)"},
            outputs={"intent_type": "string", "confidence": "float", "entities": "dict"},
            purdue_zone_required=4,
            reversibility="reversible",
        )
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

        log.info("operational_intent_handle", intent=message.intent, trace_id=message.trace_id)

        messages = [
            {"role": "user", "content": message.intent},
        ]

        response = await self._llm.complete(
            messages,
            model=None,
            temperature=0.0,
            max_tokens=512,
        )

        raw_text = ""
        for block in response.get("content", []):
            if block.get("type") == "text":
                raw_text = block["text"]
                break

        try:
            data = json.loads(raw_text)
            parsed = ParsedIntent(**data)
        except Exception:
            log.warning(
                "intent_parse_failed",
                raw=raw_text[:200],
                trace_id=message.trace_id,
            )
            parsed = ParsedIntent(
                intent_type="unknown",
                confidence=0.0,
                normalized_query=message.intent,
            )

        return AgentMessage(
            sender=self.name,
            recipient=message.sender,
            intent=parsed.intent_type,
            payload={
                "parsed_intent": parsed.model_dump(),
                "original_query": message.intent,
            },
            confidence=parsed.confidence,
            trace_id=message.trace_id,
            correlation_id=message.correlation_id,
        )
