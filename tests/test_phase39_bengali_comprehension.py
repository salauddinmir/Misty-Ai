# ruff: noqa: RUF001  (Bengali digits and text are intentional)
"""Phase 39: regressions for the Bengali comprehension defects observed in production.

Every case below reproduces an exact user message from the deployed chat UI that
previously produced a wrong or misleading answer. The assertions pin the observed
behaviour: correct intent classification, grounded answers from stored knowledge,
and honest refusals instead of invented content.
"""

from brain.core.brain import Brain
from brain.nlu.parser import IntentType, NLUParser

CANNED_FAILURE_MARKERS = (
    "intent এখনো",
    "parse করতে পারিনি",
    "বুঝতে শিখিনি",
    "fact extract করতে পারিনি",
    "বিশ্লেষণ করতে পারছি না",
    "নির্দিষ্ট solver নেই",
)


def assert_not_canned(response: str) -> None:
    for marker in CANNED_FAILURE_MARKERS:
        assert marker not in response, f"canned failure {marker!r} in {response!r}"


class TestStatusQuestion:
    """ "কি করা হচ্ছে" is a status question, not an unparsable statement."""

    def test_intent_is_conversation(self) -> None:
        assert NLUParser().parse("কি করা হচ্ছে").intent is IntentType.CONVERSATION

    def test_answer_reports_runtime_state(self) -> None:
        response = Brain().process("কি করা হচ্ছে")["response"]
        assert_not_canned(response)
        assert "cycle" in response
        assert "fact" in response

    def test_formal_variant(self) -> None:
        assert NLUParser().parse("এখন কি করছেন?").intent is IntentType.CONVERSATION


class TestBareTeachCommand:
    """A teaching command with no payload must ask what to remember."""

    def test_intent_requests_clarification(self) -> None:
        parsed = NLUParser().parse("মনে রাখো")
        assert parsed.intent is IntentType.CONVERSATION
        assert parsed.entities["clarification_needed"] == "teach_payload_missing"

    def test_response_asks_for_content_and_stores_nothing(self) -> None:
        brain = Brain()
        before = brain.semantic_memory.size
        response = brain.process("মনে রাখো")["response"]
        assert "কী মনে রাখব" in response
        assert brain.semantic_memory.size == before

    def test_teaching_with_payload_still_works(self) -> None:
        parsed = NLUParser().parse("মনে রাখো: আকাশ নীল")
        assert parsed.intent is IntentType.TEACH
        assert parsed.entities["taught"] == "আকাশ নীল"


class TestBareTopicPhrase:
    """A bare topic phrase should surface stored knowledge about the topic."""

    def test_bangla_kobita_lists_known_works(self) -> None:
        response = Brain().process("বাংলা কবিতা")["response"]
        assert_not_canned(response)
        assert any(name in response for name in ("বিদ্রোহী", "বনলতা সেন", "রূপসী বাংলা"))

    def test_ordinary_statement_is_not_treated_as_topic(self) -> None:
        brain = Brain()
        result = brain.process("আমি আজ বাজারে গিয়েছিলাম এবং অনেক কিছু কিনেছি")
        assert result["intent"] in {"statement", "conversation", "unknown"}


class TestListRequest:
    """ "... নাম বলো" is a list request and must never be answered by physics."""

    def test_intent_and_count_extraction(self) -> None:
        parsed = NLUParser().parse("ভারতের ৭ টি আশ্চর্যের নাম বলো")
        assert parsed.intent is IntentType.LIST_QUERY
        assert parsed.query["count"] == 7
        assert "আশ্চর্য" in parsed.query["target"]

    def test_spelled_count_and_possessive(self) -> None:
        parsed = NLUParser().parse("তিনটি ফুলের নাম বলো")
        assert parsed.intent is IntentType.LIST_QUERY
        assert parsed.query["count"] == 3
        assert parsed.query["target"] == "ফুল"

    def test_unknown_list_is_refused_without_invention(self) -> None:
        response = Brain().process("ভারতের ৭ টি আশ্চর্যের নাম বলো")["response"]
        assert_not_canned(response)
        assert "বানিয়ে বলব না" in response or "আমার জ্ঞানভাণ্ডারে নেই" in response

    def test_known_list_is_enumerated_from_memory(self) -> None:
        brain = Brain()
        brain.semantic_memory.store_fact(
            subject="পরীক্ষা তালিকা",
            predicate="includes",
            obj="প্রথম, দ্বিতীয়, তৃতীয়",
            confidence=0.9,
            source="unit_test",
        )
        response = brain.process("পরীক্ষা তালিকার নাম বলো")["response"]
        assert "প্রথম" in response and "তৃতীয়" in response

    def test_personal_name_request_is_not_a_list(self) -> None:
        assert NLUParser().parse("আমার নাম বলো").intent is IntentType.RECOGNITION_QUERY

    def test_self_name_request_returns_identity(self) -> None:
        response = Brain().process("তোমার নাম বলো")["response"]
        assert "Misty" in response


class TestPhysicsRoutingAndTransliteration:
    """Physics must win only when a solver applies, and Bengali spellings must resolve."""

    def test_list_request_is_not_physics(self) -> None:
        assert NLUParser().parse("ভারতের ৭ টি আশ্চর্যের নাম বলো").intent is not IntentType.PHYSICS

    def test_real_physics_problem_still_routes_to_solver(self) -> None:
        parsed = NLUParser().parse("একটি বস্তুর ভর 2 kg এবং বেগ 3 m/s, গতিশক্তি কত?")
        assert parsed.intent is IntentType.PHYSICS

    def test_bengali_transliteration_resolves_definition(self) -> None:
        result = Brain().process("কিনেটিক এনার্জি কি?")
        response = result["response"]
        assert_not_canned(response)
        assert "গতি" in response
        assert "mv^2" in response or "1/2" in response
        assert result["grounding"]["grounding_source"] == "reason_derived_evidence"

    def test_transliteration_alias_is_registered(self) -> None:
        brain = Brain()
        assert brain.semantic_memory.query(subject="কিনেটিক এনার্জি")


class TestNaturalTeachingSyntax:
    """Punctuation between the copula and object must not discard the fact."""

    def test_dash_separated_assertion_extracts_fact(self) -> None:
        parsed = NLUParser().parse("কিনেটিক হলো - এনার্জির নাম")
        assert parsed.entities.get("subject") == "কিনেটিক"
        assert parsed.entities.get("is_a") == "এনার্জির নাম"

    def test_taught_fact_is_stored_and_recalled(self) -> None:
        brain = Brain()
        brain.process("কিনেটিক হলো - এনার্জির নাম")
        assert brain.semantic_memory.query(subject="কিনেটিক", predicate="is_a")
        response = brain.process("কিনেটিক কি?")["response"]
        assert "এনার্জির নাম" in response

    def test_curriculum_answer_survives_user_teaching(self) -> None:
        brain = Brain()
        brain.process("কিনেটিক হলো - এনার্জির নাম")
        response = brain.process("কিনেটিক এনার্জি কি?")["response"]
        assert "গতি" in response
