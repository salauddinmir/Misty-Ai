"""Deterministic Bengali/English benchmark runner for MISTY.

The benchmark deliberately scores observable behavior only: expected answer
fragments, confidence, grounding claims, and latency. It does not inspect or
invent hidden chain-of-thought.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from time import perf_counter
from typing import Any, Iterable


@dataclass(frozen=True)
class BenchmarkCase:
    """One bilingual observable behavior case."""

    case_id: str
    language: str
    prompt: str
    expected_fragments: tuple[str, ...]
    minimum_confidence: float = 0.0
    required_claims: tuple[str, ...] = ()


@dataclass(frozen=True)
class BenchmarkResult:
    case_id: str
    language: str
    passed: bool
    response: str
    confidence: float
    latency_ms: float
    missing_fragments: tuple[str, ...] = ()
    missing_claims: tuple[str, ...] = ()


@dataclass
class BilingualBenchmark:
    """Run deterministic acceptance cases against a Brain-like object."""

    cases: list[BenchmarkCase] = field(default_factory=list)

    def run(self, brain: Any, cases: Iterable[BenchmarkCase] | None = None) -> list[BenchmarkResult]:
        selected = list(cases if cases is not None else self.cases)
        results: list[BenchmarkResult] = []
        for case in selected:
            started = perf_counter()
            output = brain.process(case.prompt)
            latency_ms = round((perf_counter() - started) * 1000, 3)
            response = str(output.get("response", ""))
            folded_response = response.casefold()
            missing_fragments = tuple(
                fragment for fragment in case.expected_fragments if fragment.casefold() not in folded_response
            )
            grounding = output.get("grounding") or {}
            claims = set(grounding.get("claims", []))
            missing_claims = tuple(claim for claim in case.required_claims if claim not in claims)
            confidence = float(output.get("confidence", 0.0))
            passed = not missing_fragments and not missing_claims and confidence >= case.minimum_confidence
            results.append(
                BenchmarkResult(
                    case_id=case.case_id,
                    language=case.language,
                    passed=passed,
                    response=response,
                    confidence=confidence,
                    latency_ms=latency_ms,
                    missing_fragments=missing_fragments,
                    missing_claims=missing_claims,
                )
            )
        return results

    @staticmethod
    def summary(results: Iterable[BenchmarkResult]) -> dict[str, Any]:
        records = list(results)
        passed = sum(1 for result in records if result.passed)
        by_language: dict[str, dict[str, int]] = {}
        for result in records:
            stats = by_language.setdefault(result.language, {"passed": 0, "total": 0})
            stats["total"] += 1
            stats["passed"] += int(result.passed)
        return {
            "passed": passed,
            "total": len(records),
            "pass_rate": round(passed / len(records), 4) if records else 0.0,
            "by_language": by_language,
            "max_latency_ms": max((result.latency_ms for result in records), default=0.0),
        }


def default_bilingual_cases() -> list[BenchmarkCase]:
    """Core identity and deterministic-engine acceptance cases."""
    return [
        BenchmarkCase(
            case_id="identity-bn",
            language="bn",
            prompt="মিস্টি কে?",
            expected_fragments=("Misty", "Pixline Incorporate"),
            minimum_confidence=0.8,
            required_claims=("workspace_evidence",),
        ),
        BenchmarkCase(
            case_id="identity-en",
            language="en",
            prompt="Who are you?",
            expected_fragments=("Misty",),
            minimum_confidence=0.8,
        ),
        BenchmarkCase(
            case_id="math-en",
            language="en",
            prompt="What is 2 + 2?",
            expected_fragments=("4",),
            minimum_confidence=0.5,
            required_claims=("deterministic_math_engine",),
        ),
        BenchmarkCase(
            case_id="physics-en",
            language="en",
            prompt="What is velocity?",
            expected_fragments=("velocity",),
            minimum_confidence=0.3,
        ),
    ]
