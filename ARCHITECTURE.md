# Architecture

> **Industrial Agentic Intelligence Framework** — UNS-native, cybersecurity-aware multi-agent AI for U.S. manufacturing.

## Table of Contents

1. [System Overview](#system-overview)
2. [Agent Topology](#agent-topology)
3. [UNS Context Broker (Keystone)](#uns-context-broker)
4. [Orchestration Layer](#orchestration-layer)
5. [Governance Bus](#governance-bus)
6. [Security Model](#security-model)
7. [Observability](#observability)
8. [Deployment Topologies](#deployment-topologies)
9. [Standards Alignment Matrix](#standards-alignment-matrix)

---

## System Overview

The framework implements a **10-agent group chat** mediated by the UNS Context Broker,
with governance and lineage tracked end-to-end on an immutable lineage bus.

```
Operator Query (EN/ES/VI)
        │
        ▼
┌─────────────────┐
│ Operational     │  Parses NL → typed Intent
│ Intent Agent    │  (language detection + entity extraction)
└────────┬────────┘
         │ AgentMessage
         ▼
┌─────────────────────────────────────────────────┐
│              IndustrialGroupChat                │
│   (RoutingPolicy → target agent selection)      │
│                                                 │
│  ┌────────────┐   ┌──────────────┐              │
│  │ UNS Context│   │  Telemetry & │              │
│  │ Broker     │◄──│  Historian   │              │
│  │ (zone gate)│   └──────────────┘              │
│  └────────────┘   ┌──────────────┐              │
│        │          │ Anomaly &    │              │
│        │     ┌────│ Root-Cause   │              │
│        │     │    └──────────────┘              │
│  ┌─────▼─────┴┐   ┌──────────────┐              │
│  │ Safety /   │   │ Tacit        │              │
│  │ Guardrail  │   │ Knowledge    │              │
│  └────────────┘   └──────────────┘              │
│  ┌────────────┐   ┌──────────────┐              │
│  │ Work-Order │   │ Governance & │              │
│  │ & MES      │   │ Lineage      │              │
│  └────────────┘   └──────────────┘              │
│  ┌────────────┐   ┌──────────────┐              │
│  │ HITL       │   │ Shop-Floor   │              │
│  │ Supervisor │   │ Copilot UI   │              │
│  └────────────┘   └──────────────┘              │
└─────────────────────────────────────────────────┘
         │
         ▼
  AgentDecision (Ed25519-signed OpenLineage event)
```

---

## Agent Topology

| # | Agent | Class | Role | Zone |
|---|-------|-------|------|------|
| 1 | Operational Intent | `OperationalIntentAgent` | NL → typed Intent; EN/ES/VI support | 4 |
| 2 | UNS Context Broker | `UNSContextBrokerAgent` | Mediates ALL tool calls; Purdue zone enforcement | 3 |
| 3 | Telemetry & Historian | `TelemetryHistorianAgent` | OPC UA / Sparkplug B / historian reads | 2 |
| 4 | Anomaly & Root-Cause | `AnomalyRootCauseAgent` | Matrix Profile + Isolation Forest + FMEA | 3 |
| 5 | Tacit-Knowledge Curator | `TacitKnowledgeCuratorAgent` | RAG over SOPs, manuals, expert interviews | 4 |
| 6 | Safety / Guardrail | `SafetyGuardrailAgent` | OPA policy gate; reversibility classifier; CMMC L2 | 4 |
| 7 | Work-Order & MES | `WorkOrderMESAgent` | CMMS write with dry-run diff + idempotency | 3 |
| 8 | Governance & Lineage | `GovernanceLineageAgent` | OpenLineage + Ed25519 signing + NIST AI RMF | 4 |
| 9 | HITL Supervisor | `HITLSupervisorAgent` | Confidence-threshold routing to human (Slack/Teams/email) | 4 |
| 10 | Shop-Floor Copilot | `ShopFloorCopilotAgent` | Role-aware Streamlit operator surface | 4 |

### Agent Data Flow

Every inter-agent message is an `AgentMessage` Pydantic model carrying:
- `trace_id` — UUID linking all messages in a single operator request
- `confidence` — float 0–1, gates HITL escalation
- `payload` — typed dict, PII-scrubbed before logging
- `intent` — string, fed to `RoutingPolicy` for next-hop selection

Every write decision is an `AgentDecision` that:
1. Gets Ed25519-signed by `GovernanceLineageAgent`
2. Is emitted as an OpenLineage `COMPLETE` event with industrial governance facets
3. Is stored in the immutable audit log

---

## UNS Context Broker

The UNS Context Broker is the **keystone agent**. No agent may access OT data without
going through it.

### Sparkplug B Validation

Topics must match: `spBv1.0/<group_id>/<msg_type>/<edge_node>[/<device>]`

Supported message types: `NBIRTH`, `NDEATH`, `DBIRTH`, `DDEATH`, `NDATA`, `DDATA`, `NCMD`, `DCMD`, `STATE`

### ISA-95 Path Resolution

Paths follow: `<enterprise>/<site>/<area>/<line>/<cell>/<asset>/<signal>`

Depth determines Purdue zone: deeper paths → lower zone numbers.

### Write Gate

`write_gate_zone_threshold = 2` (configurable in `config/purdue_zones.yaml`).
Any write targeting a zone ≤ 2 is blocked without explicit HITL approval.

---

## Orchestration Layer

`IndustrialGroupChat` wraps AutoGen's `GroupChat` with:

1. **RoutingPolicy** — regex-based intent → AgentRole dispatch (priority-ordered rules)
2. **EscalationRouter** — blocks execution on critical/emergency events or low-confidence irreversible decisions
3. **Max rounds** — configurable (default 10) to prevent infinite loops
4. **HITL circuit-breaker** — halts on irreversible AgentDecision until human confirms

---

## Governance Bus

The `LineageBus` implements `GovernanceProtocol` and wires `GovernanceLineageAgent`:

```
AgentDecision
    │
    ├─► sign_decision()     → Ed25519 signature (or "unsigned:" placeholder if no key)
    ├─► emit_lineage()      → OpenLineage COMPLETE event with industrial governance facets
    │       ├─► purdue_zone
    │       ├─► reversibility
    │       ├─► confidence
    │       ├─► nist_ai_rmf_function  (GOVERN/MAP/MEASURE/MANAGE)
    │       └─► cmmc_l2_applicable
    └─► _audit_log          → in-memory append-only list (exported via governance-export CLI)
```

NIST AI RMF function mapping:

| Action | Function |
|--------|---------|
| read, read_telemetry | MEASURE |
| detect_anomaly, diagnose | MEASURE |
| evaluate_action | MANAGE |
| block | GOVERN |
| create_work_order | MANAGE |
| emit_lineage, sign | GOVERN |
| rag_query | MAP |

---

## Security Model

### Purdue Zone Matrix

| From Zone | Read Allowed To | Write Allowed To |
|-----------|----------------|-----------------|
| Zone 4 (Site Business) | 3, 4, 5 | 4, 5 |
| Zone 3 (Mfg Ops) | 2, 3, 4, 5 | 3, 4 |
| Zone 2 (Supervisory) | 1, 2, 3, 4 | 2, 3 |
| Zone 1 (Control) | 0, 1, 2 | 1, 2 |

Write gate threshold = 2: any write to zone 0 or 1 requires HITL approval.

### OPA Policy Engine

Rego policies in `policies/`:
- `industrial_safety.rego` — default-deny writes, zone gate, confidence check
- `cmmc_l2.rego` — NIST SP 800-171 practice family gates

### Secrets Management

`SecretsVault` priority chain: env var → `.secrets/<key>` file → HashiCorp Vault

---

## Observability

| Layer | Implementation |
|-------|---------------|
| Distributed tracing | OpenTelemetry SDK → OTLP → Jaeger |
| Metrics | Prometheus counters/histograms (lazy init) |
| Structured logging | structlog with contextvars (trace_id propagation) |
| Governance lineage | OpenLineage + Ed25519 signatures |

---

## Deployment Topologies

### SMM Laptop Mode (no cloud)
```
Operator browser → Streamlit (port 8501)
                → Ollama (llama3.1:8b, local)
                → Mosquitto MQTT (port 1883)
                → ChromaDB (port 8000)
```

### Full Docker Compose Stack
```
docker-compose up  →  mqtt + chroma + jaeger + prometheus + uns-simulator + app
```

### Air-Gapped OT Network
- All LLM inference via Ollama (no cloud)
- OPA runs as a sidecar (no external calls)
- ChromaDB on local storage
- OTEL traces buffered locally, exported on reconnect

---

## Standards Alignment Matrix

| Standard | Component |
|----------|-----------|
| ISA-95 / IEC 62264 | UNS topic taxonomy, ISA-95 hierarchy in every `AgentMessage` |
| MQTT Sparkplug B v3 | `SparkplugClient`, `UNSContextBrokerAgent` topic validation |
| OPC UA (IEC 62541) | `OPCUAClient` (read-only, zone-2 enforcement) |
| NIST SP 800-82 Rev 3 | `PurdueZoneEnforcer`, `OPAClient`, zone matrix |
| CMMC L2 / NIST SP 800-171 | `policies/cmmc_l2.rego`, `SafetyGuardrailAgent` |
| NIST AI RMF | `GovernanceLineageAgent` NIST function mapping in every lineage event |
| ISO 42001 | Governance lineage + human oversight + risk classification |
| ISO 14224 | Asset taxonomy in synthetic data, FMEA references |

---

## Design Notes

### Why AutoGen?

AutoGen's `GroupChat` provides a production-tested multi-agent turn manager with
configurable speaker selection and message routing. The `IndustrialGroupChat` wrapper
adds UNS-mediated routing and Purdue zone enforcement on top without re-implementing
the conversation management primitives.

### Why Pydantic v2?

All inter-agent messages are Pydantic v2 models. This gives us:
- Runtime validation of confidence bounds, zone ranges, reversibility enums
- `model_dump()` for OpenLineage serialization
- JSON schema export for the IABENCH evaluation harness

### Fallback on LLM Parse Error

All agents implement a structured `try/except` around LLM JSON parsing.
On parse failure, they return a conservative default (anomaly_detected=False,
confidence=0.0, allowed=False for safety decisions) and log a warning.
This prevents a single malformed LLM response from crashing the pipeline.
