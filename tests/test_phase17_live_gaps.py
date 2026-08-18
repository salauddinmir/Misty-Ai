"""Tests for real-world gaps found during user testing (Phase 17).

These reproduce the exact queries the user sent from the deployed apps:
1. "x² - 4 = 0, x =" should solve (previously: "could not safely solve").
2. "কি খবর" / "ভালো ব্যাপার" / "তুমি কি ভাবছো?" should get a friendly
   conversational reply instead of a generic echo.
3. ``15 \u00d7 7`` in Bengali digits must return 105 (regression guard —
   verified working in the current build but kept as a test).
"""

from brain.core.brain import Brain
from brain.nlu.parser import IntentType, NLUParser

_Parser = NLUParser()


class TestQuadraticSolver:
    def test_solve_x_squared_minus_four(self):
        from brain.math_engine import MATH_ENGINE

        result = MATH_ENGINE.solve("x² - 4 = 0")
        assert result is not None
        assert result.category == "quadratic_equation"
        assert "2" in result.answer and "-2" in result.answer

    def test_solve_perfect_square(self):
        from brain.math_engine import MATH_ENGINE

        result = MATH_ENGINE.solve("x² + 4x + 4 = 0")
        assert result is not None
        assert "-2" in result.answer

    def test_no_real_solution(self):
        from brain.math_engine import MATH_ENGINE

        result = MATH_ENGINE.solve("x² + 1 = 0")
        assert result is not None
        assert "বাস্তব সমাধান" in result.answer or "no_real" in result.exact

    def test_nontrivial_roots(self):
        from brain.math_engine import MATH_ENGINE

        result = MATH_ENGINE.solve("x² - 5x + 6 = 0")
        assert result is not None
        assert "2" in result.answer and "3" in result.answer

    def test_caret_notation(self):
        from brain.math_engine import MATH_ENGINE

        result = MATH_ENGINE.solve("x^2 + 2x + 1 = 0")
        assert result is not None
        assert "-1" in result.answer

    def test_quadratic_via_brain_process(self):
        brain = Brain()
        outcome = brain.process("x² - 4 = 0, x = ?")
        answer = outcome.get("response", "")
        assert "2" in answer
        assert "-2" in answer


class TestCasualConversationIntents:
    def test_bn_ki_khobor(self):
        result = _Parser.parse("কি খবর")
        assert result is not None
        assert result.intent == IntentType.CONVERSATION

    def test_bn_valo_byapar(self):
        result = _Parser.parse("ভালো ব্যাপার")
        assert result is not None
        assert result.intent == IntentType.CONVERSATION

    def test_bn_ki_bhabcho(self):
        result = _Parser.parse("তুমি কি ভাবছো?")
        assert result is not None
        assert result.intent == IntentType.CONVERSATION

    def test_en_how_are_you(self):
        result = _Parser.parse("how are you?")
        assert result is not None
        assert result.intent == IntentType.CONVERSATION

    def test_en_thats_good(self):
        result = _Parser.parse("that's good")
        assert result is not None
        assert result.intent == IntentType.CONVERSATION

    def test_brain_friendly_reply_ki_khobor(self):
        brain = Brain()
        outcome = brain.process("কি খবর")
        response = outcome.get("response", "")
        assert "আমি" in response and "ধন্যবাদ" in response

    def test_brain_friendly_reply_valo_byapar(self):
        brain = Brain()
        outcome = brain.process("ভালো ব্যাপার")
        response = outcome.get("response", "")
        assert "ধন্যবাদ" in response

    def test_brain_friendly_reply_thinking_query(self):
        brain = Brain()
        outcome = brain.process("তুমি কি ভাবছো?")
        response = outcome.get("response", "")
        assert "পর্যবেক্ষণ" in response or "ভাব" in response

    def test_brain_english_casual_reply(self):
        brain = Brain()
        outcome = brain.process("how are you?")
        response = outcome.get("response", "")
        assert "well" in response.lower() or "আমি" in response


class TestBengaliArithmeticRegression:
    def test_fifteen_times_seven(self):
        brain = Brain()
        outcome = brain.process("১৫ × ৭ কত?")  # noqa: RUF001  # BN digits intentional
        assert "105" in outcome.get("response", "")
