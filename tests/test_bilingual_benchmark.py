"""Tests for deterministic bilingual acceptance benchmarking."""

from brain.core.brain import Brain
from brain.evaluation.bilingual import BenchmarkCase, BilingualBenchmark, default_bilingual_cases


def test_default_bilingual_cases_run_against_brain() -> None:
    results = BilingualBenchmark(default_bilingual_cases()).run(Brain())
    summary = BilingualBenchmark.summary(results)

    assert summary["total"] == 4
    assert summary["passed"] >= 3
    assert summary["by_language"]["bn"]["total"] == 1
    assert summary["by_language"]["en"]["total"] == 3
    assert all(result.latency_ms >= 0 for result in results)


def test_benchmark_reports_missing_fragments() -> None:
    benchmark = BilingualBenchmark()
    results = benchmark.run(
        Brain(),
        [
            BenchmarkCase(
                case_id="deliberate-failure",
                language="bn",
                prompt="মিস্টি কে?",
                expected_fragments=("definitely-not-present",),
            )
        ],
    )

    assert results[0].passed is False
    assert "definitely-not-present" in results[0].missing_fragments
    assert BilingualBenchmark.summary(results)["pass_rate"] == 0.0
