# UNS Context Broker Agent

The **UNS Context Broker** is the single mandatory gateway for all agent tool calls. No
agent may read from or write to an industrial asset directly — every request must pass
through this agent, which validates the Sparkplug B topic or ISA-95 path and enforces
Purdue zone policies before forwarding.

## Responsibilities

1. **Topic validation** — Resolves and validates UNS paths in both Sparkplug B format
   (`spBv1.0/<group>/<msg_type>/<edge_node>[/<device>]`) and ISA-95 hierarchical format
   (`enterprise/site/area/line/cell/asset/signal`).

2. **Zone enforcement** — Checks the requesting agent's zone against the target resource's
   zone. Write operations to zones 0–2 are blocked unless the OPA policy engine grants
   explicit permission.

3. **Write gating** — All non-read operations are routed through the `validate_write_gate`
   capability. The default threshold blocks writes to any resource at or below zone 2
   (supervisory and below).

## Configuration

```yaml
# config/purdue_zones.yaml
write_gate_zone_threshold: 2   # blocks writes to zones 0, 1, 2
```

## API

```python
from industrial_agents.agents.uns_context_broker import UNSContextBrokerAgent

agent = UNSContextBrokerAgent(
    name="uns_broker",
    llm=llm,
    context_broker=mock_broker,
    governance=governance,
    write_gate_zone_threshold=2,
)

# Validate a Sparkplug B topic
result = agent.resolve_path("spBv1.0/plant1/NDATA/line1/motor_01")
# result.purdue_zone == 1, result.sparkplug == True

# Block a write to zone 1
allowed = agent.validate_zone(agent_zone=3, target_zone=1)
# allowed == False (blocked by write gate)
```

## Topic Format Reference

| Format | Example | Zone |
|--------|---------|------|
| Sparkplug B | `spBv1.0/plant/NDATA/line1/asset1` | 1 |
| ISA-95 (7 levels) | `acme/chicago/area1/line1/cell1/motor01/vibration` | 0 |
| ISA-95 (5 levels) | `acme/chicago/line1/cell1/motor01` | 1 |
| ISA-95 (3 levels) | `acme/chicago/area1` | 3 |
