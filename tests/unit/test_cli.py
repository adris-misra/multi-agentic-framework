"""Unit tests for CLI entry points."""

from __future__ import annotations

from typer.testing import CliRunner

from industrial_agents.cli import app

runner = CliRunner()


class TestCLIHelp:
    def test_help_exits_zero(self) -> None:
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "industrial-agents" in result.output.lower() or "usage" in result.output.lower()

    def test_run_help(self) -> None:
        result = runner.invoke(app, ["run", "--help"])
        assert result.exit_code == 0

    def test_chat_help(self) -> None:
        result = runner.invoke(app, ["chat", "--help"])
        assert result.exit_code == 0

    def test_bench_help(self) -> None:
        result = runner.invoke(app, ["bench", "--help"])
        assert result.exit_code == 0

    def test_seed_synthetic_help(self) -> None:
        result = runner.invoke(app, ["seed-synthetic", "--help"])
        assert result.exit_code == 0

    def test_governance_export_help(self) -> None:
        result = runner.invoke(app, ["governance-export", "--help"])
        assert result.exit_code == 0


class TestRunCommand:
    def test_run_shows_routing(self) -> None:
        result = runner.invoke(app, ["run", "check motor vibration"])
        # CLI should show routing result and exit 0
        assert result.exit_code == 0
        assert "Routed to:" in result.output

    def test_run_safety_routes_to_safety(self) -> None:
        result = runner.invoke(app, ["run", "emergency stop on line 3"])
        assert result.exit_code == 0
        assert "safety_guardrail" in result.output

    def test_run_anomaly_routes_correctly(self) -> None:
        result = runner.invoke(app, ["run", "vibration anomaly on spindle"])
        assert result.exit_code == 0
        assert "anomaly_root_cause" in result.output


class TestUnimplementedCommands:
    def test_bench_exits_nonzero(self) -> None:
        result = runner.invoke(app, ["bench"])
        assert result.exit_code != 0

    def test_seed_synthetic_exits_nonzero(self) -> None:
        result = runner.invoke(app, ["seed-synthetic"])
        assert result.exit_code != 0
