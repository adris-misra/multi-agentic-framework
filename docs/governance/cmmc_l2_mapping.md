# CMMC Level 2 Mapping

This document maps each CMMC L2 practice to the framework component that addresses it.

## Access Control (AC)

| Practice | Requirement | Framework Component |
|----------|-------------|---------------------|
| AC.L2-3.1.1 | Limit system access to authorized users | `PurdueZoneEnforcer`, `SecretsVault` |
| AC.L2-3.1.2 | Limit system access to types of transactions | `OPAClient` (`policies/cmmc_l2.rego`) |
| AC.L2-3.1.3 | Control CUI flow to external systems | `UNSContextBrokerAgent` write gate |
| AC.L2-3.1.5 | Employ principle of least privilege | Agent zone assignments (config/purdue_zones.yaml) |

## Audit and Accountability (AU)

| Practice | Requirement | Framework Component |
|----------|-------------|---------------------|
| AU.L2-3.3.1 | Create system audit logs | `GovernanceLineageAgent`, `LineageBus` |
| AU.L2-3.3.2 | Ensure accountability of users | Ed25519-signed `AgentDecision` objects |

## Identification and Authentication (IA)

| Practice | Requirement | Framework Component |
|----------|-------------|---------------------|
| IA.L2-3.5.1 | Identify system users | `AgentMessage.sender` field |
| IA.L2-3.5.3 | Use multifactor authentication | MFA context in OPA policy input |

## Configuration Management (CM)

| Practice | Requirement | Framework Component |
|----------|-------------|---------------------|
| CM.L2-3.4.1 | Establish baseline configurations | `config/` YAML files under version control |
| CM.L2-3.4.2 | Track changes to configurations | Git history + signed commits |

## Incident Response (IR)

| Practice | Requirement | Framework Component |
|----------|-------------|---------------------|
| IR.L2-3.6.1 | Establish incident response capability | `HITLSupervisorAgent` + `EscalationRouter` |

## Risk Assessment (RA)

| Practice | Requirement | Framework Component |
|----------|-------------|---------------------|
| RA.L2-3.11.1 | Assess risk to operations | `AnomalyRootCauseAgent` (FMEA traversal) |
| RA.L2-3.11.2 | Scan for vulnerabilities | `policies/industrial_safety.rego` |

## System and Communications Protection (SC)

| Practice | Requirement | Framework Component |
|----------|-------------|---------------------|
| SC.L2-3.13.1 | Monitor, control, and protect communications | Purdue zone enforcement |
| SC.L2-3.13.3 | Separate user functionality from system management | Agent role separation |

## System and Information Integrity (SI)

| Practice | Requirement | Framework Component |
|----------|-------------|---------------------|
| SI.L2-3.14.1 | Identify, report, and correct information flaws | `SafetyGuardrailAgent` + OPA |
| SI.L2-3.14.6 | Monitor organizational systems to detect attacks | `IndustrialMetrics` (Prometheus) |

---

*Last updated: 2026-05-29. See `policies/cmmc_l2.rego` for machine-readable policy enforcement.*
