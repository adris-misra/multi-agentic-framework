# Industrial Agent Benchmark (IABENCH-v1)

> **Status:** Specification skeleton — fully implemented in Phase 7.

## Overview

IABENCH-v1 is a reproducible benchmark for evaluating multi-agent AI systems on
manufacturing-specific tasks. It is designed to be:

- **Runnable by anyone** using the synthetic dataset in `data/synthetic/`
- **LLM-agnostic** — scores for Claude, GPT-4o, and Llama 3.1 8B are provided
- **Citable** as an independent artifact

## Task Inventory

| Task ID | Name | Metric | Target |
|---------|------|--------|--------|
| TASK-IA-1 | Root-cause attribution | Precision/Recall F1 | TBD |
| TASK-IA-2 | Tacit-knowledge retrieval | nDCG@5 | TBD |
| TASK-IA-3 | Safety guardrail compliance | Block-rate, FPR | TBD |
| TASK-IA-4 | Multi-source synthesis | Expert-rated rubric | TBD |
| TASK-IA-5 | Hallucination rate | % hallucinated claims | < 2% |
| TASK-IA-6 | Token cost per decision | USD / decision | TBD |
| TASK-IA-7 | Escalation appropriateness | Mean-time accuracy | TBD |

## Running the Benchmark

```bash
# Default: Ollama (Llama 3.1 8B), no cloud required
make bench

# Specific model
industrial-agents bench --suite all --model claude-sonnet-4-6

# Single task
industrial-agents bench --task TASK-IA-1 --model gpt-4o
```

## Leaderboard

See [leaderboard.md](leaderboard.md) — populated in Phase 7.

## Detailed Task Specs

Task definitions, prompts, ground truth, and scoring rubrics live in `benchmarks/tasks/`.
Each file follows the naming convention `task_ia_<N>.yaml`.

*Full content added in Phase 7.*
