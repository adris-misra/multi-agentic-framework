"""Unit tests for IABENCH benchmark harness."""

from __future__ import annotations

import json

import pytest
from benchmarks.iabench import (
    _IA7_HITL_THRESHOLD,
    BenchmarkResult,
    BenchmarkSuite,
    _compute_macro_f1,
    _evaluate_routing_policy,
    _load_routing_cases,
    _make_anomaly_dataset,
    _make_stub,
    _ndcg_at_5,
    _normalize_doc_id,
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


class TestNormalizeDocId:
    def test_exact_match(self) -> None:
        assert _normalize_doc_id("SOP-MAINT-001") == "SOP-MAINT-001"

    def test_case_insensitive(self) -> None:
        assert _normalize_doc_id("sop-maint-001") == "SOP-MAINT-001"

    def test_embedded_in_path(self) -> None:
        assert _normalize_doc_id("data/sops/SOP-MAINT-002-hydraulic.md") == "SOP-MAINT-002"

    def test_expert_note_id(self) -> None:
        assert _normalize_doc_id("EN-001 expert notes") == "EN-001"

    def test_unknown_returns_stripped(self) -> None:
        result = _normalize_doc_id("  some-unknown-doc  ")
        assert result == "some-unknown-doc"

    def test_longer_id_wins_over_shorter(self) -> None:
        # SOP-MAINT-001 should match before EN-001 when both appear
        result = _normalize_doc_id("SOP-MAINT-001 references EN-001")
        assert result == "SOP-MAINT-001"


class TestNdcgAt5:
    def test_perfect_ranking(self) -> None:
        qrels = {"A": 2, "B": 1}
        score = _ndcg_at_5(["A", "B"], qrels)
        assert score == pytest.approx(1.0)

    def test_empty_retrieved(self) -> None:
        qrels = {"A": 2}
        assert _ndcg_at_5([], qrels) == pytest.approx(0.0)

    def test_no_relevant_docs(self) -> None:
        qrels: dict[str, int] = {}
        assert _ndcg_at_5(["A", "B"], qrels) == pytest.approx(0.0)

    def test_wrong_order_lower_than_perfect(self) -> None:
        qrels = {"A": 2, "B": 1}
        perfect = _ndcg_at_5(["A", "B"], qrels)
        reversed_order = _ndcg_at_5(["B", "A"], qrels)
        assert reversed_order < perfect

    def test_irrelevant_docs_score_zero(self) -> None:
        qrels = {"GOOD": 2}
        score = _ndcg_at_5(["BAD1", "BAD2", "BAD3"], qrels)
        assert score == pytest.approx(0.0)

    def test_only_first_five_scored(self) -> None:
        qrels = {"SIXTH": 2}
        # SIXTH is at position 6 — beyond @5 cutoff → should score 0
        score = _ndcg_at_5(["A", "B", "C", "D", "E", "SIXTH"], qrels)
        assert score == pytest.approx(0.0)

    def test_partial_relevance(self) -> None:
        qrels = {"A": 2, "B": 1}
        score = _ndcg_at_5(["A"], qrels)
        assert 0.0 < score < 1.0


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


# ---------------------------------------------------------------------------
# IA-7 helpers
# ---------------------------------------------------------------------------


class TestEvaluateRoutingPolicy:
    """Tests for _evaluate_routing_policy — deterministic routing from config."""

    def test_high_conf_reversible_zone3_auto_proceed(self) -> None:
        assert _evaluate_routing_policy(0.95, "reversible", 3) == "auto_proceed"

    def test_high_conf_soft_zone4_auto_proceed(self) -> None:
        assert _evaluate_routing_policy(0.90, "soft", 4) == "auto_proceed"

    def test_confidence_exactly_at_threshold_auto_proceed(self) -> None:
        assert _evaluate_routing_policy(_IA7_HITL_THRESHOLD, "reversible", 3) == "auto_proceed"

    def test_confidence_just_below_threshold_escalates(self) -> None:
        below = _IA7_HITL_THRESHOLD - 0.01
        assert _evaluate_routing_policy(below, "reversible", 3) == "escalate"

    def test_moderate_conf_reversible_escalates(self) -> None:
        assert _evaluate_routing_policy(0.75, "reversible", 3) == "escalate"

    def test_low_conf_reversible_escalates(self) -> None:
        assert _evaluate_routing_policy(0.20, "reversible", 4) == "escalate"

    def test_moderate_conf_soft_escalates(self) -> None:
        assert _evaluate_routing_policy(0.80, "soft", 3) == "escalate"

    def test_irreversible_high_conf_blocks(self) -> None:
        assert _evaluate_routing_policy(0.95, "irreversible", 3) == "block"

    def test_irreversible_low_conf_blocks(self) -> None:
        assert _evaluate_routing_policy(0.20, "irreversible", 4) == "block"

    def test_irreversible_takes_priority_over_low_conf(self) -> None:
        # block wins over escalate — irreversibility checked first
        assert _evaluate_routing_policy(0.10, "irreversible", 3) == "block"

    def test_zone1_high_conf_reversible_blocks(self) -> None:
        assert _evaluate_routing_policy(0.95, "reversible", 1) == "block"

    def test_zone0_high_conf_reversible_blocks(self) -> None:
        assert _evaluate_routing_policy(0.95, "reversible", 0) == "block"

    def test_zone1_high_conf_soft_blocks(self) -> None:
        assert _evaluate_routing_policy(0.90, "soft", 1) == "block"

    def test_zone2_is_not_blocked_by_zone_rule(self) -> None:
        # zone 2 is above the blocked-zone threshold
        assert _evaluate_routing_policy(0.95, "reversible", 2) == "auto_proceed"

    def test_threshold_constant_is_0_85(self) -> None:
        assert pytest.approx(0.85) == _IA7_HITL_THRESHOLD


class TestComputeMacroF1:
    """Tests for _compute_macro_f1 — macro-averaged F1 across routing classes."""

    def test_perfect_predictions_return_1_0(self) -> None:
        preds = ["auto_proceed", "escalate", "block", "escalate", "block"]
        truth = ["auto_proceed", "escalate", "block", "escalate", "block"]
        f1, _ = _compute_macro_f1(preds, truth)
        assert f1 == pytest.approx(1.0)

    def test_all_wrong_return_0_0(self) -> None:
        preds = ["block", "block", "block"]
        truth = ["auto_proceed", "escalate", "auto_proceed"]
        f1, _ = _compute_macro_f1(preds, truth)
        assert f1 == pytest.approx(0.0)

    def test_per_class_keys_present(self) -> None:
        preds = ["auto_proceed", "escalate"]
        truth = ["auto_proceed", "escalate"]
        _, per_class = _compute_macro_f1(preds, truth)
        assert set(per_class.keys()) == {"auto_proceed", "escalate", "block"}

    def test_per_class_fields_present(self) -> None:
        preds = ["auto_proceed"]
        truth = ["auto_proceed"]
        _, per_class = _compute_macro_f1(preds, truth)
        cls = per_class["auto_proceed"]
        assert "precision" in cls
        assert "recall" in cls
        assert "f1" in cls
        assert "tp" in cls

    def test_class_absent_from_predictions_contributes_zero_f1(self) -> None:
        # "block" never predicted — its F1 should be 0
        preds = ["auto_proceed", "escalate", "auto_proceed"]
        truth = ["auto_proceed", "escalate", "block"]
        f1, per_class = _compute_macro_f1(preds, truth)
        assert per_class["block"]["f1"] == pytest.approx(0.0)
        assert f1 < 1.0

    def test_single_class_all_correct(self) -> None:
        preds = ["escalate", "escalate", "escalate"]
        truth = ["escalate", "escalate", "escalate"]
        f1, per_class = _compute_macro_f1(preds, truth)
        assert per_class["escalate"]["f1"] == pytest.approx(1.0)
        # Other classes absent in both — P and R undefined → 0 for those classes
        assert f1 == pytest.approx(1 / 3)

    def test_macro_f1_is_mean_of_per_class(self) -> None:
        preds = ["auto_proceed", "escalate", "block"]
        truth = ["auto_proceed", "escalate", "block"]
        f1, per_class = _compute_macro_f1(preds, truth)
        expected = sum(per_class[c]["f1"] for c in per_class) / len(per_class)
        assert f1 == pytest.approx(expected)


class TestLoadRoutingCases:
    """Tests for _load_routing_cases — JSON corpus loader."""

    def test_returns_list(self) -> None:
        cases = _load_routing_cases()
        assert isinstance(cases, list)

    def test_has_enough_cases(self) -> None:
        cases = _load_routing_cases()
        assert len(cases) >= 15

    def test_required_fields_present(self) -> None:
        cases = _load_routing_cases()
        required = {"case_id", "confidence", "reversibility", "purdue_zone", "expected_routing"}
        for case in cases:
            assert required.issubset(case.keys()), f"Missing fields in {case['case_id']}"

    def test_confidence_in_range(self) -> None:
        cases = _load_routing_cases()
        for case in cases:
            assert 0.0 <= float(case["confidence"]) <= 1.0

    def test_reversibility_valid_values(self) -> None:
        valid = {"reversible", "soft", "irreversible"}
        cases = _load_routing_cases()
        for case in cases:
            assert case["reversibility"] in valid

    def test_expected_routing_valid_values(self) -> None:
        valid = {"auto_proceed", "escalate", "block"}
        cases = _load_routing_cases()
        for case in cases:
            assert case["expected_routing"] in valid, (
                f"case {case['case_id']} has invalid expected_routing: {case['expected_routing']}"
            )

    def test_expected_routing_matches_policy(self) -> None:
        """Ground truth in the JSON must match the routing policy implementation."""
        cases = _load_routing_cases()
        mismatches = []
        for case in cases:
            actual = _evaluate_routing_policy(
                float(case["confidence"]),
                str(case["reversibility"]),
                int(case["purdue_zone"]),
            )
            if actual != case["expected_routing"]:
                mismatches.append(
                    f"{case['case_id']}: policy={actual} json={case['expected_routing']}"
                )
        assert not mismatches, "Ground truth mismatch:\n" + "\n".join(mismatches)

    def test_covers_all_three_routing_outcomes(self) -> None:
        cases = _load_routing_cases()
        outcomes = {case["expected_routing"] for case in cases}
        assert outcomes == {"auto_proceed", "escalate", "block"}
