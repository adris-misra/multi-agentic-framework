"""
Example 02 -- UNS Topic Validation: Sparkplug B and ISA-95 path resolution.

Demonstrates:
- UNSContextBrokerAgent validating Sparkplug B topics
- ISA-95 path resolution and Purdue zone mapping
- Write-gate enforcement

Run with:
    PYTHONPATH=src python examples/02_uns_topic_validation.py
"""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock

from industrial_agents.agents.uns_context_broker import UNSContextBrokerAgent


async def main() -> None:
    mock_llm = AsyncMock()
    mock_broker = AsyncMock()
    mock_gov = AsyncMock()
    mock_gov.sign_decision.return_value = "unsigned:demo"

    broker = UNSContextBrokerAgent(
        name="uns_context_broker",
        llm=mock_llm,
        context_broker=mock_broker,
        governance=mock_gov,
        write_gate_zone_threshold=2,
    )

    test_paths = [
        "spBv1.0/Chicago/NDATA/line1/motor_01",
        "spBv1.0/Chicago/DDATA/line2/press_01",
        "acme/chicago/line1/cell1/motor_01/vibration_rms",
        "acme/chicago/area1/line3/cell1/hydraulic_01",
        "not-a-valid-path",
    ]

    print("\n--- UNS Path Resolution ---")
    for path in test_paths:
        r = broker.resolve_path(path)
        status = "VALID" if r.resolved else "INVALID"
        spk = " [Sparkplug B]" if r.sparkplug else " [ISA-95]" if r.resolved else ""
        print(f"  {status:7} zone={r.purdue_zone}{spk}  {path}")

    print("\n--- Zone Write Gate ---")
    write_tests = [
        (3, 3, "Same zone -- should allow"),
        (3, 2, "Agent zone 3 -> target zone 2 -- should BLOCK (<= gate threshold 2)"),
        (3, 1, "Agent zone 3 -> target zone 1 -- should BLOCK (<= gate threshold 2)"),
        (3, 0, "Agent zone 3 -> target zone 0 -- should BLOCK"),
    ]
    for agent_z, target_z, desc in write_tests:
        allowed = broker.validate_zone(agent_zone=agent_z, target_zone=target_z)
        print(f"  {'ALLOWED' if allowed else 'BLOCKED':7}  {desc}")
    print()


if __name__ == "__main__":
    asyncio.run(main())
