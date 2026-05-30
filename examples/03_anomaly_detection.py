"""
Example 03 — Anomaly Detection: Generating and detecting a bearing-wear anomaly.

Demonstrates:
- UNSDataGenerator producing synthetic motor vibration data
- AnomalyRootCauseAgent analyzing the anomaly with mocked LLM
- GovernanceLineageAgent signing the decision

Run with:
    PYTHONPATH=src python examples/03_anomaly_detection.py
"""

from __future__ import annotations

import asyncio
import json
import uuid
from unittest.mock import AsyncMock

from industrial_agents.agents.anomaly_root_cause import AnomalyRootCauseAgent
from industrial_agents.agents.base import AgentMessage
from industrial_agents.governance.lineage_bus import LineageBus
from industrial_agents.synthetic.uns_generator import UNSDataGenerator


async def main() -> None:
    # 1. Generate 6h of synthetic data with bearing-wear anomaly at hour 4
    print("\n[1] Generating synthetic telemetry (6h, motor_01 bearing wear at ~hour 4)...")
    gen = UNSDataGenerator(seed=42)
    data = gen.generate(n_hours=6, inject_anomalies=True)
    motor_rows = [
        r for r in data["rows"]
        if r["asset_id"] == "motor_01" and r["signal"] == "vibration_rms"
    ]
    max_vib = max(r["value"] for r in motor_rows)
    mean_vib = sum(r["value"] for r in motor_rows) / len(motor_rows)
    print(f"   motor_01 vibration: mean={mean_vib:.2f} mm/s, peak={max_vib:.2f} mm/s")

    # 2. Set up the anomaly agent with a mocked LLM response
    analysis_response = {
        "anomaly_detected": True,
        "anomaly_type": "bearing_wear",
        "confidence": 0.93,
        "root_cause": "Progressive bearing degradation — vibration RMS exceeded 3σ for 45 minutes",
        "fmea_reference": "FM-MOT-001",
        "recommended_action": "Schedule bearing replacement per SOP-MAINT-001 within 48 hours",
        "severity": "high",
        "affected_assets": ["motor_01"],
    }

    mock_llm = AsyncMock()
    mock_llm.complete.return_value = {
        "content": [{"type": "text", "text": json.dumps(analysis_response)}],
        "model": "demo",
        "stop_reason": "end_turn",
        "usage": {},
    }

    governance = LineageBus()
    mock_broker = AsyncMock()

    agent = AnomalyRootCauseAgent(
        name="anomaly_root_cause",
        llm=mock_llm,
        context_broker=mock_broker,
        governance=governance,
    )

    # 3. Send a message representing the anomalous reading
    trace_id = str(uuid.uuid4())
    msg = AgentMessage(
        sender="telemetry_historian",
        intent="vibration anomaly on motor_01",
        trace_id=trace_id,
        payload={
            "asset_id": "motor_01",
            "series": motor_rows[-60:],  # last 60 readings
        },
    )

    print("\n[2] Running AnomalyRootCauseAgent...")
    result = await agent.handle(msg)

    print(f"   Anomaly detected: {result.payload.get('anomaly_detected')}")
    print(f"   Type:             {result.payload.get('anomaly_type')}")
    print(f"   Root cause:       {result.payload.get('root_cause')}")
    print(f"   Recommendation:   {result.payload.get('recommended_action')}")
    print(f"   Severity:         {result.payload.get('severity')}")
    print(f"   Confidence:       {result.confidence:.2f}")
    print(f"   Governance log:   {len(governance.get_audit_log())} event(s)")
    print()


if __name__ == "__main__":
    asyncio.run(main())
