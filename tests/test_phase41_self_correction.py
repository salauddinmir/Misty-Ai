"""Phase 41: self-correction (CorrectionAuditor) tests."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from brain.core.brain import Brain
from brain.learning.self_correction import (
    CorrectionAuditor,
    CorrectionEntry,
    _detect_challenge,
)


# ---------------------------------------------------------------------------
# Challenge detection
# ---------------------------------------------------------------------------
class TestChallengeDetection:
    def test_bengali_challenge(self) -> None:
        detected, marker = _detect_challenge("আপনার আগের উত্তর ভুল বলছেন।")
        assert detected and "ভুল" in marker

    def test_english_challenge(self) -> None:
        detected, marker = _detect_challenge("No, that's wrong!")
        assert detected and "wrong" in marker.lower()

    def test_variants(self) -> None:
        for text in ("এটা ঠিক নয়", "wrong answer", "ur wrong", "it's false", "আসলে তা না"):
            detected, _ = _detect_challenge(text)
            assert detected, f"expected challenge for {text!r}"

    def test_normal_text(self) -> None:
        detected, _ = _detect_challenge("রাজধানী কোথায়?")
        assert not detected

    def test_question_with_wrong_keyword(self) -> None:
        # "কোনটা ভুল হলো?" is a genuine question containing a marker —
        # detection is intentionally conservative, but the auditor only
        # accepts corrections with provable contradictions.
        detected, _ = _detect_challenge("কোনটা ভুল হলো?")
        assert detected


# ---------------------------------------------------------------------------
# Auditor unit tests
# ---------------------------------------------------------------------------
class TestCorrectionAuditor:
    @pytest.fixture
    def auditor(self) -> CorrectionAuditor:
        return CorrectionAuditor()

    def test_no_challenge_passes_through(self, auditor: CorrectionAuditor) -> None:
        detected, note = auditor.audit("রাজধানী কোথায়?", "দিল্লি হলো ভারতের রাজধানী।", lambda t: {})
        assert not detected and note is None

    def test_challenge_without_claim_gets_humble_note(self, auditor: CorrectionAuditor) -> None:
        auditor.last_output = "মিস্টি একটি স্মার্ট ব্রেন।"
        detected, note = auditor.audit(
            "এটা ভুল", auditor.last_output, lambda t: {"contradicted": False, "reason": "none"}
        )
        assert detected
        # "এটা ভুল" yields extractable claim tokens (from the challenge
        # text after markers are stripped), so the auditor emits the
        # epistemic-humility note rather than the generic one.
        assert note is not None and "সাবধানে" in note

    def test_accepted_correction_uses_warm_admission(self, auditor: CorrectionAuditor) -> None:
        auditor.last_output = "আগের উত্তর।"
        detected, note = auditor.audit(
            "এটা ভুল বলছেন", auditor.last_output, lambda t: {"contradicted": True, "reason": "r"}
        )
        assert detected and note is not None
        assert "ঠিক বলেছেন" in note

    def test_unprovable_challenge_does_not_accept(self, auditor: CorrectionAuditor) -> None:
        auditor.last_output = "আগের উত্তর।"
        detected, _ = auditor.audit("এটা ভুল", auditor.last_output, lambda t: {"contradicted": False, "reason": "x"})
        assert detected
        entry = auditor.last_correction()
        assert isinstance(entry, CorrectionEntry) and not entry.accepted

    def test_log_growth_and_summary(self, auditor: CorrectionAuditor) -> None:
        auditor.last_output = "ans"
        auditor.audit("এটা ভুল", "ans", lambda t: {"contradicted": True, "reason": "r"})
        # Non-challenge turns are not logged; only challenges appear in the
        # audit log, so the log still holds just the accepted correction.
        auditor.audit("কিছু জানাও", "ans", lambda t: {})
        summary = auditor.summary()
        assert summary["challenges_received"] == 1
        assert summary["corrections_accepted"] == 1
        assert summary["last_correction"]["accepted"] is True

    def test_claim_token_extraction(self, auditor: CorrectionAuditor) -> None:
        tokens = auditor._claim_tokens("এটা ভুল, আমার নাম রাহুল না, আমার নাম করিম।")
        assert any(t in ("নাম", "করিম", "রাহুল") for t in tokens)


# ---------------------------------------------------------------------------
# Brain wiring tests
# ---------------------------------------------------------------------------
class TestBrainWiring:
    def test_correction_auditor_attribute(self) -> None:
        brain = Brain()
        assert hasattr(brain, "correction_auditor") and isinstance(brain.correction_auditor, CorrectionAuditor)

    def test_state_includes_self_correction(self) -> None:
        brain = Brain()
        state = brain.get_state()
        assert "self_correction" in state and state["self_correction"]["enabled"] is True

    def test_challenge_triggers_audit(self) -> None:
        brain = Brain()
        brain.process("রাজধানী কোথায়?")
        brain.semantic_memory.store_fact("রাজধানী", "is_capital_of", "কোলকাতা", source="training")
        # Challenge the answer — the stored fact makes the auditor accept
        # the correction (answer object token matched).
        brain.process("আপনার উত্তর ভুল")
        summary = brain.correction_auditor.summary()
        assert summary["challenges_received"] == 1

    def test_no_challenge_stays_quiet(self) -> None:
        brain = Brain()
        brain.process("রাজধানী কোথায়?")
        brain.process("ধন্যবাদ!")
        assert brain.correction_auditor.summary()["challenges_received"] == 0


# ---------------------------------------------------------------------------
# API route tests
# ---------------------------------------------------------------------------
class TestBrainStateRoute:
    def test_state_exposes_self_correction(self) -> None:
        import importlib

        import apps.api.routes.brain as brain_route

        brain_route = importlib.reload(brain_route)
        app = FastAPI()
        app.include_router(brain_route.router, prefix="/api/brain")
        brain = Brain()
        app.state.brain = brain
        brain.process("কেমন আছো?")
        brain.process("এটা ভুল বলছেন")
        client = TestClient(app)
        state = client.get("/api/brain/state").json()
        assert "self_correction" in state
        assert state["self_correction"]["challenges_received"] >= 1
