package industrial.cmmc

import future.keywords.if
import future.keywords.in

# CMMC Level 2 policy gates for CUI-adjacent operations.
# Maps to NIST SP 800-171 practice families.

default compliant := false

# AC: Access Control — AC.L2-3.1.1
compliant if {
    practice := "AC"
    input.agent_role in {"governance_lineage", "safety_guardrail", "hitl_supervisor"}
    input.action in {"read", "read_telemetry", "evaluate_action", "emit_lineage"}
}

# AU: Audit and Accountability — AU.L2-3.3.1
compliant if {
    practice := "AU"
    input.context.audit_log_enabled == true
    input.context.signature != null
}

# IA: Identification and Authentication — IA.L2-3.5.3
compliant if {
    practice := "IA"
    input.context.mfa_verified == true
}

# CM: Configuration Management — CM.L2-3.4.1
compliant if {
    practice := "CM"
    input.action in {"read", "read_telemetry", "rag_query"}
}

# Deny write-to-production without audit trail
deny_write if {
    input.action in {"create_work_order", "dispatch_work_order"}
    input.context.audit_log_enabled != true
}

# Deny export of CUI without signature
deny_export if {
    input.action == "export_audit_log"
    input.context.signature == null
}
