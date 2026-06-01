"""UNS Context Broker Agent — mediates tool calls and enforces Purdue zoning."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

import structlog
from pydantic import BaseModel

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

# Sparkplug B topic: spBv1.0/<group>/<message_type>/<edge_node>[/<device>]
_SPARKPLUG_PATTERN = re.compile(
    r"^spBv1\.0/(?P<group>[^/]+)/(?P<msg_type>NBIRTH|NDEATH|DBIRTH|DDEATH|NDATA|DDATA|NCMD|DCMD|STATE)/(?P<edge_node>[^/]+)(?:/(?P<device>[^/]+))?$"
)

# ISA-95 UNS path: <enterprise>/<site>/<area>/<line>/<cell>/<asset>/<signal>
_ISA95_PATTERN = re.compile(r"^[A-Za-z0-9_-]+(/[A-Za-z0-9_-]+){2,6}$")


class UNSResolution(BaseModel):
    path: str
    resolved: bool
    purdue_zone: int
    sparkplug: bool
    group_id: str | None = None
    edge_node_id: str | None = None
    device_id: str | None = None
    message_type: str | None = None


class UNSContextBrokerAgent(BaseIndustrialAgent):
    """Validates Sparkplug B topics, resolves ISA-95 paths, enforces zone boundaries."""

    role = AgentRole.UNS_CONTEXT_BROKER
    capabilities = [
        AgentCapability(
            name="resolve_uns_path",
            description="Validate and resolve a UNS topic or ISA-95 path",
            inputs={"path": "string", "requesting_zone": "int"},
            outputs={"resolved": "bool", "purdue_zone": "int"},
            purdue_zone_required=3,
            reversibility="reversible",
        ),
        AgentCapability(
            name="validate_write_gate",
            description="Gate write operations by Purdue zone policy",
            inputs={"action": "string", "target_zone": "int", "agent_zone": "int"},
            outputs={"allowed": "bool", "reason": "string"},
            purdue_zone_required=3,
            reversibility="soft",
        ),
    ]

    def __init__(
        self,
        name: str,
        llm: LLMProvider,
        context_broker: ContextBrokerProtocol,
        governance: GovernanceProtocol,
        write_gate_zone_threshold: int = 2,
    ) -> None:
        super().__init__(name, llm, context_broker, governance)
        self._write_gate_threshold = write_gate_zone_threshold

    def resolve_path(self, path: str) -> UNSResolution:
        spk_match = _SPARKPLUG_PATTERN.match(path)
        if spk_match:
            return UNSResolution(
                path=path,
                resolved=True,
                purdue_zone=1,
                sparkplug=True,
                group_id=spk_match.group("group"),
                edge_node_id=spk_match.group("edge_node"),
                device_id=spk_match.group("device"),
                message_type=spk_match.group("msg_type"),
            )

        if _ISA95_PATTERN.match(path):
            depth = path.count("/")
            zone = max(0, 3 - depth)
            return UNSResolution(path=path, resolved=True, purdue_zone=zone, sparkplug=False)

        return UNSResolution(path=path, resolved=False, purdue_zone=5, sparkplug=False)

    def validate_zone(self, agent_zone: int, target_zone: int) -> bool:
        if target_zone <= self._write_gate_threshold:
            log.warning(
                "uns_zone_violation",
                agent_zone=agent_zone,
                target_zone=target_zone,
                threshold=self._write_gate_threshold,
            )
            return False
        return True

    async def handle(self, message: AgentMessage) -> AgentMessage | AgentDecision:
        path = message.payload.get("path", "")
        action = message.payload.get("action", "read")
        agent_zone = int(message.payload.get("agent_zone", 3))

        resolution = self.resolve_path(path)
        allowed = True
        reason = "OK"

        if action != "read":
            allowed = self.validate_zone(agent_zone, resolution.purdue_zone)
            if not allowed:
                reason = (
                    f"Zone {resolution.purdue_zone} is at or below "
                    f"write gate threshold {self._write_gate_threshold}"
                )

        log.info(
            "uns_context_broker_handle",
            path=path,
            resolved=resolution.resolved,
            allowed=allowed,
            trace_id=message.trace_id,
        )

        return AgentMessage(
            sender=self.name,
            recipient=message.sender,
            intent=message.intent,
            payload={
                "resolution": resolution.model_dump(),
                "allowed": allowed,
                "reason": reason,
            },
            confidence=1.0 if resolution.resolved else 0.5,
            trace_id=message.trace_id,
            correlation_id=message.correlation_id,
        )
