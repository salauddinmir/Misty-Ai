"""Tests for the Phase 3 extended NLU intents and relation grammar."""

from brain.nlu.parser import IntentType, NLUParser


def _parse(text: str):
    parser = NLUParser()
    return parser.parse(text)


class TestNewIntentTypes:
    def test_teach_intent(self) -> None:
        result = _parse("মনে রাখো প্যারিস ফ্রান্সের রাজধানী")
        assert result.intent == IntentType.TEACH
        # TEACH always captures the taught content in entities
        assert result.entities.get("taught")

    def test_teach_english(self) -> None:
        result = _parse("remember that the sun is a star")
        assert result.intent == IntentType.TEACH

    def test_correction_intent(self) -> None:
        result = _parse("না, ভুল বলছো")
        assert result.intent == IntentType.CORRECTION

    def test_correction_asol(self) -> None:
        result = _parse("আসলে মিস্তি একজন AI")
        assert result.intent == IntentType.CORRECTION

    def test_correction_not_definition_query(self) -> None:
        # "এর মানে" definition queries must not look like corrections
        result = _parse("এর মানে কী?")
        assert result.intent != IntentType.CORRECTION

    def test_continuation_bn(self) -> None:
        result = _parse("আরো বলো")
        assert result.intent == IntentType.CONTINUATION

    def test_continuation_en(self) -> None:
        result = _parse("more")
        assert result.intent == IntentType.CONTINUATION

    def test_pronoun_what_query(self) -> None:
        result = _parse("সে কী?")
        assert result.intent in (IntentType.QUERY_WHO, IntentType.QUERY_WHAT)

    def test_interrogative_guard_name_question(self) -> None:
        result = _parse("আমার নাম কি?")
        assert result.intent != IntentType.NAME_DECLARATION


class TestFacts:
    def test_bn_holo_facts(self) -> None:
        result = _parse("সূর্য হলো তারা")
        assert result.intent == IntentType.STATEMENT or result.facts
        if result.facts:
            assert result.facts[0]["subject"] == "সূর্য"

    def test_en_is_facts(self) -> None:
        result = _parse("python is a programming language")
        assert result.facts
        assert result.facts[0]["subject"] == "python"


class TestRelationGrammar:
    def test_bn_relation_three_groups(self) -> None:
        result = _parse("আমি রহিমের ক্রিযেটর মিস্তি")
        assert result.intent == IntentType.RELATION_DECLARATION
        rel = result.relations[0]
        assert rel["source"] == "রহিম"
        assert rel["target"] == "মিস্তি"

    def test_bn_relation_with_hyphen(self) -> None:
        result = _parse("আমি রহিম-এর ক্রিযেটর মিস্তি")
        assert result.intent == IntentType.RELATION_DECLARATION
        assert result.relations[0]["source"] == "রহিম"
        assert result.relations[0]["target"] == "মিস্তি"

    def test_bn_relation_two_groups(self) -> None:
        result = _parse("আমি মিস্তির মালিক")
        assert result.intent == IntentType.RELATION_DECLARATION
        assert result.relations[0]["source"] == "__self__"
        assert result.relations[0]["target"] == "মিস্তি"


class TestBrainTurnRecording:
    """Multi-turn dialogue must keep context without blowing up."""

    def test_multi_turn_roundtrip(self) -> None:
        from brain.core.brain import Brain

        brain = Brain(use_neural_sim=False)
        answers = []
        for text in [
            "আমার নাম রহিম",
            "আরে বলো",
            "সে কী?",
            "আসলে রহিম একজন শিক্ষক",
        ]:
            result = brain.process(text)
            answers.append(result["response"])
        assert all(answers)
