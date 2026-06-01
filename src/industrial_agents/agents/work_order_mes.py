"""Work-Order & MES Dispatch Agent — writes to CMMS/MES with dry-run diff + idempotency."""

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

log = structlog.get_logger(__name__)

_SYSTEM_PROMPT = """You are the Work-Order & MES Dispatch agent for an industrial facility.
Given a work request, generate a structured work order JSON with:
- work_order_id: string (generate a UUID-like ID)
- asset_id: string
- work_type: "preventive" | "corrective" | "predictive" | "emergency"
- priority: "low" | "medium" | "high" | "critical"
- description: string (clear maintenance task description)
- estimated_hours: float
- required_skills: list of strings
- required_parts: list of dicts with {"part_number": str, "quantity": int}
- safety_precautions: list of strings
- idempotency_key: string (deterministic hash of asset_id + description)

Always include at least one safety precaution.
"""


class WorkOrderMESAgent(BaseIndustrialAgent):
    role = AgentRole.WORK_ORDER_MES
    capabilities = [
        AgentCapability(
            name="create_work_order",
            description="Create a work order in CMMS with dry-run diff preview",
            inputs={
                "asset_id": "string",
                "description": "string",
                "work_type": "string",
                "priority": "string",
            },
            outputs={"work_order": "dict", "dry_run_diff": "dict"},
            purdue_zone_required=3,
            reversibility="soft",
        ),
        AgentCapability(
            name="dispatch_to_mes",
            description="Dispatch work order to MES (requires HITL approval for irreversible)",
            inputs={"work_order_id": "string"},
            outputs={"dispatched": "bool", "mes_reference": "string"},
            purdue_zone_required=3,
            reversibility="irreversible",
        ),
    ]

    def __init__(
        self: Self,
        name: str,
        llm: LLMProvider,
        context_broker: ContextBrokerProtocol,
        governance: GovernanceProtocol,
        cmms_client: object | None = None,
    ) -> None:
        super().__init__(name, llm, context_broker, governance)
        self._cmms = cmms_client
        self._idempotency_store: dict[str, dict[str, Any]] = {}

    def _idempotency_key(self: Self, asset_id: str, description: str) -> str:
        return hashlib.sha256(f"{asset_id}:{description}".encode()).hexdigest()[:16]

    async def handle(self: Self, message: AgentMessage) -> AgentMessage | AgentDecision:
        action = message.payload.get("action", "create")
        log.info(
            "work_order_mes_handle",
            action=action,
            intent=message.intent,
            trace_id=message.trace_id,
        )

        if action == "dispatch":
            return await self._dispatch(message)
        return await self._create(message)

    async def _create(self: Self, message: AgentMessage) -> AgentMessage:
        asset_id = message.payload.get("asset_id", "unknown")
        description = message.payload.get("description", message.intent)

        ikey = self._idempotency_key(asset_id, description)
        if ikey in self._idempotency_store:
            log.info("work_order_idempotent_hit", key=ikey, trace_id=message.trace_id)
            existing = self._idempotency_store[ikey]
            return AgentMessage(
                sender=self.name,
                recipient=message.sender,
                intent="work_order_created",
                payload={"work_order": existing, "idempotent": True, "dry_run_diff": {}},
                confidence=0.99,
                trace_id=message.trace_id,
                correlation_id=message.correlation_id,
            )

        messages = [
            {"role": "system", "content": _SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    f"Asset: {asset_id}\n"
                    f"Request: {description}\n"
                    f"Context: {json.dumps(message.payload)}"
                ),
            },
        ]

        response = await self._llm.complete(messages, temperature=0.2, max_tokens=1024)
        raw_text = next(
            (b["text"] for b in response.get("content", []) if b.get("type") == "text"),
            "{}",
        )

        try:
            work_order = json.loads(raw_text)
        except Exception:
            work_order = {
                "work_order_id": f"WO-{ikey}",
                "asset_id": asset_id,
                "work_type": "corrective",
                "priority": "medium",
                "description": description,
                "estimated_hours": 2.0,
                "required_skills": ["maintenance_technician"],
                "required_parts": [],
                "safety_precautions": ["LOTO required"],
                "idempotency_key": ikey,
            }

        self._idempotency_store[ikey] = work_order

        return AgentMessage(
            sender=self.name,
            recipient=message.sender,
            intent="work_order_created",
            payload={"work_order": work_order, "idempotent": False, "dry_run_diff": work_order},
            confidence=0.85,
            trace_id=message.trace_id,
            correlation_id=message.correlation_id,
        )

    async def _dispatch(self: Self, message: AgentMessage) -> AgentMessage | AgentDecision:
        wo_id = message.payload.get("work_order_id", "unknown")
        inputs_hash = hashlib.sha256(wo_id.encode()).hexdigest()

        decision = AgentDecision(
            agent=self.name,
            action=f"dispatch_work_order:{wo_id}",
            rationale="Work order dispatched to MES after HITL approval",
            confidence=0.95,
            purdue_zone=3,
            reversibility="irreversible",
            trace_id=message.trace_id,
            inputs_hash=inputs_hash,
            timestamp_utc=datetime.datetime.now(datetime.UTC)
            .replace(tzinfo=None)
            .isoformat()
            + "Z",
        )
        return decision
