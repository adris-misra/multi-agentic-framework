# Industrial Agentic Intelligence Framework

> **Closing the operational knowledge gap in U.S. manufacturing with open-source,
> UNS-native, cybersecurity-aware multi-agent AI.**

## Why This Exists

U.S. manufacturing faces a converging crisis:

- **2.1 million unfilled positions** projected by 2030 (Deloitte / Manufacturing Institute)
- **40% of the skilled workforce** is within 10 years of retirement, taking decades of
  institutional knowledge with them
- **Small-to-mid manufacturers (SMMs)** — the backbone of the CHIPS Act supplier ecosystem —
  lack the capital and OT/AI expertise to deploy agentic AI safely

Off-the-shelf AI tools are not designed for the shop floor: they are not OT-aware,
not UNS-aware, not air-gap-tolerant, and not CMMC-aligned.

This framework is the missing reference implementation.

## Quick Start

```bash
git clone https://github.com/adris-misra/multi-agentic-framework.git
cd multi-agentic-framework
make install
cp .env.example .env   # fill in your API keys
make demo              # starts MQTT + ChromaDB + Jaeger + Operator Copilot
```

## Ten Industrial Agents

| Agent | Responsibility |
|-------|---------------|
| Operational Intent | NL → typed `Intent` (EN/ES/VI) |
| UNS Context Broker | Mediates ALL tool calls; enforces Purdue zoning |
| Telemetry & Historian | OPC UA, Sparkplug B, PI, Ignition, Snowflake, Timestream |
| Anomaly & Root-Cause | Matrix Profile + Isolation Forest + FMEA traversal |
| Tacit-Knowledge Curator | RAG over SOPs, expert interviews, work orders |
| Safety / Guardrail | OPA policy engine + reversibility classifier |
| Work-Order & MES Dispatch | CMMS/MES writes with dry-run + idempotency |
| Governance & Lineage | OpenLineage + Ed25519 signing + NIST AI RMF mapping |
| HITL Supervisor | Confidence-thresholded human-in-the-loop routing |
| Shop-Floor Copilot UI | Role-aware Streamlit operator surface |

## Standards Alignment

ISA-95 · MQTT Sparkplug B v3 · OPC UA · NIST SP 800-82 Rev 3 ·
CMMC L2 · NIST AI RMF · ISO 42001 · ISO 14224 · ISO 15926

See the full [Standards Alignment Matrix](standards/standards_alignment.md).
