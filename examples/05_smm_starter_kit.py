"""
Example 05 — SMM Starter Kit: Full local pipeline (no cloud required).

Shows a small-to-mid manufacturer running the full framework on a laptop
with Ollama (local LLM), no API keys required.

Demonstrates:
- Full routing from operator query through 3-agent pipeline
- Local LLM provider (Ollama llama3.1:8b)
- Governance lineage emission
- Shop-floor copilot role-aware response

Run with:
    ollama pull llama3.1:8b
    PYTHONPATH=src LLM_PROVIDER=ollama python examples/05_smm_starter_kit.py

Or with mocked LLM for testing:
    PYTHONPATH=src python examples/05_smm_starter_kit.py --mock
"""

from __future__ import annotations

import asyncio
import json
import sys
import uuid
from unittest.mock import AsyncMock

from industrial_agents.agents._llm import get_llm_provider
from industrial_agents.agents.base import AgentMessage
from industrial_agents.agents.shop_floor_copilot import ShopFloorCopilotAgent
from industrial_agents.governance.lineage_bus import LineageBus
from industrial_agents.orchestration.routing_policy import RoutingPolicy

_MOCK_MODE = "--mock" in sys.argv or "pytest" in sys.modules


def _make_mock_llm(role_hint: str = "operator") -> AsyncMock:
    llm = AsyncMock()

    responses = {
        "copilot": {
            "summary": "Motor 01 has a bearing wear issue. Vibration is 3x normal levels.",
            "action_items": [
                "1. Do NOT restart motor until bearing is inspected.",
                "2. Call maintenance (ext. 4521) to raise a work order.",
                "3. Switch production to motor_02 if available.",
            ],
            "urgency": "action_required",
            "safe_to_proceed": False,
            "next_step": "Contact maintenance and raise a work order for SOP-MAINT-001.",
        }
    }

    llm.complete.return_value = {
        "content": [{"type": "text", "text": json.dumps(responses["copilot"])}],
        "model": "mock",
        "stop_reason": "end_turn",
        "usage": {},
    }
    return llm


async def main() -> None:
    print("\n=== Industrial Agentic Intelligence Framework — SMM Starter Kit ===")
    print(f"    Mode: {'MOCK (demo)' if _MOCK_MODE else 'LIVE (Ollama)'}")

    query = "Motor 01 is making a loud noise and vibrating a lot. What should I do?"
    operator_role = "operator"
    trace_id = str(uuid.uuid4())

    print(f"\n[Operator query] {query!r}")
    print(f"[Operator role]  {operator_role}")
    print(f"[Trace ID]       {trace_id[:8]}...")

    # 1. Route the query
    message = AgentMessage(
        sender="operator",
        intent=query,
        trace_id=trace_id,
        confidence=0.85,
    )
    policy = RoutingPolicy()
    target = policy.route(message)
    print(f"\n[1] Routing → {target.value}")

    # 2. Set up LLM provider
    if _MOCK_MODE:
        llm = _make_mock_llm()
    else:
        llm = get_llm_provider("ollama")

    governance = LineageBus()
    mock_broker = AsyncMock()

    # 3. Shop-floor copilot composes role-aware response
    copilot = ShopFloorCopilotAgent(
        name="shop_floor_copilot",
        llm=llm,
        context_broker=mock_broker,
        governance=governance,
    )

    copilot_msg = AgentMessage(
        sender="system",
        intent=query,
        trace_id=trace_id,
        payload={
            "role": operator_role,
            "context": {
                "anomaly": "bearing_wear",
                "asset": "motor_01",
                "vibration_rms": 4.2,
                "threshold": 2.5,
            },
        },
    )

    print(f"[2] Running ShopFloorCopilotAgent (role={operator_role})...")
    result = await copilot.handle(copilot_msg)
    response = result.payload.get("response", {})

    print(f"\n{'='*60}")
    print(f"URGENCY:  {response.get('urgency', 'unknown').upper()}")
    print(f"SUMMARY:  {response.get('summary', '')}")
    print()
    if response.get("action_items"):
        print("ACTION ITEMS:")
        for item in response["action_items"]:
            print(f"  {item}")
    print(f"\nNEXT STEP: {response.get('next_step', '')}")
    print(f"{'='*60}")
    print(f"\n[Safe to proceed: {response.get('safe_to_proceed', '?')}]")
    print()


if __name__ == "__main__":
    asyncio.run(main())
