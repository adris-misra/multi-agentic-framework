# Contributing

Thank you for your interest in contributing to the Industrial Agentic Intelligence Framework.

## Before You Start

- Read the [Code of Conduct](CODE_OF_CONDUCT.md).
- Open an issue to discuss significant changes before submitting a PR.
- For security vulnerabilities, follow the process in [SECURITY.md](SECURITY.md).

## Development Setup

```bash
git clone https://github.com/adris-misra/multi-agentic-framework.git
cd multi-agentic-framework
make install
```

## Workflow

1. Fork the repo and create a branch: `git checkout -b phase-N/short-description` (or `feat/short-description` for community contributions).
2. Write code + tests. Run `make lint typecheck test` before pushing.
3. Open a PR against `main`. Use the PR template in `.github/PULL_REQUEST_TEMPLATE.md`.

## Code Style

- **Formatter/linter:** `ruff` (configured in `pyproject.toml`; run `make format`).
- **Type checker:** `mypy --strict` on `src/` (run `make typecheck`).
- **Line length:** 100 characters.
- **Docstrings:** Google style.
- No `print()` in `src/`; use `structlog`.

## Testing

- Unit tests: `tests/unit/` — no I/O, no LLM calls, no docker.
- Integration tests: `tests/integration/` — require the docker-compose stack (`make demo`).
- Eval tests: `tests/eval/` — LLM-quality regressions; nightly only.
- Target ≥ 80% line coverage on `src/`.

## Commit Convention

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
feat(agents): add bearing-wear anomaly detection heuristic
fix(tools): handle OPC UA reconnect on timeout
docs(standards): add ISA-88 batch recipe alignment notes
```

## Industrial Domain Notes

- All UNS paths must be validated against `config/uns_topic_taxonomy.yaml`.
- Any agent action that mutates state at Purdue zone ≤ 2 must pass Safety/Guardrail review.
- Do not add LLM providers beyond those in §2.3 of the spec without a prior issue.
