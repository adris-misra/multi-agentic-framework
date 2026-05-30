package industrial.safety

import future.keywords.if
import future.keywords.in

# Default: allow read operations, deny writes
default allow := false

# Allow all read operations
allow if {
    input.action == "read"
}

allow if {
    input.action == "read_telemetry"
}

allow if {
    input.action == "rag_query"
}

allow if {
    input.action == "export_audit_log"
}

# Allow write operations only when zone constraints are met
allow if {
    input.action == "create_work_order"
    not zone_violation
    not low_confidence
}

allow if {
    input.action == "emit_lineage"
}

allow if {
    input.action == "sign_decision"
}

# Block actions that violate Purdue zone boundaries
zone_violation if {
    input.context.target_zone <= 1
    input.action != "read"
}

zone_violation if {
    input.context.agent_zone > 3
    input.context.target_zone < 2
}

# Block low-confidence irreversible actions
low_confidence if {
    input.context.confidence < 0.85
    input.context.reversibility == "irreversible"
}

# CMMC L2: require explicit authorization for CUI-adjacent operations
cmmc_block if {
    input.action == "dispatch_work_order"
    not input.context.hitl_approved
}

# Safety interlocks — never allow unsupervised zone-0 writes
allow if {
    input.action == "emergency_stop"
    input.context.operator_confirmed == true
}
