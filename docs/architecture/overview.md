# Architecture Overview

The Industrial Agentic Intelligence Framework is a ten-agent pipeline built on top of a
Unified Namespace (UNS) message fabric. All inter-agent communication flows through the
**UNS Context Broker**, which enforces Purdue zone boundaries before any tool call is
permitted to cross OT/IT network segments.

## High-Level Diagram

```
Operator Query
      │
      ▼
Operational Intent Agent  ──►  UNS Context Broker
      │                               │
      ▼                               ▼
 Routing Policy                Purdue Zone Enforcer
      │                               │
      ▼                               ▼
┌─────────────────────────────────────────────┐
│               10-Agent Group Chat            │
│                                              │
│  Telemetry & Historian                       │
│  Anomaly & Root-Cause                        │
│  Tacit-Knowledge Curator                     │
│  Safety / Guardrail  ◄── OPA Policy Engine  │
│  Work-Order & MES                            │
│  Governance & Lineage ◄── Ed25519 Signing   │
│  HITL Supervisor                             │
│  Shop-Floor Copilot UI                       │
└─────────────────────────────────────────────┘
```

## Key Design Principles

**UNS-native** — Every sensor tag, work order, and agent decision is addressed via an
ISA-95-compliant topic hierarchy (`enterprise/site/area/line/cell/asset/signal`).

**Purdue-aware** — Write operations targeting zones 0–2 (field devices, control systems,
supervisory) are blocked by the UNS Context Broker unless HITL approval has been granted
and the OPA policy engine returns `allow: true`.

**Cybersecurity-first** — CMMC Level 2 compliance is baked into the routing policy,
the guardrail agent, and the governance lineage bus. Every agent decision is Ed25519-signed
and emitted as an OpenLineage event before the action takes effect.

**Local-first** — The framework runs on a single laptop with Ollama (no cloud API keys)
via `industrial-agents bench --provider ollama`. Cloud providers (Anthropic, OpenAI,
Bedrock) are drop-in replacements via the `LLMProvider` Protocol.

## Agent Roles

| Agent | Purdue Zone | Reversibility |
|-------|------------|---------------|
| Operational Intent | 4–5 | reversible |
| UNS Context Broker | 3–5 | reversible |
| Telemetry & Historian | 2–3 | reversible |
| Anomaly & Root-Cause | 3 | reversible |
| Tacit-Knowledge Curator | 4 | reversible |
| Safety / Guardrail | 4 | reversible |
| Work-Order & MES | 3 | soft → irreversible |
| Governance & Lineage | 4 | reversible |
| HITL Supervisor | 4 | reversible |
| Shop-Floor Copilot UI | 4–5 | reversible |

For the full component mapping see [CMMC L2 Mapping](../governance/cmmc_l2_mapping.md).
