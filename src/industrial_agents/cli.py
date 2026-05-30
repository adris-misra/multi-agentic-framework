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
    provider: str = typer.Option("anthropic", "--provider", "-p", help="LLM provider."),
) -> None:
    """Start an interactive chat session with the operator copilot."""
    typer.echo("chat subcommand — implemented in Phase 3.")
    raise typer.Exit(code=1)


@app.command()
def bench(
    suite: str = typer.Option("all", "--suite", "-s", help="Benchmark suite name."),
    model: str = typer.Option("llama3.1:8b", "--model", "-m", help="Model identifier."),
) -> None:
    """Run the Industrial Agent Benchmark (IABENCH-v1)."""
    typer.echo("⚙  bench subcommand — implemented in Phase 7.")
    raise typer.Exit(code=1)


@app.command(name="seed-synthetic")
def seed_synthetic(
    seed: int = typer.Option(42, "--seed", help="Random seed for reproducibility."),
    out: str = typer.Option("data/synthetic/", "--out", help="Output directory."),
) -> None:
    """Generate the synthetic UNS dataset used for benchmarks and examples."""
    typer.echo("⚙  seed-synthetic subcommand — implemented in Phase 6.")
    raise typer.Exit(code=1)


@app.command(name="governance-export")
def governance_export(
    since: str = typer.Option(..., "--since", help="ISO 8601 start timestamp."),
    fmt: str = typer.Option("json", "--format", help="Output format: json or csv."),
) -> None:
    """Export signed governance decisions since a given timestamp."""
    typer.echo("⚙  governance-export subcommand — implemented in Phase 5.")
    raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
