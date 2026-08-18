"""Phase 21a: bare Bengali "what is X" parsing + technology commonsense.

The user saw "স্যাটেলাইট কি?" answered with the canned parse-failure
message. The NLU parser previously required হলো/মানে in Bengali
definition queries, so the bare form "X কি?" fell through to UNKNOWN.
This suite guards against that regression and verifies the new
technology commonsense facts are derivable.
"""

import pytest

from brain.core.brain import Brain
from brain.knowledge.commonsense import _COMMONSENSE_FACTS
from brain.nlu.parser import IntentType, NLUParser

_CANNED_PARSE_FAILURE = "ইনটেনট নির্ভুলভাবে parse করতে পারছি না"


@pytest.fixture(name="parser")
def parser() -> NLUParser:
    return NLUParser()


@pytest.fixture(name="brain")
def brain() -> Brain:
    return Brain(use_neural_sim=False)


# ---------------------------------------------------------------------------
# NLU: bare "X কি?" must be QUERY_WHAT, not UNKNOWN
# ---------------------------------------------------------------------------

def test_bare_what_query_parsed(parser: NLUParser) -> None:
    for text in ["স্যাটেলাইট কি?", "স্যাটেলাইট কী।", "পানি কি?", "রোবট কী?"]:
        result = parser.parse(text)
        assert result.intent is IntentType.QUERY_WHAT, text
        assert result.query.get("target")


def test_bare_what_excludes_self_pronouns(parser: NLUParser) -> None:
    result = parser.parse("তুমি কি?")
    assert result.intent is not IntentType.QUERY_WHAT


def test_sentence_with_ki_not_definition(parser: NLUParser) -> None:
    """A multi-word phrase ending in কি is not forced into QUERY_WHAT."""
    result = parser.parse("আমি জানি কি তুমি বুঝছো")
    assert result.intent is not IntentType.QUERY_WHAT


def test_bare_what_excludes_misty_self_query(parser: NLUParser) -> None:
    """The brain itself answers identity queries through its self model,
    not through generic fact lookup."""
    result = parser.parse("মিস্টি কী?")
    assert result.intent is not IntentType.QUERY_WHAT


# ---------------------------------------------------------------------------
# Commonsense layer coverage
# ---------------------------------------------------------------------------

def test_technology_facts_loaded(brain: Brain) -> None:
    subjects = {fact.subject for fact in _COMMONSENSE_FACTS}
    for subject in ["স্যাটেলাইট", "satellite", "কম্পিউটার", "ইন্টারনেট", "রোবট"]:
        assert subject in subjects


def test_satellite_question_derives_answer(brain: Brain) -> None:
    output = brain.process("স্যাটেলাইট কি?")
    response = output["response"].lower()
    assert _CANNED_PARSE_FAILURE not in response
    assert "ঘূর্ণনরত" in response or "orbit" in response or "যন্ত্র" in response


def test_robot_question_derives_answer(brain: Brain) -> None:
    output = brain.process("রোবট কী?")
    response = output["response"].lower()
    assert _CANNED_PARSE_FAILURE not in response
    assert "যন্ত্র" in response or "machine" in response or "মিস্তি" in response


def test_internet_question_derives_answer(brain: Brain) -> None:
    output = brain.process("ইন্টারনেট কি?")
    response = output["response"].lower()
    assert _CANNED_PARSE_FAILURE not in response
    assert "জাল" in response or "network" in response or "সংযোগ" in response
