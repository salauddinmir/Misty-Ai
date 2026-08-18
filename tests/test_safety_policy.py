from brain.safety.policy import (
    AutonomyPolicy,
    Decision,
    evaluate_action,
    evaluate_learning,
)


def test_learning_without_provenance_is_rejected():
    result = evaluate_learning({"confidence": 1.0, "observations": 4})
    assert result.decision is Decision.REJECT
    assert result.audit_code == "LEARN_NO_PROVENANCE"


def test_low_evidence_is_quarantined():
    result = evaluate_learning({"source_ref": "memory:1", "confidence": 0.7, "observations": 1})
    assert result.decision is Decision.QUARANTINE
    assert result.audit_code == "LEARN_INSUFFICIENT_EVIDENCE"


def test_contradictory_learning_is_quarantined_even_with_high_confidence():
    result = evaluate_learning(
        {"source_ref": "memory:2", "confidence": 0.99, "observations": 8, "contradicts_existing": True}
    )
    assert result.decision is Decision.QUARANTINE
    assert result.audit_code == "LEARN_CONTRADICTION"


def test_external_side_effect_is_disabled_by_default():
    result = evaluate_action({"type": "external_side_effect"})
    assert result.decision is Decision.REJECT


def test_internal_action_is_allowed_but_identity_change_requires_review_when_enabled():
    assert evaluate_action({"type": "memory_review"}).decision is Decision.ALLOW
    result = evaluate_action({"type": "identity_mutation"}, policy=AutonomyPolicy(allow_identity_mutation=True))
    assert result.decision is Decision.REQUIRE_APPROVAL
    assert result.requires_human
