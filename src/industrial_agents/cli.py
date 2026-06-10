"""CLI entry point for the Industrial Agentic Intelligence Framework."""

from __future__ import annotations

import uuid

import structlog
import typer

from industrial_agents.agents.base import AgentMessage

log = structlog.get_logger(__name__)

app = typer.Typer(
    name="industrial-agents",
    help=(
        "Industrial Agentic Intelligence Framework — "
        "UNS-native, cybersecurity-aware multi-agent AI for U.S. manufacturing."
    ),
    add_completion=False,
)


@app.command()
def run(
    requirement: str = typer.Argument(..., help="Natural-language operator query."),
    provider: str = typer.Option("anthropic", "--provider", "-p", help="LLM provider."),
) -> None:
    """Run the 10-agent pipeline on a single operator query."""
    import structlog.contextvars

    structlog.contextvars.clear_contextvars()
    trace_id = str(uuid.uuid4())
    structlog.contextvars.bind_contextvars(trace_id=trace_id)

    message = AgentMessage(sender="cli", intent=requirement, trace_id=trace_id)

    typer.echo(f"[trace={trace_id}] Routing: {requirement!r}")
    from industrial_agents.orchestration.routing_policy import RoutingPolicy

    policy = RoutingPolicy()
    target = policy.route(message)
    typer.echo(f"→ Routed to: {target.value}")
    typer.echo(f"LLM provider: {provider} (pipeline wired in Phase 3)")
    raise typer.Exit(code=0)


@app.command()
def chat(
    _provider: str = typer.Option("anthropic", "--provider", "-p", help="LLM provider."),
) -> None:
    """Start an interactive chat session with the operator copilot."""
    typer.echo("chat subcommand — implemented in Phase 3.")
    raise typer.Exit(code=1)


@app.command()
def bench(
    suite: str = typer.Option("all", "--suite", "-s", help="Task ID or 'all'."),
    model: str = typer.Option("llama3.1:8b", "--model", "-m", help="Model identifier."),
    provider: str = typer.Option("ollama", "--provider", "-p", help="LLM provider."),
    out: str = typer.Option("benchmarks/results/", "--out", help="Output directory."),
    supplementary: bool = typer.Option(False, "--supplementary", help="Also run IA-LIN."),
    judge_model: str = typer.Option(
        "",
        "--judge-model",
        help=(
            "Model used as LLM-as-judge in IA-5 hallucination scoring. "
            "Defaults to the same model as the agent under test. "
            "Using a different (typically larger) judge model reduces sycophancy risk."
        ),
    ),
) -> None:
    """Run the Industrial Agent Benchmark (IABENCH-v1)."""
    import asyncio
    from pathlib import Path

    from benchmarks.iabench import run_suite

    resolved_judge = judge_model.strip() or None
    typer.echo(f"Running IABENCH-v1 suite={suite} model={model} provider={provider}...")
    out_path = Path(out) / f"iabench_{suite}_{model.replace(':', '_')}.json"

    result_suite = asyncio.run(
        run_suite(
            suite_name=suite,
            model=model,
            provider=provider,
            output_path=out_path,
            include_supplementary=supplementary,
            judge_model=resolved_judge,
        )
    )

    summary = result_suite.summary()
    implemented = summary["passed"] + summary["failed"]
    typer.echo(
        f"Results: {summary['passed']}/{implemented} implemented tasks passed"
        f" | {summary['not_implemented']} stubs skipped. Saved to {out_path}"
    )
    raise typer.Exit(code=0 if result_suite.passed() else 1)


@app.command(name="seed-synthetic")
def seed_synthetic(
    seed: int = typer.Option(42, "--seed", help="Random seed for reproducibility."),
    out: str = typer.Option("data/synthetic/", "--out", help="Output directory."),
    hours: int = typer.Option(24, "--hours", help="Hours of telemetry to generate."),
    fmt: str = typer.Option("jsonl", "--format", help="Output format: jsonl or parquet."),
) -> None:
    """Generate the synthetic UNS dataset used for benchmarks and examples."""
    from pathlib import Path

    from industrial_agents.synthetic.uns_generator import UNSDataGenerator

    typer.echo(f"Generating {hours}h synthetic UNS dataset (seed={seed})...")
    gen = UNSDataGenerator(seed=seed)
    data = gen.generate(n_hours=hours)
    out_path = Path(out)

    if fmt == "parquet":
        gen.save_parquet(data, out_path / "telemetry.parquet")
    else:
        gen.save_jsonl(data, out_path / "telemetry.jsonl")

    meta = data["metadata"]
    typer.echo(
        f"Done: {meta['n_rows']:,} rows, {meta['n_assets']} assets, "
        f"{len(meta['anomalies'])} injected anomalies → {out}"
    )
    raise typer.Exit(code=0)


@app.command(name="governance-export")
def governance_export(
    _since: str = typer.Option(..., "--since", help="ISO 8601 start timestamp."),
    _fmt: str = typer.Option("json", "--format", help="Output format: json or csv."),
) -> None:
    """Export signed governance decisions since a given timestamp."""
    typer.echo("⚙  governance-export subcommand — implemented in Phase 5.")
    raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
