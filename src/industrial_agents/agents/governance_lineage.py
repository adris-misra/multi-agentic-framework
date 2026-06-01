"""Governance & Lineage Agent — OpenLineage emit, Ed25519 signing, NIST AI RMF mapping."""

from __future__ import annotations

import base64
import datetime
import json
from typing import TYPE_CHECKING, Any, Protocol, Self

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
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

    from industrial_agents.agents._llm import LLMProvider

log = structlog.get_logger(__name__)


class _OpenLineageProtocol(Protocol):
    async def emit(self: Self, event: dict[str, Any]) -> None: ...


# NIST AI RMF function mappings for agent actions
_NIST_FUNCTION_MAP: dict[str, str] = {
    "read": "MEASURE",
    "read_telemetry": "MEASURE",
    "detect_anomaly": "MEASURE",
    "diagnose": "MEASURE",
    "evaluate_action": "MANAGE",
    "block": "GOVERN",
    "allow": "MANAGE",
    "create_work_order": "MANAGE",
    "dispatch_work_order": "MANAGE",
    "rag_query": "MAP",
    "sign": "GOVERN",
    "emit_lineage": "GOVERN",
}


class GovernanceLineageAgent(BaseIndustrialAgent):
    role = AgentRole.GOVERNANCE_LINEAGE
    capabilities = [
        AgentCapability(
            name="emit_lineage",
            description="Emit OpenLineage event for a decision",
            inputs={"decision": "AgentDecision"},
            outputs={"lineage_event_id": "string"},
            purdue_zone_required=4,
            reversibility="reversible",
        ),
        AgentCapability(
            name="sign_decision",
            description="Ed25519-sign an AgentDecision",
            inputs={"decision": "AgentDecision"},
            outputs={"signature": "string"},
            purdue_zone_required=4,
            reversibility="reversible",
        ),
        AgentCapability(
            name="export_audit_log",
            description="Export signed governance decisions since a timestamp",
            inputs={"since": "ISO 8601", "format": "json|csv"},
            outputs={"export": "string"},
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
        signing_key_path: str | None = None,
        openlineage_client: _OpenLineageProtocol | None = None,
    ) -> None:
        super().__init__(name, llm, context_broker, governance)
        self._signing_key_path = signing_key_path
        self._ol_client = openlineage_client
        self._private_key: Ed25519PrivateKey | None = None
        self._audit_log: list[dict[str, Any]] = []

    def _load_key(self: Self) -> Ed25519PrivateKey | None:
        if self._private_key is not None:
            return self._private_key
        if self._signing_key_path is None:
            return None
        try:
            from cryptography.hazmat.primitives.serialization import load_pem_private_key

            with open(self._signing_key_path, "rb") as fh:
                self._private_key = load_pem_private_key(fh.read(), password=None)  # type: ignore[assignment]
            return self._private_key
        except Exception as exc:
            log.warning("signing_key_load_failed", error=str(exc))
            return None

    def sign_decision(self: Self, decision: AgentDecision) -> str:
        key = self._load_key()
        if key is None:
            # No key configured — return a deterministic placeholder
            import hashlib

            return "unsigned:" + hashlib.sha256(decision.inputs_hash.encode()).hexdigest()[:16]

        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

        if not isinstance(key, Ed25519PrivateKey):
            log.warning("signing_key_wrong_type")
            return "unsigned:wrong-key-type"

        payload = json.dumps(
            {
                "agent": decision.agent,
                "action": decision.action,
                "inputs_hash": decision.inputs_hash,
                "timestamp_utc": decision.timestamp_utc,
            },
            sort_keys=True,
        ).encode()

        raw_sig = key.sign(payload)
        return base64.b64encode(raw_sig).decode()

    def _to_openlineage(self: Self, decision: AgentDecision) -> dict[str, Any]:
        nist_function = _NIST_FUNCTION_MAP.get(decision.action.split(":")[0], "MAP")
        return {
            "eventType": "COMPLETE",
            "eventTime": decision.timestamp_utc,
            "run": {"runId": decision.trace_id},
            "job": {
                "namespace": "industrial-agents",
                "name": f"{decision.agent}.{decision.action}",
            },
            "inputs": [{"namespace": "industrial-agents", "name": decision.inputs_hash}],
            "outputs": [],
            "producer": "industrial-agents/governance-lineage",
            "schemaURL": "https://openlineage.io/spec/1-0-5/OpenLineage.json",
            "facets": {
                "industrialGovernance": {
                    "_producer": "industrial-agents",
                    "_schemaURL": "https://industrial-agents.io/facets/governance/v1",
                    "purdue_zone": decision.purdue_zone,
                    "reversibility": decision.reversibility,
                    "confidence": decision.confidence,
                    "signature": decision.signature,
                    "nist_ai_rmf_function": nist_function,
                    "cmmc_l2_applicable": decision.purdue_zone <= 3,
                }
            },
        }

    async def emit_lineage(self: Self, decision: AgentDecision) -> None:
        event = self._to_openlineage(decision)
        self._audit_log.append(event)

        if self._ol_client is not None:
            try:
                await self._ol_client.emit(event)
            except Exception as exc:
                log.error("openlineage_emit_failed", error=str(exc))

        log.info(
            "lineage_emitted",
            agent=decision.agent,
            action=decision.action,
            trace_id=decision.trace_id,
        )

    async def handle(self: Self, message: AgentMessage) -> AgentMessage | AgentDecision:
        action = message.payload.get("action", "export")
        log.info("governance_handle", action=action, trace_id=message.trace_id)

        if action == "export":
            since_str = message.payload.get("since", "")
            fmt = message.payload.get("format", "json")
            filtered = self._audit_log
            if since_str:
                try:
                    since_dt = datetime.datetime.fromisoformat(since_str.rstrip("Z"))
                    filtered = [
                        e
                        for e in self._audit_log
                        if datetime.datetime.fromisoformat(e.get("eventTime", "").rstrip("Z"))
                        >= since_dt
                    ]
                except Exception as exc:
                    log.debug("lineage_filter_parse_error", since=since_str, error=str(exc))

            if fmt == "csv":
                import csv
                import io

                buf = io.StringIO()
                if filtered:
                    writer = csv.DictWriter(buf, fieldnames=filtered[0].keys())
                    writer.writeheader()
                    writer.writerows(filtered)
                export_data = buf.getvalue()
            else:
                export_data = json.dumps(filtered, indent=2)

            return AgentMessage(
                sender=self.name,
                recipient=message.sender,
                intent="governance_export",
                payload={"export": export_data, "count": len(filtered)},
                confidence=1.0,
                trace_id=message.trace_id,
                correlation_id=message.correlation_id,
            )

        return AgentMessage(
            sender=self.name,
            recipient=message.sender,
            intent="governance_ack",
            payload={"status": "ok"},
            confidence=1.0,
            trace_id=message.trace_id,
            correlation_id=message.correlation_id,
        )
