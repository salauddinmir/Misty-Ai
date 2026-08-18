"""Training and benchmark report helpers for department-wise evaluation."""

from __future__ import annotations

from typing import Any, Iterable, Mapping

from brain.knowledge.cognitive_curriculum import list_cognitive_curricula
from brain.knowledge.curriculum import list_curricula


def _department_threshold(department: str) -> float:
    manifests = list_curricula() + list_cognitive_curricula()
    for manifest in manifests:
        if manifest.department == department:
            values = [value for key, value in manifest.acceptance.items() if not key.endswith("_max")]
            return min(values) if values else 1.0
    return 1.0


def build_training_report(results: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    """Aggregate observable benchmark results without exposing hidden reasoning."""
    records = list(results)
    by_department: dict[str, dict[str, Any]] = {}
    for record in records:
        department = str(record.get("department", "general"))
        bucket = by_department.setdefault(
            department,
            {"department": department, "passed": 0, "total": 0, "latencies_ms": [], "confidence_sum": 0.0},
        )
        bucket["total"] += 1
        bucket["passed"] += int(bool(record.get("passed", False)))
        bucket["latencies_ms"].append(float(record.get("latency_ms", 0.0)))
        bucket["confidence_sum"] += float(record.get("confidence", 0.0))

    departments = []
    for department, bucket in sorted(by_department.items()):
        total = bucket["total"]
        pass_rate = bucket["passed"] / total if total else 0.0
        departments.append(
            {
                "department": department,
                "passed": bucket["passed"],
                "total": total,
                "pass_rate": round(pass_rate, 4),
                "mean_confidence": round(bucket["confidence_sum"] / total, 4) if total else 0.0,
                "max_latency_ms": round(max(bucket["latencies_ms"], default=0.0), 3),
                "acceptance_threshold": _department_threshold(department),
                "accepted": pass_rate >= _department_threshold(department),
            }
        )

    total = len(records)
    passed = sum(int(bool(record.get("passed", False))) for record in records)
    return {
        "schema_version": "training-report.v1",
        "total_cases": total,
        "passed_cases": passed,
        "overall_pass_rate": round(passed / total, 4) if total else 0.0,
        "departments": departments,
    }
