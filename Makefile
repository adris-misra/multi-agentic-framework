# Makefile for Industrial Agentic Intelligence Framework
# Requires: Python 3.11+, Docker, docker-compose

PYTHON      := python3
VENV        := .venv
PIP         := $(VENV)/bin/pip
PYTEST      := $(VENV)/bin/pytest
RUFF        := $(VENV)/bin/ruff
MYPY        := $(VENV)/bin/mypy
PRECOMMIT   := $(VENV)/bin/pre-commit
MKDOCS      := $(VENV)/bin/mkdocs
CYCLONEDX   := $(VENV)/bin/cyclonedx-py

# Windows compatibility: use Scripts instead of bin
ifeq ($(OS),Windows_NT)
    PIP       := $(VENV)/Scripts/pip
    PYTEST    := $(VENV)/Scripts/pytest
    RUFF      := $(VENV)/Scripts/ruff
    MYPY      := $(VENV)/Scripts/mypy
    PRECOMMIT := $(VENV)/Scripts/pre-commit
    MKDOCS    := $(VENV)/Scripts/mkdocs
    PYTHON    := python
endif

.DEFAULT_GOAL := help

.PHONY: help install lint format typecheck test test-unit test-int test-eval \
        demo clean docs sbom bench

help:  ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
	  awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-18s\033[0m %s\n", $$1, $$2}'

install:  ## Create venv and install all dependencies (including dev extras)
	$(PYTHON) -m venv $(VENV)
	$(PIP) install --upgrade pip
	$(PIP) install -e ".[dev]"
	$(PRECOMMIT) install
	@echo "✓ Environment ready. Activate with: source $(VENV)/bin/activate"

lint:  ## Run ruff linter
	$(RUFF) check src/ tests/

format:  ## Auto-format with ruff
	$(RUFF) format src/ tests/
	$(RUFF) check --fix src/ tests/

format-check:  ## Check formatting without modifying files
	$(RUFF) format --check src/ tests/

typecheck:  ## Run mypy strict type checks on src/
	$(MYPY) src/

test:  ## Run unit tests with coverage
	$(PYTEST) tests/unit -q --tb=short

test-unit:  ## Run unit tests only
	$(PYTEST) tests/unit -q --tb=short

test-int:  ## Run integration tests (requires docker-compose stack)
	$(PYTEST) tests/integration -q --tb=short -m integration

test-eval:  ## Run LLM-quality eval tests (nightly; requires API keys)
	$(PYTEST) tests/eval -q --tb=short -m eval

demo:  ## Bring up the full docker-compose stack and print connection info
	@echo "Starting Industrial Agents demo stack..."
	docker compose -f docker/docker-compose.yml up -d
	@echo ""
	@echo "=== Connection Info ==="
	@echo "  MQTT Broker:   mqtt://localhost:1883"
	@echo "  ChromaDB:      http://localhost:8000"
	@echo "  Jaeger UI:     http://localhost:16686"
	@echo "  App:           http://localhost:8501"
	@echo ""
	@echo "Run 'make demo-down' to stop."

demo-down:  ## Stop the docker-compose stack
	docker compose -f docker/docker-compose.yml down

clean:  ## Remove build artifacts and caches
	rm -rf $(VENV) dist build *.egg-info .pytest_cache .mypy_cache .ruff_cache
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

docs:  ## Build MkDocs documentation site
	$(MKDOCS) build --strict

docs-serve:  ## Serve docs locally with live reload
	$(MKDOCS) serve

sbom:  ## Generate CycloneDX SBOM
	$(CYCLONEDX) environment --output-format json --output-file sbom.json
	@echo "SBOM written to sbom.json"

bench:  ## Run benchmark suite against synthetic dataset (Ollama default)
	$(PYTEST) benchmarks/ -q --tb=short
