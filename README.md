# Industrial Agentic Intelligence Framework

> **Closing the operational knowledge gap in U.S. manufacturing with open-source, UNS-native, cybersecurity-aware multi-agent AI.**

[![CI](https://github.com/adris-misra/multi-agentic-framework/actions/workflows/ci.yml/badge.svg)](https://github.com/adris-misra/multi-agentic-framework/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue)](https://www.python.org)
[![CMMC L2 Aligned](https://img.shields.io/badge/CMMC-L2%20Aligned-green)](docs/governance/cmmc_l2_mapping.md)

---

## Why This Exists

U.S. manufacturing faces a converging crisis:

- **2.1 million unfilled positions** projected by 2030 (Deloitte / Manufacturing Institute)
- **40% of the skilled workforce** is within 10 years of retirement, taking 30+ years of institutional knowledge with them
- **Small-to-mid manufacturers (SMMs)** — the backbone of the CHIPS Act supplier ecosystem — lack the capital, OT expertise, and AI safety literacy to deploy agentic AI without risk

Off-the-shelf AI tools are not designed for the shop floor. They are:
- Not OT-aware (no Purdue zoning, no ISA-95 context)
- Not UNS-aware (cannot speak Sparkplug B or OPC UA natively)
- Not air-gap tolerant (assume cloud connectivity)
- Not CMMC-aligned (non-starter for defense-adjacent suppliers)
- Not auditable (no governance lineage, no human-in-the-loop discipline)

Gartner estimates **40%+ of agentic AI projects will be cancelled by 2027** due to unclear value and inadequate risk controls. This framework is the missing reference implementation that makes agentic AI safe to deploy in manufacturing.

---

## Architecture

![Architecture Overview](docs/architecture/overview.png)

Ten specialized agents collaborate in a UNS-mediated group chat, governed end-to-end by an immutable lineage bus:

| Agent | Role |
|-------|------|
| **Operational Intent** | Parses operator NL queries → typed `Intent` (EN/ES/VI) |
| **UNS Context Broker** | Mediates ALL tool calls; enforces Purdue zoning; resolves ISA-95 paths |
| **Telemetry & Historian** | Reads OPC UA, MQTT Sparkplug B, PI, Ignition, Snowflake, Timestream |
| **Anomaly & Root-Cause** | Multivariate AD (Matrix Profile + Isolation Forest) + FMEA traversal |
| **Tacit-Knowledge Curator** | RAG over SOPs, expert interviews, OEM manuals, work orders |
| **Safety / Guardrail** | OPA policy engine; reversibility classifier; CMMC L2 gate |
| **Work-Order & MES Dispatch** | Writes to CMMS/MES with dry-run diff + idempotency |
| **Governance & Lineage** | OpenLineage emit + Ed25519 signing + NIST AI RMF mapping |
| **HITL Supervisor** | Confidence-thresholded human routing (Slack/Teams/email) |
| **Shop-Floor Copilot UI** | Role-aware Streamlit operator surface |

---

## Quick Start

### Prerequisites

- Python 3.11+
- Docker + Docker Compose
- (Optional) Ollama for local LLM inference

```bash
git clone https://github.com/adris-misra/multi-agentic-framework.git
cd multi-agentic-framework
make install
cp .env.example .env   # fill in your API keys
make demo              # starts the full docker-compose stack
```

The demo stack starts:
- **MQTT broker** at `mqtt://localhost:1883` (Eclipse Mosquitto)
- **ChromaDB** at `http://localhost:8000`
- **Jaeger tracing UI** at `http://localhost:16686`
- **Operator Copilot** at `http://localhost:8501`

### SMM Laptop-Only Mode (no cloud required)

```bash
# Install Ollama: https://ollama.com
ollama pull llama3.1:8b
LLM_PROVIDER=ollama make demo
# Then open examples/05_smm_starter_kit.ipynb
```

---

## Standards Alignment

| Standard | How this framework addresses it |
|----------|--------------------------------|
| **ISA-95 / IEC 62264** | UNS topic taxonomy, ISA-95 hierarchy in every `AgentMessage` |
| **MQTT Sparkplug B v3** | Native decode/encode; UNS Context Broker validates all paths |
| **OPC UA (IEC 62541)** | Async read-only client with zone-enforcement wrapper |
| **NIST SP 800-82 Rev 3** | Purdue zoning, network segmentation policy, declarative control mapping |
| **CMMC L2 / NIST SP 800-171** | Policy engine gates every write; audit log with Ed25519 signatures |
| **NIST AI RMF** | Every decision mapped to Govern/Map/Measure/Manage; exportable |
| **ISO 42001** | Governance lineage + human oversight + risk classification |
| **ISO 14224** | Asset taxonomy used for metadata decoration |

---

## Repository Layout

```
├── src/industrial_agents/   # Python package
│   ├── agents/              # 10 industrial agents
│   ├── tools/               # Protocol adapters (OPC UA, MQTT, PI, Snowflake, …)
│   ├── orchestration/       # AutoGen group-chat + routing
│   ├── governance/          # Lineage, signing, OPA, PII redaction
│   ├── security/            # Purdue zoning, mTLS, secrets vault
│   ├── observability/       # OpenTelemetry, Prometheus
│   └── ui/                  # Streamlit operator copilot
├── config/                  # ISA-95, UNS taxonomy, Purdue zones, CMMC, LLM config
├── docker/                  # docker-compose + Dockerfiles
├── policies/                # OPA rego policies
├── data/synthetic/          # Reproducible synthetic UNS dataset
├── examples/                # Five canonical Jupyter notebooks
├── benchmarks/              # Industrial Agent Benchmark (IABENCH-v1)
├── docs/                    # MkDocs site source
└── legacy/                  # Archived original SDLC demo
```

---

## Benchmarks (IABENCH-v1)

| Task | Metric | Claude Sonnet | GPT-4o | Llama 3.1 8B |
|------|--------|--------------|--------|--------------|
| Root-cause attribution | P/R F1 | TBD | TBD | TBD |
| Tacit-knowledge retrieval | nDCG@5 | TBD | TBD | TBD |
| Safety guardrail compliance | Block-rate | TBD | TBD | TBD |
| Hallucination rate | % | TBD | TBD | TBD |

*Results populated in Phase 7.*

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). This project follows the [Contributor Covenant v2.1](CODE_OF_CONDUCT.md).

## Citation

If you use this framework in research, please cite:

```bibtex
@software{misra2026industrialagents,
  author    = {Misra, Adris},
  title     = {Industrial Agentic Intelligence Framework},
  year      = {2026},
  url       = {https://github.com/adris-misra/multi-agentic-framework},
  version   = {0.1.0}
}
```

## License

[MIT](LICENSE) © 2026 Adris Misra
