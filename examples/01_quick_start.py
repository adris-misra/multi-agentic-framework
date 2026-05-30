"""
Example 01 -- Quick Start: Routing an operator query through the framework.

Demonstrates:
- Creating an AgentMessage from a natural-language query
- RoutingPolicy resolving the intent to the correct agent role
- HITLSupervisorAgent threshold check

Run with:
    PYTHONPATH=src python examples/01_quick_start.py
"""

from __future__ import annotations

import asyncio
import uuid
from unittest.mock import AsyncMock

from industrial_agents.agents.base import AgentMessage
from industrial_agents.agents.hitl_supervisor import HITLSupervisorAgent
from industrial_agents.orchestration.routing_policy import RoutingPolicy


async def main() -> None:
    trace_id = str(uuid.uuid4())
    query = "vibration anomaly on motor_01 -- should I schedule maintenance?"

    message = AgentMessage(
        sender="operator",
        intent=query,
        trace_id=trace_id,
        confidence=0.78,
    )

    print(f"\n[trace={trace_id[:8]}] Query: {query!r}")

    policy = RoutingPolicy()
    target_role = policy.route(message)
    needs_hitl = policy.requires_hitl(message)

    print(f"  -> Routed to: {target_role.value}")
    print(f"  -> Requires HITL: {needs_hitl}")

    mock_llm = AsyncMock()
    mock_broker = AsyncMock()
    mock_gov = AsyncMock()
    mock_gov.sign_decision.return_value = "unsigned:demo"

    hitl = HITLSupervisorAgent(
        name="hitl_supervisor",
        llm=mock_llm,
        context_broker=mock_broker,
        governance=mock_gov,
        confidence_threshold=0.85,
    )

    result = await hitl.handle(message)
    print(f"  -> HITL decision: {result.intent}")
    if result.payload.get("routed"):
        print(f"  -> Notification ID: {result.payload.get('notification_id')}")
    print()


if __name__ == "__main__":
    asyncio.run(main())
