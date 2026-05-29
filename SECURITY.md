# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| 0.1.x   | Yes       |

## Reporting a Vulnerability

**Do not open a public GitHub issue for security vulnerabilities.**

Please report vulnerabilities via GitHub's private [Security Advisory](https://github.com/adris-misra/multi-agentic-framework/security/advisories/new) feature.

Include:
- A description of the vulnerability and its potential impact
- Steps to reproduce
- Affected versions
- Any suggested mitigations

You will receive an acknowledgement within **72 hours** and a resolution timeline within **7 days**.

## Scope

This framework is intended for use in operational technology (OT) environments adjacent to manufacturing control systems. Vulnerabilities that could affect:

- Purdue zone enforcement bypass
- OPA policy evasion
- Governance log tampering
- Prompt-injection paths that could reach Purdue zones ≤ 2
- Credential exposure in any adapter

are treated as **Critical** severity and will be patched on an expedited timeline.

## Security Design Principles

- **Zone enforcement first:** The UNS Context Broker mediates all tool calls and denies cross-zone violations before any LLM reasoning occurs.
- **Immutable audit log:** All agent decisions are Ed25519-signed and appended to an append-only store. Tampering is detectable.
- **Dry-run by default:** Write actions to CMMS/MES produce a diff for human review before committing.
- **NIST SP 800-82 alignment:** Declarative control mapping is maintained in `src/industrial_agents/security/nist80082_controls.py`.
- **CMMC L2 alignment:** Policy engine gates every write; see `config/cmmc_l2_controls.yaml`.
