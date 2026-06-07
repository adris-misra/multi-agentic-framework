"""Unit tests for IABENCH benchmark harness."""

from __future__ import annotations

import json

from benchmarks.iabench import (
    BenchmarkResult,
    BenchmarkSuite,
    _make_anomaly_dataset,
    _make_stub,
    _normalize_fault_type,
)


class TestBenchmarkDataStructures:
    def test_benchmark_result_pass(self) -> None:
        r = BenchmarkResult(
            task_id="IA-1",
            task_name="Root-cause",
            model="test",
            provider="mock",
            metric_name="F1",
            metric_value=0.85,
            pass_threshold=0.70,
            passed=True,
            n_samples=10,
            duration_seconds=1.5,
        )
        assert r.passed is True

    def test_benchmark_result_fail(self) -> None:
        r = BenchmarkResult(
            task_id="IA-1",
            task_name="Root-cause",
            model="test",
            provider="mock",
            metric_name="F1",
            metric_value=0.50,
            pass_threshold=0.70,
            passed=False,
            n_samples=10,
            duration_seconds=1.5,
        )
        assert r.passed is False

    def test_suite_summary_structure(self) -> None:
        suite = BenchmarkSuite(name="all", model="test", provider="mock")
        suite.results = [
            BenchmarkResult(
                task_id="T1",
                task_name="t",
                model="x",
                provider="y",
                metric_name="F1",
                metric_value=0.9,
                pass_threshold=0.7,
                passed=True,
                n_samples=5,
                duration_seconds=1.0,
            )
        ]
        s = suite.summary()
        assert s["total_tasks"] == 1
        assert s["passed"] == 1
        assert s["failed"] == 0

    def test_suite_passed_all(self) -> None:
        suite = BenchmarkSuite(name="all", model="test", provider="mock")
        suite.results = [
            BenchmarkResult(
                task_id="T1",
                task_name="t",
                model="x",
                provider="y",
                metric_name="F1",
                metric_value=0.9,
                pass_threshold=0.7,
                passed=True,
                n_samples=5,
                duration_seconds=1.0,
            )
        ]
        assert suite.passed() is True

    def test_suite_fails_if_any_fail(self) -> None:
        suite = BenchmarkSuite(name="all", model="test", provider="mock")
        suite.results = [
            BenchmarkResult(
                task_id="T1",
                task_name="t",
                model="x",
                provider="y",
                metric_name="F1",
                metric_value=0.9,
                pass_threshold=0.7,
                passed=True,
                n_samples=5,
                duration_seconds=1.0,
            ),
            BenchmarkResult(
                task_id="T2",
                task_name="t2",
                model="x",
                provider="y",
                metric_name="F1",
                metric_value=0.3,
                pass_threshold=0.7,
                passed=False,
                n_samples=5,
                duration_seconds=1.0,
            ),
        ]
        assert suite.passed() is False


class TestAnomalyDataset:
    def test_dataset_has_samples(self) -> None:
        samples = _make_anomaly_dataset()
        assert len(samples) >= 3

    def test_dataset_sample_schema(self) -> None:
        samples = _make_anomaly_dataset()
        for s in samples:
            assert "series" in s
            assert "asset_id" in s
            assert "ground_truth_anomaly_type" in s
            assert len(s["series"]) > 0


class TestBenchmarkIO:
    def test_summary_json_serializable(self) -> None:
        suite = BenchmarkSuite(name="test", model="m", provider="p")
        suite.results = [
            BenchmarkResult(
                task_id="T1",
                task_name="t",
                model="m",
                provider="p",
                metric_name="F1",
                metric_value=0.9,
                pass_threshold=0.7,
                passed=True,
                n_samples=1,
                duration_seconds=0.5,
            )
        ]
        # Should not raise — nan values serialized as strings via default=str
        serialized = json.dumps(suite.summary(), default=str)
        assert "T1" in serialized


class TestNormalizeFaultType:
    def test_underscore_to_dash(self) -> None:
        assert _normalize_fault_type("bearing_wear") == "bearing-wear"

    def test_space_to_dash(self) -> None:
        assert _normalize_fault_type("bearing wear") == "bearing-wear"

    def test_case_insensitive(self) -> None:
        assert _normalize_fault_type("Bearing_Wear") == "bearing-wear"

    def test_already_canonical(self) -> None:
        assert _normalize_fault_type("bearing-wear") == "bearing-wear"

    def test_mixed(self) -> None:
        assert _normalize_fault_type("Hydraulic Leak") == "hydraulic-leak"
        assert _normalize_fault_type("hydraulic_leak") == "hydraulic-leak"
        assert _normalize_fault_type("FILTER_CLOG") == "filter-clog"


class TestStubFactory:
    def test_stub_not_implemented(self) -> None:
        stub = _make_stub("IA-2", "Tacit-knowledge retrieval", "nDCG@5", "test", "mock")
        assert stub.not_implemented is True
        assert stub.passed is False
        assert stub.task_id == "IA-2"

    def test_stub_excluded_from_suite_passed(self) -> None:
        suite = BenchmarkSuite(name="all", model="test", provider="mock")
        suite.results = [
            BenchmarkResult(
                task_id="IA-1",
                task_name="Root-cause",
                model="test",
                provider="mock",
                metric_name="F1",
                metric_value=0.9,
                pass_threshold=0.7,
                passed=True,
                n_samples=3,
                duration_seconds=1.0,
            ),
            _make_stub("IA-2", "Tacit-knowledge retrieval", "nDCG@5", "test", "mock"),
        ]
        # Suite.passed() should be True because the only non-stub task passed
        assert suite.passed() is True

    def test_summary_counts_not_implemented_separately(self) -> None:
        suite = BenchmarkSuite(name="all", model="test", provider="mock")
        suite.results = [
            BenchmarkResult(
                task_id="IA-1",
                task_name="t",
                model="x",
                provider="y",
                metric_name="F1",
                metric_value=0.9,
                pass_threshold=0.7,
                passed=True,
                n_samples=3,
                duration_seconds=1.0,
            ),
            _make_stub("IA-2", "Tacit", "nDCG@5", "x", "y"),
        ]
        s = suite.summary()
        assert s["passed"] == 1
        assert s["failed"] == 0
        assert s["not_implemented"] == 1
        assert s["total_tasks"] == 2
