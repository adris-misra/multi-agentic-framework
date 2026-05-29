# Architecture

> **Status:** Skeleton — filled in during Phase 8.

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

*TBD — Phase 8*

## Agent Topology

*TBD — Phase 8. Will include Mermaid sequence and component diagrams.*

## UNS Context Broker

*TBD — Phase 8. Deep-dive on the keystone agent: path resolution, zone enforcement, metadata decoration.*

## Orchestration Layer

*TBD — Phase 8.*

## Governance Bus

*TBD — Phase 8.*

## Security Model

*TBD — Phase 8. Covers Purdue zoning, mTLS, OPA policies, secrets vault.*

## Observability

*TBD — Phase 8. OpenTelemetry traces, Prometheus metrics, Jaeger.*

## Deployment Topologies

*TBD — Phase 8. Cloud (AWS/Azure/GCP), on-prem, air-gapped edge.*

## Standards Alignment Matrix

*TBD — Phase 8. Full ISA-95 / Sparkplug B / OPC UA / NIST 800-82 / CMMC / AI RMF matrix.*

---

**LLM Provider Choice:** `pyautogen >= 0.2` is used for the group-chat orchestration layer because it provides the most mature ConversableAgent abstractions for the 10-agent topology and is available as a stable pip package. AutoGen 0.4+ (`autogen-agentchat`) will be evaluated for Phase 2 and adopted if the v0.4 API is stable at that time; the LLM provider abstraction in `src/industrial_agents/agents/_llm.py` isolates us from this decision.
