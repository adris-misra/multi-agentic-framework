"""
Example 04 — Governance Lineage: Ed25519 signing and OpenLineage emission.

Demonstrates:
- GovernanceLineageAgent emitting signed OpenLineage events
- Audit log export to JSON
- NIST AI RMF function mapping in facets

Run with:
    PYTHONPATH=src python examples/04_governance_lineage.py
"""

from __future__ import annotations

import asyncio
import datetime
import json
import uuid
from unittest.mock import AsyncMock

from industrial_agents.agents.base import AgentDecision, AgentMessage
from industrial_agents.agents.governance_lineage import GovernanceLineageAgent
from industrial_agents.governance.lineage_bus import LineageBus


async def main() -> None:
    mock_llm = AsyncMock()
    mock_broker = AsyncMock()
    mock_gov = AsyncMock()
    mock_gov.sign_decision.return_value = "unsigned:demo"

    gov_agent = GovernanceLineageAgent(
        name="governance_lineage",
        llm=mock_llm,
        context_broker=mock_broker,
        governance=mock_gov,
        signing_key_path=None,  # unsigned mode for demo
    )

    lineage = LineageBus(governance_agent=gov_agent)

    print("\n[1] Emitting governance decisions...")

    decisions = [
        AgentDecision(
            agent="anomaly_root_cause",
            action="anomaly_alert:bearing_wear",
            rationale="Progressive bearing degradation detected",
            confidence=0.93,
            purdue_zone=3,
            reversibility="reversible",
            trace_id=str(uuid.uuid4()),
            inputs_hash="a" * 64,
            timestamp_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        ),
        AgentDecision(
            agent="safety_guardrail",
            action="allow",
            rationale="Action approved: read-only telemetry query",
            confidence=0.99,
            purdue_zone=4,
            reversibility="reversible",
            trace_id=str(uuid.uuid4()),
            inputs_hash="b" * 64,
            timestamp_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        ),
        AgentDecision(
            agent="work_order_mes",
            action="create_work_order:WO-bearing-001",
            rationale="Bearing replacement work order created per SOP-MAINT-001",
            confidence=0.87,
            purdue_zone=3,
            reversibility="soft",
            trace_id=str(uuid.uuid4()),
            inputs_hash="c" * 64,
            timestamp_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        ),
    ]

    for decision in decisions:
        sig = await lineage.sign_decision(decision)
        decision.signature = sig
        await lineage.emit_lineage(decision)
        print(f"   {decision.agent:30} action={decision.action[:30]:30} sig={sig[:20]}...")

    # 2. Export audit log
    print("\n[2] Exporting audit log...")
    trace_id = str(uuid.uuid4())
    export_msg = AgentMessage(
        sender="cli",
        intent="export governance",
        trace_id=trace_id,
        payload={"action": "export", "since": "2020-01-01T00:00:00Z", "format": "json"},
    )
    result = await gov_agent.handle(export_msg)
    log_data = json.loads(result.payload["export"])

    print(f"   Exported {result.payload['count']} events")
    if log_data:
        facets = log_data[0].get("facets", {}).get("industrialGovernance", {})
        print(f"   First event NIST AI RMF function: {facets.get('nist_ai_rmf_function')}")
        print(f"   First event Purdue zone: {facets.get('purdue_zone')}")
        print(f"   CMMC L2 applicable: {facets.get('cmmc_l2_applicable')}")
    print()


if __name__ == "__main__":
    asyncio.run(main())
