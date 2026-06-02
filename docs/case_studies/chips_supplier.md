# CHIPS Act Supplier

**Scenario:** A 300-person semiconductor packaging shop that landed a CHIPS Act
incentive agreement. DOD contract requires CMMC Level 2 by end of year. The shop
runs three production lines with Allen-Bradley PLCs, a Rockwell FTPC historian, and
Infor EAM as their CMMS. They need an AI assistant that is CMMC-compliant from day one.

## Architecture for This Use Case

```
Cloud (Azure Gov)
    └── Anthropic Claude (via Bedrock GovCloud endpoint)

Edge Server (on-prem, air-gapped production floor)
    ├── industrial-agents framework
    ├── OPA policy engine (cmmc_l2.rego)
    ├── Mosquitto MQTT broker (Sparkplug B)
    ├── ChromaDB (SOP vectors)
    └── Jaeger (distributed tracing)

Field Devices (Purdue zone 0–2)
    ├── Allen-Bradley PLCs → MQTT gateway → Sparkplug B
    └── Rockwell FTPC historian → OPC UA read-only
```

## Deployment

```bash
# Use AWS Bedrock for the LLM (GovCloud endpoint)
export LLM_PROVIDER=bedrock
export AWS_DEFAULT_REGION=us-gov-west-1
export BEDROCK_MODEL_ID=anthropic.claude-3-5-sonnet-20241022-v2:0

# Generate synthetic test data before go-live
industrial-agents seed-synthetic --hours 168 --format parquet

# Run the full benchmark against the Bedrock endpoint
industrial-agents bench --suite all --provider bedrock
```

## CMMC Level 2 Controls in Production

| Domain | Practice | Implementation |
|--------|----------|----------------|
| AC | AC.L2-3.1.3 (CUI flow) | `UNSContextBrokerAgent` blocks cross-zone writes |
| AU | AU.L2-3.3.1 (audit logs) | OpenLineage events to immutable S3 bucket |
| AU | AU.L2-3.3.2 (user accountability) | Ed25519-signed `AgentDecision` objects |
| CM | CM.L2-3.4.1 (baseline config) | All YAML configs in git, signed commits |
| IA | IA.L2-3.5.1 (user ID) | `AgentMessage.sender` field in every message |
| RA | RA.L2-3.11.1 (risk assessment) | `AnomalyRootCauseAgent` with FMEA traversal |
| SI | SI.L2-3.14.6 (attack detection) | `IndustrialMetrics` Prometheus dashboards |

## Governance Export for Auditors

```bash
# Export all signed decisions for the audit period
industrial-agents governance-export \
  --since 2026-01-01T00:00:00Z \
  --format json > cmmc_audit_2026_q1.json
```

Each record in the export includes:
- Agent name and action taken
- Ed25519 signature (verifiable against the public key in `config/`)
- NIST AI RMF function tag
- Purdue zone of the affected resource
- Confidence score and reversibility classification
