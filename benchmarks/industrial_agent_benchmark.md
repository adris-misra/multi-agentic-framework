# Industrial Agent Benchmark (IABENCH-v1)

> **Status:** v1.0 — IA-1 and IA-3 fully implemented. IA-2, 4–7 are stubs scheduled
> for PRs 2–5 of the `bench/iabench-*` series.

## Overview

IABENCH-v1 is a reproducible benchmark for evaluating multi-agent AI systems on
manufacturing-specific tasks. It is designed to be:

- **Runnable by anyone** using the synthetic dataset in `data/synthetic/`
- **LLM-agnostic** — the same harness runs against Ollama (local, no API keys),
  Anthropic Claude, OpenAI GPT-4o, and AWS Bedrock
- **Citable** as an independent artifact once all 7 tasks are implemented

## Canonical Task Inventory

| Task ID | Name | Primary Metric | Pass Threshold | Status |
|---------|------|---------------|----------------|--------|
| IA-1 | Root-cause attribution | F1 | 0.70 | ✅ Implemented |
| IA-2 | Tacit-knowledge retrieval | nDCG@5 | 0.70 | 🔲 Stub (PR 2) |
| IA-3 | Safety guardrail compliance | block_rate, fpr | 0.90 / ≤0.10 | ✅ Implemented |
| IA-4 | Multi-source synthesis | rubric 1–5 | 3.5 | 🔲 Stub (PR 3) |
| IA-5 | Hallucination rate | % unsupported claims | ≤2% | 🔲 Stub (PR 3) |
| IA-6 | Token-cost-per-decision | USD/invocation | informational | 🔲 Stub (PR 4) |
| IA-7 | Mean-time-to-escalation | routing F1 | 0.80 | 🔲 Stub (PR 4) |

### Supplementary Check (not part of main suite)

| Task ID | Name | Metric | Notes |
|---------|------|--------|-------|
| IA-LIN | Governance lineage completeness | completeness (0–1) | Infrastructure canary; enable with `--supplementary` |

> **Numbering note:** An earlier harness version labelled tasks IA-4–7 differently
> from this spec. The canonical mapping above is authoritative. The old "lineage
> completeness" check that was previously called "IA-7" is now **IA-LIN** and runs
> as a supplementary check; see `benchmarks/tasks/task_ia_lin.yaml`.

## Running the Benchmark

```bash
# Default: Ollama (Llama 3.1 8B), no cloud required
industrial-agents bench --suite all --provider ollama --model llama3.1:8b

# Specific cloud model
industrial-agents bench --suite all --provider anthropic --model claude-sonnet-4-6

# Single task
industrial-agents bench --suite IA-1 --provider ollama

# Direct Python invocation (also works)
python -m benchmarks.iabench ollama llama3.1:8b

# Include supplementary IA-LIN check
industrial-agents bench --suite all --provider ollama --supplementary
```

## Interpreting Results

After a run, the JSON output in `benchmarks/results/` contains:

- `passed` / `failed` counts for implemented tasks only
- `not_implemented` count for stubs (these do not affect pass/fail)
- `reliable: false` on IA-3 if error_rate > 10% (LLM connectivity issue)
- Task-level `details` with per-sample breakdowns

**Warning signs:**
- IA-1 F1 = 1.0 exactly → possible bug or trivially easy dataset
- IA-3 block_rate = 1.0 AND error_rate > 0 → exceptions are being counted as blocks
- IA-3 fpr > 0.10 → guardrail is too aggressive; investigate benign verdicts

## Task Spec Files

Detailed scoring rubrics, input formats, limitations, and implementation
roadmaps for each task live in `benchmarks/tasks/`:

```
benchmarks/tasks/
├── task_ia_1.yaml   Root-cause attribution
├── task_ia_2.yaml   Tacit-knowledge retrieval
├── task_ia_3.yaml   Safety guardrail compliance
├── task_ia_4.yaml   Multi-source synthesis
├── task_ia_5.yaml   Hallucination rate
├── task_ia_6.yaml   Token-cost-per-decision
├── task_ia_7.yaml   Mean-time-to-escalation
└── task_ia_lin.yaml Governance lineage completeness (supplementary)
```

## Leaderboard

To be populated after all 7 tasks are implemented. Planned comparison:
- `llama3.1:8b` via Ollama (baseline, free)
- `claude-sonnet-4-6` via Anthropic
- `gpt-4o` via OpenAI

## Citation

Once the benchmark is published as an arXiv preprint, a `@misc` bibtex entry
will appear here. Until then, cite the GitHub repository.
