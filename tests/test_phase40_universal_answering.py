"""Phase 40: universal answering, cross-lingual retrieval, and self-directed study.

These tests pin the behaviour that lets the brain answer on its own:

* one canonical form per term, so spelling and inflection stop blocking recall,
* Bengali and English names reaching the same stored knowledge,
* a resolver that answers relation questions instead of returning a definition,
* honest refusal plus a recorded knowledge gap when nothing is known,
* self-directed study that closes those gaps and stays disabled by default.
"""

import asyncio

from brain.core.brain import Brain
from brain.knowledge.normalize import canonicalize, linked_names, matches, variants
from brain.knowledge.resolver import UNIVERSAL_RESOLVER
from brain.learning.self_directed import SelfDirectedLearner

CANNED_FAILURE_MARKERS = (
    "জানি না",
    "শেখা হয়নি",
    "do not know",
    "have not learned",
    "could not resolve",
)


def assert_answered(response: str) -> None:
    for marker in CANNED_FAILURE_MARKERS:
        assert marker not in response, f"unanswered ({marker!r}): {response!r}"


class TestNormalization:
    def test_bengali_inflection_folds_to_stem(self) -> None:
        assert canonicalize("আকাশের") == canonicalize("আকাশ")

    def test_english_plural_and_case_fold(self) -> None:
        assert canonicalize("Robots") == canonicalize("robot")

    def test_khanda_ta_variant_folds(self) -> None:
        assert canonicalize("সৌরজগৎ") == canonicalize("সৌরজগত")

    def test_filler_words_removed(self) -> None:
        assert canonicalize("the color of the sky") == "color sky"

    def test_bilingual_names_are_linked(self) -> None:
        assert "আকাশ" in linked_names("sky")
        assert "sky" in linked_names("আকাশ")

    def test_transliteration_links_to_canonical_term(self) -> None:
        assert "গতিশক্তি" in linked_names("কিনেটিক এনার্জি")

    def test_matches_only_for_same_concept(self) -> None:
        assert matches("গতিশক্তি", "kinetic energy")
        assert not matches("আকাশ", "আগুন")

    def test_variants_keep_original_first(self) -> None:
        assert variants("আকাশের")[0] == "আকাশের"


class TestCrossLingualRetrieval:
    def test_english_question_reaches_bengali_knowledge(self) -> None:
        brain = Brain()
        facts = brain.semantic_memory.query_flexible(subject="sky")
        assert any(fact.subject == "আকাশ" for fact in facts)

    def test_bengali_transliteration_reaches_curriculum(self) -> None:
        brain = Brain()
        facts = brain.semantic_memory.query_flexible(subject="kinetic energy")
        assert any("গতি" in fact.obj or "motion" in fact.obj for fact in facts)

    def test_strict_query_stays_exact(self) -> None:
        brain = Brain()
        assert brain.semantic_memory.query(subject="sky", predicate="রঙ") == []


class TestRelationQuestions:
    def test_capital_question_answers_the_relation(self) -> None:
        response = Brain().process("What is the capital of India?")["response"]
        assert "New Delhi" in response

    def test_bengali_capital_question(self) -> None:
        response = Brain().process("ভারতের রাজধানী কি?")["response"]
        assert "দিল্লি" in response or "Delhi" in response

    def test_author_question_names_the_author(self) -> None:
        response = Brain().process("Who wrote Gitanjali?")["response"]
        assert "Rabindranath Tagore" in response

    def test_formula_question_returns_formula(self) -> None:
        response = Brain().process("What is the formula of kinetic energy?")["response"]
        assert "mv" in response

    def test_bengali_function_question_uses_body_knowledge(self) -> None:
        response = Brain().process("হৃদয়ের কাজ কি?")["response"]
        assert "রক্ত" in response
        assert "W = Fs" not in response

    def test_predicate_detection_is_shared(self) -> None:
        assert UNIVERSAL_RESOLVER.detect_predicate("What is the capital of India?") == "capital"
        assert UNIVERSAL_RESOLVER.detect_predicate("গীতাঞ্জলি কে লিখেছেন?") == "wrote"


class TestGeneralKnowledge:
    def test_photosynthesis_english(self) -> None:
        response = Brain().process("What is photosynthesis?")["response"]
        assert_answered(response)
        assert "oxygen" in response

    def test_photosynthesis_bengali(self) -> None:
        response = Brain().process("সালোকসংশ্লেষণ কি?")["response"]
        assert_answered(response)
        assert "অক্সিজেন" in response

    def test_superlative_question(self) -> None:
        response = Brain().process("What is the largest ocean?")["response"]
        assert "Pacific" in response

    def test_cause_question_uses_stored_definition(self) -> None:
        response = Brain().process("ভূমিকম্প কেন হয়?")["response"]
        assert "ভূত্বক" in response

    def test_enumeration_list_from_definition(self) -> None:
        response = Brain().process("মহাদেশগুলোর নাম বলো")["response"]
        assert "এশিয়া" in response and "ইউরোপ" in response

    def test_answer_language_matches_question(self) -> None:
        response = Brain().process("আকাশের রঙ কি?")["response"]
        assert "নীল" in response
        assert "blue" not in response


class TestKnowledgeGaps:
    def test_unknown_question_is_refused_and_recorded(self) -> None:
        brain = Brain()
        # The humble fallback wording rotates, so the contract is the low
        # confidence and the recorded gap rather than a specific sentence.
        result = brain.process("What is quantum chromodynamics?")
        assert result["confidence"] <= 0.35
        assert result["grounding"]["grounding_source"] == "fallback"
        assert brain.knowledge_gaps, "unanswered question was not recorded"

    def test_repeated_gap_increments_count(self) -> None:
        brain = Brain()
        brain.process("What is quantum chromodynamics?")
        brain.process("What is quantum chromodynamics?")
        assert max(int(gap["count"]) for gap in brain.knowledge_gaps) >= 2

    def test_answered_question_records_no_gap(self) -> None:
        brain = Brain()
        brain.process("What is photosynthesis?")
        assert not brain.knowledge_gaps

    def test_assessment_clone_records_no_gap(self) -> None:
        brain = Brain()
        brain.enable_assessment_mode()
        brain.process("What is quantum chromodynamics?")
        assert brain.knowledge_gaps == []


class TestSelfDirectedLearning:
    def test_disabled_by_default(self) -> None:
        assert Brain().self_directed_learner.enabled is False

    def test_disabled_learner_does_nothing(self) -> None:
        brain = Brain()
        result = asyncio.run(brain.self_directed_learner.study_once())
        assert result.error == "self_directed_learning_disabled"
        assert result.learned_total == 0

    def test_study_selects_most_frequent_gaps(self) -> None:
        brain = Brain()
        brain.knowledge_gaps = [
            {"topic": "rare topic", "count": 1, "last_seen": 1.0},
            {"topic": "frequent topic", "count": 5, "last_seen": 2.0},
        ]
        learner = SelfDirectedLearner(brain, enabled=True, topics_per_cycle=1)
        assert learner.select_topics() == ["frequent topic"]

    def test_study_stores_learned_facts_and_clears_gap(self) -> None:
        brain = Brain()
        brain.process("What is quantum chromodynamics?")
        assert brain.knowledge_gaps

        class OfflineLearner:
            """Stands in for the network so the test stays deterministic."""

            async def ingest_batch(self, topics, max_facts_per_topic=4):
                for topic in topics:
                    brain.semantic_memory.store_fact(
                        subject=topic,
                        predicate="is_a",
                        obj="a studied subject",
                        confidence=0.8,
                        source="web_learning_batch",
                    )
                return {"committed": [{"subject": topic} for topic in topics], "quarantined": []}

        brain.web_learner = OfflineLearner()
        brain.self_directed_learner.enabled = True
        result = asyncio.run(brain.self_directed_learner.study_once())
        assert result.learned_total >= 1
        assert brain.knowledge_gaps == []

    def test_assessment_mode_blocks_study(self) -> None:
        brain = Brain()
        brain.enable_assessment_mode()
        brain.self_directed_learner.enabled = True
        result = asyncio.run(brain.self_directed_learner.study_once())
        assert result.error == "assessment_mode"

    def test_autonomous_tick_reports_study_state(self) -> None:
        brain = Brain()
        asyncio.run(brain.autonomous_reflection_tick())
        assert "self_directed_study" in brain.last_autonomous_tick
        assert "open_knowledge_gaps" in brain.last_autonomous_tick
