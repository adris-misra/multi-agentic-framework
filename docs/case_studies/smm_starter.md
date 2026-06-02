# SMM Starter Kit

**Scenario:** A 45-person precision machining shop in Ohio running Haas CNC machines
and a legacy CMMS. No dedicated OT security staff. No cloud budget. Needs CMMC Level 2
compliance to keep a Tier-2 automotive contract.

## Prerequisites

- Laptop or edge server (8 GB RAM minimum)
- [Ollama](https://ollama.ai) installed locally
- Python 3.11+

## Quick Start (5 minutes, no API keys)

```bash
# 1. Clone and install
git clone https://github.com/adris-misra/multi-agentic-framework.git
cd multi-agentic-framework
pip install -e ".[dev]"

# 2. Pull a local LLM
ollama pull llama3.1:8b

# 3. Run the SMM demo
PYTHONPATH=src LLM_PROVIDER=ollama python examples/05_smm_starter_kit.py
```

## What Happens

The demo simulates a shop-floor operator querying the system:

> "Motor 01 is making a loud noise and vibrating a lot. What should I do?"

The framework:

1. **Routes** the query to the Anomaly & Root-Cause agent
2. **Detects** a likely bearing-wear pattern from vibration telemetry
3. **Guards** against unsafe actions (no write to zone 0/1 without HITL)
4. **Generates** a work order with LOTO safety precautions
5. **Signs** the decision with Ed25519 and emits an OpenLineage event
6. **Returns** a plain-English summary appropriate for the operator's role

## CMMC L2 Checklist

| Practice | How This Demo Addresses It |
|----------|---------------------------|
| AC.L2-3.1.1 | `SecretsVault` controls access; no credentials in code |
| AU.L2-3.3.1 | Every decision is signed and logged to the lineage bus |
| IR.L2-3.6.1 | `HITLSupervisorAgent` escalates anomalies above threshold |
| SI.L2-3.14.1 | `SafetyGuardrailAgent` blocks unsafe actions before execution |

## Next Steps

- Add your OPC UA endpoint: set `OPCUA_ENDPOINT=opc.tcp://your-plc:4840` in `.env`
- Connect a real MQTT broker: set `MQTT_BROKER=192.168.1.10` in `.env`
- Run the benchmark suite: `industrial-agents bench --suite all --provider ollama`
