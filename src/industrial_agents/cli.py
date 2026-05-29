"""CLI entry point for the Industrial Agentic Intelligence Framework.

Subcommands are implemented in Phase 2. This module registers the Typer app
so that `industrial-agents --help` works after `make install`.
"""

from __future__ import annotations

import typer

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
    """Run the full 10-agent pipeline on a single operator query."""
    typer.echo("⚙  run subcommand — implemented in Phase 2.")
    raise typer.Exit(code=1)


@app.command()
def chat(
    provider: str = typer.Option("anthropic", "--provider", "-p", help="LLM provider."),
) -> None:
    """Start an interactive chat session with the operator copilot."""
    typer.echo("⚙  chat subcommand — implemented in Phase 2.")
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
