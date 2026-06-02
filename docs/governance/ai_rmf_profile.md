# NIST AI RMF Profile

This page documents how the framework maps to the four core functions of the
**NIST AI Risk Management Framework (AI RMF 1.0)**: GOVERN, MAP, MEASURE, and MANAGE.

## GOVERN

Establishes accountability, policies, and organizational roles for AI risk.

| Framework Component | AI RMF Control |
|--------------------|----------------|
| `GovernanceLineageAgent` | Maintains an immutable, Ed25519-signed audit log of every agent decision |
| `OPAClient` + Rego policies | Enforces write-gate policies before any irreversible action |
| `HITLSupervisorAgent` | Routes low-confidence decisions to human operators |
| `SecretsVault` | Manages credentials with least-privilege access |

## MAP

Identifies and categorizes AI risks in context.

| Framework Component | AI RMF Control |
|--------------------|----------------|
| `PurdueZoneEnforcer` | Maps each agent action to its Purdue zone impact |
| `UNSContextBrokerAgent` | Resolves UNS paths to physical assets, scoping potential blast radius |
| `AnomalyRootCauseAgent` | FMEA traversal maps anomalies to known failure modes and criticality |
| `RoutingPolicy` | Intent classification determines which agents handle each request |

## MEASURE

Analyzes and assesses AI risks and impacts.

| Framework Component | AI RMF Control |
|--------------------|----------------|
| `IABENCH-v1` | Seven-task benchmark suite measuring F1, block-rate, hallucination, lineage completeness |
| `IndustrialMetrics` (Prometheus) | Real-time counters for agent requests, errors, latency, escalations |
| `AgentDecision.confidence` | Every decision carries a calibrated confidence score |
| `SafetyGuardrailAgent` | OPA pre-check + LLM evaluation quantifies risk level before action |

## MANAGE

Prioritizes and addresses AI risks.

| Framework Component | AI RMF Control |
|--------------------|----------------|
| `EscalationRouter` | Halts irreversible or low-confidence decisions pending human review |
| `WorkOrderMESAgent` | Dry-run diff preview before any CMMS/MES write; idempotency keys prevent duplication |
| `GovernanceLineageAgent` | NIST function tags on every OpenLineage event (`GOVERN`, `MAP`, `MEASURE`, `MANAGE`) |
| `PIIRedactor` | Scrubs personal identifiers from agent messages before logging |

## NIST AI RMF Function Tags

The `GovernanceLineageAgent` tags every emitted OpenLineage event with its AI RMF function:

```python
_NIST_FUNCTION_MAP = {
    "read":             "MEASURE",
    "detect_anomaly":   "MEASURE",
    "evaluate_action":  "MANAGE",
    "block":            "GOVERN",
    "allow":            "MANAGE",
    "create_work_order":"MANAGE",
    "sign":             "GOVERN",
    "emit_lineage":     "GOVERN",
}
```

These tags appear in the `industrialGovernance` facet of each OpenLineage event and are
queryable via the governance export CLI command:

```bash
industrial-agents governance-export --since 2026-01-01T00:00:00Z --format json
```
