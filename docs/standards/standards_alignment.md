# Standards Alignment Matrix

This page maps each external standard to the framework components that implement it.

## Industrial Protocols

| Standard | Role in Framework | Component |
|----------|-------------------|-----------|
| **MQTT Sparkplug B v3** | Primary UNS message transport | `SparkplugClient`, `UNSContextBrokerAgent` |
| **OPC UA (IEC 62541)** | Read-only historian access | `OPCUAClient` |
| **ISA-95 / IEC 62264** | Topic hierarchy structure | `UNSContextBrokerAgent`, `uns_topic_taxonomy.yaml` |
| **ISA-88** | Work-order phase structure | `WorkOrderMESAgent` |

## Cybersecurity

| Standard | Role in Framework | Component |
|----------|-------------------|-----------|
| **NIST SP 800-171 / CMMC L2** | Policy enforcement, audit trail | `OPAClient`, `GovernanceLineageAgent`, `SecretsVault` |
| **NIST SP 800-82 Rev 3** | Purdue zone model | `PurdueZoneEnforcer`, `UNSContextBrokerAgent` |
| **IEC 62443** | Zone-conduit architecture | `PurdueZoneEnforcer`, zone config YAML |

## AI / Data Governance

| Standard | Role in Framework | Component |
|----------|-------------------|-----------|
| **NIST AI RMF** | Govern / Map / Measure / Manage functions | `GovernanceLineageAgent` (NIST function map) |
| **ISO 42001** | AI management system alignment | Governance lineage, HITL escalation |
| **OpenLineage** | Immutable decision audit trail | `GovernanceLineageAgent`, `LineageBus` |

## Manufacturing Domain

| Standard | Role in Framework | Component |
|----------|-------------------|-----------|
| **ISO 14224** | Equipment taxonomy for FMEA | `AnomalyRootCauseAgent` (FMEA traversal) |
| **ISO 15926** | Equipment classification | `TacitKnowledgeCuratorAgent` (SOP indexing) |

## Cryptographic

| Standard | Role in Framework | Component |
|----------|-------------------|-----------|
| **Ed25519 (RFC 8032)** | Agent decision signing | `GovernanceLineageAgent.sign_decision()` |
| **FIPS 186-5** | Digital signature compliance | Ed25519 via `cryptography` library |

For CMMC Level 2 practice-by-practice mapping see [CMMC L2 Mapping](../governance/cmmc_l2_mapping.md).
