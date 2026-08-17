"""Regression tests for MISTY's deterministic mathematics capability."""

from brain.math_engine import MATH_ENGINE
from brain.nlu.parser import IntentType, NLUParser


class TestMathEngine:
    def test_arithmetic(self):
        result = MATH_ENGINE.solve("calculate 2 + 3 * 4")
        assert result is not None
        assert result.answer == "14"

    def test_percentage_and_bengali_digits(self):
        result = MATH_ENGINE.solve("২৫ শতাংশ of ২০০")
        assert result is not None
        assert result.exact == "50"

    def test_linear_equation(self):
        result = MATH_ENGINE.solve("solve 2x + 4 = 10")
        assert result is not None
        assert result.exact == "x = 3"

    def test_bengali_square_root(self):
        result = MATH_ENGINE.solve("বর্গমূল ৮১")
        assert result is not None
        assert result.exact == "9"

    def test_geometry_and_statistics(self):
        circle = MATH_ENGINE.solve("circle radius 3")
        stats = MATH_ENGINE.solve("mean 2, 4, 6")
        assert circle is not None and circle.category == "geometry"
        assert stats is not None and "mean = 4" in stats.answer

    def test_sequence_and_combinatorics(self):
        sequence = MATH_ENGINE.solve("sequence: 2, 4, 8 next 2")
        combination = MATH_ENGINE.solve("combination 5 2")
        assert sequence is not None and sequence.exact == "16, 32"
        assert combination is not None and combination.exact == "10"

    def test_unsafe_expression_is_rejected(self):
        result = MATH_ENGINE.solve("calculate __import__('os').system('echo bad')")
        assert result is None or result.category == "error"


class TestMathIntent:
    def test_english_math_is_classified(self):
        parsed = NLUParser().parse("what is 12 / 3?")
        assert parsed.intent == IntentType.MATH

    def test_bengali_math_is_classified(self):
        parsed = NLUParser().parse("হিসাব করো 7 + 5")
        assert parsed.intent == IntentType.MATH

    def test_identity_is_not_math(self):
        parsed = NLUParser().parse("তুমি কে?")
        assert parsed.intent == IntentType.QUERY_WHO
