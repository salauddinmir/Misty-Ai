"""
Regression tests for NLU parser fixes.

Ensures Bengali interrogative words are never captured as names and
that question inputs are not misclassified as name declarations.
"""
import pytest

from brain.nlu.parser import NLUParser, IntentType


@pytest.fixture
def parser():
    return NLUParser()


class TestBengaliInterrogativeGuard:
    """Regression tests: "আমার নাম কি?" must NOT become a name declaration."""

    def test_ami_nam_ki_not_name_declaration(self, parser):
        result = parser.parse("আমার নাম কি?")
        assert result.intent != IntentType.NAME_DECLARATION
        assert result.entities.get("name") != "কি"

    def test_ami_nam_ki_with_bengali_full_stop(self, parser):
        result = parser.parse("আমার নাম কি\u0964")
        assert result.intent != IntentType.NAME_DECLARATION

    def test_ami_nam_comma_question(self, parser):
        # Interrogative word variants must all be blocked
        for word in ["কি", "কী", "কোন", "কেমন"]:
            result = parser.parse(f"আমার নাম {word}?")
            assert result.intent != IntentType.NAME_DECLARATION, word

    def test_valid_name_declaration_still_works(self, parser):
        result = parser.parse("আমার নাম Salauddin")
        assert result.intent == IntentType.NAME_DECLARATION
        assert result.entities.get("name") == "Salauddin"

    def test_bengali_name_declaration_still_works(self, parser):
        result = parser.parse("আমার নাম রহিম")
        assert result.intent == IntentType.NAME_DECLARATION
        assert result.entities.get("name") == "রহিম"

    def test_query_with_question_mark_not_name(self, parser):
        result = parser.parse("ভালো আছো?")
        assert result.intent != IntentType.NAME_DECLARATION


class TestNameCaptureDoesNotEatInterrogatives:
    def test_english_my_name_is_what(self, parser):
        result = parser.parse("my name is what?")
        assert result.intent != IntentType.NAME_DECLARATION or \
            result.entities.get("name") != "what"
