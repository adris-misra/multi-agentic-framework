"""Unit tests for IABENCH benchmark harness."""

from __future__ import annotations

import asyncio
import json
from unittest.mock import AsyncMock

import pytest
from benchmarks.iabench import (
    BenchmarkResult,
    BenchmarkSuite,
    _compute_rubric_score,
    _estimate_tokens_from_messages,
    _extract_json_block,
    _judge_hallucination,
    _judge_synthesis_rubric,
    _load_pricing_table,
    _lookup_model_price,
    _make_anomaly_dataset,
    _make_stub,
    _ndcg_at_5,
    _normalize_doc_id,
    _normalize_fault_type,
    _TokenTracker,
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


class TestComputeRubricScore:
    def test_all_fives(self) -> None:
        verdict = {
            "factual_accuracy": 5,
            "source_coverage": 5,
            "actionability": 5,
            "safety_adherence": 5,
        }
        assert _compute_rubric_score(verdict) == pytest.approx(5.0)

    def test_all_ones(self) -> None:
        verdict = {
            "factual_accuracy": 1,
            "source_coverage": 1,
            "actionability": 1,
            "safety_adherence": 1,
        }
        assert _compute_rubric_score(verdict) == pytest.approx(1.0)

    def test_mixed_scores(self) -> None:
        verdict = {
            "factual_accuracy": 4,
            "source_coverage": 3,
            "actionability": 5,
            "safety_adherence": 2,
        }
        # mean = (4+3+5+2)/4 = 14/4 = 3.5
        assert _compute_rubric_score(verdict) == pytest.approx(3.5)

    def test_missing_dimension_defaults_to_one(self) -> None:
        verdict = {
            "factual_accuracy": 4,
            "source_coverage": 4,
            # actionability and safety_adherence missing
        }
        # mean = (4+4+1+1)/4 = 10/4 = 2.5
        assert _compute_rubric_score(verdict) == pytest.approx(2.5)

    def test_pass_threshold_boundary(self) -> None:
        verdict = {
            "factual_accuracy": 4,
            "source_coverage": 3,
            "actionability": 4,
            "safety_adherence": 3,
        }
        score = _compute_rubric_score(verdict)
        # 3.5 exactly is at threshold
        assert score == pytest.approx(3.5)
        assert score >= 3.5


class TestTokenTracker:
    """Unit tests for _TokenTracker wrapper."""

    def _make_mock_llm(self, input_tok: int, output_tok: int) -> object:
        """Return a fake LLM that reports fixed token counts."""

        class FakeLLM:
            async def complete(
                self,
                messages: list,
                *,
                model=None,
                temperature=0.2,
                max_tokens=2048,
                tools=None,
            ) -> dict:
                return {
                    "content": [{"type": "text", "text": "ok"}],
                    "usage": {"input_tokens": input_tok, "output_tokens": output_tok},
                }

        return FakeLLM()

    def test_accumulates_tokens(self) -> None:
        import asyncio

        fake_llm = self._make_mock_llm(100, 50)
        tracker = _TokenTracker(fake_llm)

        async def run() -> None:
            await tracker.complete([{"role": "user", "content": "hello"}])
            await tracker.complete([{"role": "user", "content": "world"}])

        asyncio.run(run())
        assert tracker.input_tokens == 200
        assert tracker.output_tokens == 100

    def test_reset_clears_counts(self) -> None:
        import asyncio

        fake_llm = self._make_mock_llm(100, 50)
        tracker = _TokenTracker(fake_llm)

        async def run() -> None:
            await tracker.complete([{"role": "user", "content": "hello"}])

        asyncio.run(run())
        tracker.reset()
        assert tracker.input_tokens == 0
        assert tracker.output_tokens == 0

    def test_stores_last_messages(self) -> None:
        import asyncio

        fake_llm = self._make_mock_llm(10, 5)
        tracker = _TokenTracker(fake_llm)
        msgs = [{"role": "user", "content": "test"}]

        async def run() -> None:
            await tracker.complete(msgs)

        asyncio.run(run())
        assert tracker._last_messages == msgs

    def test_zero_input_tokens_triggers_estimation(self) -> None:
        # When input_tokens is 0, _estimate_tokens_from_messages should be used.
        fake_llm = self._make_mock_llm(0, 30)
        import asyncio

        tracker = _TokenTracker(fake_llm)

        async def run() -> None:
            await tracker.complete([{"role": "user", "content": "hello world test message"}])

        asyncio.run(run())
        # Tracker accumulates 0 from provider — caller must check and estimate
        assert tracker.input_tokens == 0
        assert tracker.output_tokens == 30
        # Estimation function should give a positive result for non-empty messages
        estimated = _estimate_tokens_from_messages(tracker._last_messages)
        assert estimated > 0


class TestEstimateTokens:
    def test_non_empty_message(self) -> None:
        msgs = [{"role": "user", "content": "hello world"}]
        result = _estimate_tokens_from_messages(msgs)
        assert result >= 1

    def test_empty_content(self) -> None:
        msgs = [{"role": "user", "content": ""}]
        result = _estimate_tokens_from_messages(msgs)
        assert result >= 1  # minimum 1

    def test_longer_content_gives_more_tokens(self) -> None:
        short = [{"role": "user", "content": "hi"}]
        long = [{"role": "user", "content": "hello world this is a longer message with more words"}]
        assert _estimate_tokens_from_messages(long) > _estimate_tokens_from_messages(short)

    def test_multiple_messages_summed(self) -> None:
        single = [{"role": "user", "content": "hello world"}]
        double = [
            {"role": "user", "content": "hello world"},
            {"role": "assistant", "content": "hello world"},
        ]
        assert _estimate_tokens_from_messages(double) > _estimate_tokens_from_messages(single)


class TestPricingTable:
    def test_loads_without_error(self) -> None:
        table = _load_pricing_table()
        assert isinstance(table, dict)
        assert len(table) > 0

    def test_ollama_model_is_free(self) -> None:
        table = _load_pricing_table()
        in_price, out_price = _lookup_model_price(table, "llama3.2:1b")
        assert in_price == 0.0
        assert out_price == 0.0

    def test_known_cloud_model_has_nonzero_price(self) -> None:
        table = _load_pricing_table()
        in_price, out_price = _lookup_model_price(table, "claude-sonnet-4-6")
        assert in_price > 0.0
        assert out_price > 0.0

    def test_unknown_model_returns_zeros(self) -> None:
        table = _load_pricing_table()
        in_price, out_price = _lookup_model_price(table, "nonexistent-model-xyz")
        assert in_price == 0.0
        assert out_price == 0.0

    def test_cost_computation(self) -> None:
        # 1000 input tokens + 500 output tokens at $3/$15 per 1M
        in_price = 3.0
        out_price = 15.0
        usd = (1000 * in_price + 500 * out_price) / 1_000_000
        assert usd == pytest.approx(0.003 + 0.0075)

    def test_local_model_cost_is_zero(self) -> None:
        in_price = 0.0
        out_price = 0.0
        usd = (10000 * in_price + 5000 * out_price) / 1_000_000
        assert usd == 0.0


class TestExtractJsonBlock:
    def test_plain_json_unchanged(self) -> None:
        raw = '{"key": "value"}'
        assert _extract_json_block(raw) == '{"key": "value"}'

    def test_strips_markdown_fence(self) -> None:
        raw = '```json\n{"key": "value"}\n```'
        result = _extract_json_block(raw)
        assert json.loads(result) == {"key": "value"}

    def test_strips_bare_fence(self) -> None:
        raw = '```\n{"key": "value"}\n```'
        result = _extract_json_block(raw)
        assert json.loads(result) == {"key": "value"}

    def test_extracts_json_from_prose(self) -> None:
        raw = 'Here is my evaluation:\n{"score": 4, "note": "good"}\nThat is all.'
        result = _extract_json_block(raw)
        assert json.loads(result) == {"score": 4, "note": "good"}

    def test_nested_braces(self) -> None:
        raw = '{"outer": {"inner": 1}}'
        result = _extract_json_block(raw)
        assert json.loads(result) == {"outer": {"inner": 1}}

    def test_no_json_returns_raw(self) -> None:
        raw = "No JSON here at all."
        result = _extract_json_block(raw)
        assert result == raw.strip()


def _make_mock_llm(response_text: str, input_tok: int = 50, output_tok: int = 30) -> AsyncMock:
    """Return an AsyncMock LLM that returns fixed JSON text and token counts."""
    mock = AsyncMock()
    mock.complete.return_value = {
        "content": [{"type": "text", "text": response_text}],
        "usage": {"input_tokens": input_tok, "output_tokens": output_tok},
    }
    return mock


class TestJudgeSynthesisRubric:
    """Tests for _judge_synthesis_rubric — assert scoring logic with mocked LLM."""

    def test_parses_valid_json_response(self) -> None:
        verdict_json = json.dumps(
            {
                "factual_accuracy": 4,
                "source_coverage": 3,
                "actionability": 5,
                "safety_adherence": 4,
                "overall_score": 4.0,
                "explanation": "Good answer",
            }
        )
        llm = _make_mock_llm(verdict_json)
        scenario = {
            "situation": "Motor running hot",
            "sources": [{"source_type": "telemetry", "asset_id": "motor_01"}],
            "question": "What should I do?",
            "key_synthesis_points": ["Check temperature trend"],
        }
        result = asyncio.run(_judge_synthesis_rubric(llm, None, scenario, "Shut down the motor."))
        assert result["factual_accuracy"] == 4
        assert result["source_coverage"] == 3
        assert result["overall_score"] == pytest.approx(4.0)
        assert "judge_error" not in result

    def test_handles_fenced_json(self) -> None:
        inner = json.dumps(
            {
                "factual_accuracy": 5,
                "source_coverage": 5,
                "actionability": 5,
                "safety_adherence": 5,
                "overall_score": 5.0,
                "explanation": "Perfect",
            }
        )
        verdict_json = f"```json\n{inner}\n```"
        llm = _make_mock_llm(verdict_json)
        scenario = {"situation": "s", "sources": [], "question": "q", "key_synthesis_points": []}
        result = asyncio.run(_judge_synthesis_rubric(llm, None, scenario, "answer"))
        assert result["factual_accuracy"] == 5
        assert "judge_error" not in result

    def test_sets_missing_dimensions_to_one(self) -> None:
        verdict_json = json.dumps({"factual_accuracy": 3, "explanation": "partial"})
        llm = _make_mock_llm(verdict_json)
        scenario = {"situation": "s", "sources": [], "question": "q", "key_synthesis_points": []}
        result = asyncio.run(_judge_synthesis_rubric(llm, None, scenario, "answer"))
        assert result["source_coverage"] == 1
        assert result["actionability"] == 1
        assert result["safety_adherence"] == 1

    def test_judge_error_on_unparseable_response(self) -> None:
        llm = _make_mock_llm("This is not JSON at all, just prose with no braces.")
        scenario = {"situation": "s", "sources": [], "question": "q", "key_synthesis_points": []}
        result = asyncio.run(_judge_synthesis_rubric(llm, None, scenario, "answer"))
        assert result.get("judge_error") is True

    def test_passes_judge_model_to_llm(self) -> None:
        verdict_json = json.dumps(
            {"factual_accuracy": 4, "source_coverage": 4, "actionability": 4, "safety_adherence": 4}
        )
        llm = _make_mock_llm(verdict_json)
        scenario = {"situation": "s", "sources": [], "question": "q", "key_synthesis_points": []}
        asyncio.run(_judge_synthesis_rubric(llm, "llama3.1:70b", scenario, "answer"))
        llm.complete.assert_called_once()
        _, kwargs = llm.complete.call_args
        assert kwargs["model"] == "llama3.1:70b"


class TestJudgeHallucination:
    """Tests for _judge_hallucination — assert parsing and error handling with mocked LLM."""

    def test_parses_valid_json_response(self) -> None:
        verdict_json = json.dumps(
            {
                "recall": 0.8,
                "has_hallucination": False,
                "hallucinations_detected": [],
                "explanation": "Mostly correct",
            }
        )
        llm = _make_mock_llm(verdict_json)
        result = asyncio.run(_judge_hallucination(llm, None, "question", "answer", ["fact1"], []))
        assert result["recall"] == pytest.approx(0.8)
        assert result["has_hallucination"] is False
        assert "judge_error" not in result

    def test_handles_fenced_json(self) -> None:
        inner = json.dumps(
            {
                "recall": 1.0,
                "has_hallucination": False,
                "hallucinations_detected": [],
                "explanation": "ok",
            }
        )
        verdict_json = f"```json\n{inner}\n```"
        llm = _make_mock_llm(verdict_json)
        result = asyncio.run(_judge_hallucination(llm, None, "question", "answer", [], []))
        assert result["recall"] == pytest.approx(1.0)
        assert "judge_error" not in result

    def test_judge_error_on_unparseable_response(self) -> None:
        llm = _make_mock_llm("Sorry, I cannot evaluate this.")
        result = asyncio.run(_judge_hallucination(llm, None, "question", "answer", [], []))
        assert result.get("judge_error") is True
        assert result["recall"] == pytest.approx(0.0)

    def test_sets_default_keys_on_missing_fields(self) -> None:
        verdict_json = json.dumps({"recall": 0.5})
        llm = _make_mock_llm(verdict_json)
        result = asyncio.run(_judge_hallucination(llm, None, "question", "answer", [], []))
        assert "has_hallucination" in result
        assert "hallucinations_detected" in result
        assert "explanation" in result

    def test_passes_judge_model_to_llm(self) -> None:
        verdict_json = json.dumps(
            {
                "recall": 1.0,
                "has_hallucination": False,
                "hallucinations_detected": [],
                "explanation": "",
            }
        )
        llm = _make_mock_llm(verdict_json)
        asyncio.run(_judge_hallucination(llm, "claude-sonnet-4-6", "question", "answer", [], []))
        llm.complete.assert_called_once()
        _, kwargs = llm.complete.call_args
        assert kwargs["model"] == "claude-sonnet-4-6"
