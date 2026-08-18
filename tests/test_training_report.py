from brain.evaluation.training_report import build_training_report


def test_training_report_aggregates_department_metrics():
    report = build_training_report(
        [
            {"department": "mathematics", "passed": True, "confidence": 0.9, "latency_ms": 4.0},
            {"department": "mathematics", "passed": True, "confidence": 0.8, "latency_ms": 6.0},
            {"department": "language", "passed": False, "confidence": 0.4, "latency_ms": 8.0},
        ]
    )
    assert report["schema_version"] == "training-report.v1"
    assert report["total_cases"] == 3
    assert report["passed_cases"] == 2
    math = next(item for item in report["departments"] if item["department"] == "mathematics")
    assert math["pass_rate"] == 1.0
    assert math["max_latency_ms"] == 6.0
    assert math["accepted"]


def test_training_report_handles_empty_input():
    assert build_training_report([]) == {
        "schema_version": "training-report.v1",
        "total_cases": 0,
        "passed_cases": 0,
        "overall_pass_rate": 0.0,
        "departments": [],
    }
