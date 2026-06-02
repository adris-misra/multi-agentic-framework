"""Unit tests for synthetic UNS data generator."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from industrial_agents.synthetic.uns_generator import UNSDataGenerator


class TestUNSDataGenerator:
    @pytest.fixture()
    def gen(self) -> UNSDataGenerator:
        return UNSDataGenerator(seed=42)

    def test_generate_returns_rows_and_metadata(self, gen: UNSDataGenerator) -> None:
        data = gen.generate(n_hours=1)
        assert "rows" in data
        assert "metadata" in data
        assert data["metadata"]["n_hours"] == 1

    def test_row_count(self, gen: UNSDataGenerator) -> None:
        data = gen.generate(n_hours=1, interval_seconds=60)
        meta = data["metadata"]
        assert meta["n_rows"] == len(data["rows"])
        assert meta["n_rows"] > 0

    def test_row_schema(self, gen: UNSDataGenerator) -> None:
        data = gen.generate(n_hours=1)
        row = data["rows"][0]
        assert "timestamp_utc" in row
        assert "uns_path" in row
        assert "sparkplug_topic" in row
        assert "asset_id" in row
        assert "value" in row
        assert "quality" in row

    def test_uns_path_format(self, gen: UNSDataGenerator) -> None:
        data = gen.generate(n_hours=1)
        for row in data["rows"][:10]:
            parts = row["uns_path"].split("/")
            assert len(parts) >= 5

    def test_sparkplug_topic_format(self, gen: UNSDataGenerator) -> None:
        data = gen.generate(n_hours=1)
        for row in data["rows"][:10]:
            assert row["sparkplug_topic"].startswith("spBv1.0/")

    def test_anomalies_injected(self, gen: UNSDataGenerator) -> None:
        data = gen.generate(n_hours=24, inject_anomalies=True)
        assert len(data["metadata"]["anomalies"]) >= 3

    def test_no_anomalies_when_disabled(self, gen: UNSDataGenerator) -> None:
        data = gen.generate(n_hours=24, inject_anomalies=False)
        assert len(data["metadata"]["anomalies"]) == 0

    def test_reproducible_with_same_seed(self) -> None:
        g1 = UNSDataGenerator(seed=99)
        g2 = UNSDataGenerator(seed=99)
        d1 = g1.generate(n_hours=1)
        d2 = g2.generate(n_hours=1)
        assert d1["rows"][0]["value"] == d2["rows"][0]["value"]

    def test_different_seeds_differ(self) -> None:
        g1 = UNSDataGenerator(seed=1)
        g2 = UNSDataGenerator(seed=2)
        d1 = g1.generate(n_hours=1)
        d2 = g2.generate(n_hours=1)
        values1 = [r["value"] for r in d1["rows"][:20]]
        values2 = [r["value"] for r in d2["rows"][:20]]
        assert values1 != values2

    def test_save_jsonl(self, gen: UNSDataGenerator, tmp_path: Path) -> None:
        data = gen.generate(n_hours=1)
        out = tmp_path / "telemetry.jsonl"
        gen.save_jsonl(data, out)
        assert out.exists()
        lines = out.read_text().strip().split("\n")
        assert len(lines) == len(data["rows"])
        first = json.loads(lines[0])
        assert "timestamp_utc" in first

    def test_anomaly_causes_value_spike(self, gen: UNSDataGenerator) -> None:
        data = gen.generate(n_hours=6, inject_anomalies=True)
        motor_vibration = [
            r
            for r in data["rows"]
            if r["asset_id"] == "motor_01" and r["signal"] == "vibration_rms"
        ]
        values = [r["value"] for r in motor_vibration]
        baseline = sorted(values)[len(values) // 2]  # median
        max_val = max(values)
        assert max_val > baseline * 2, "Expected anomaly spike in motor_01 vibration"
