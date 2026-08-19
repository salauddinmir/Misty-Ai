"""Phase 18b: graceful unknown-question handling.

Regression guards for the user-reported complaint where casual Bengali
follow-ups like "বুঝলাম না" or "কি ব্যাপার?" triggered the canned
parser-failure reply. Two rules are enforced:

1. The NLU parser must classify clarification/casual turns as CONVERSATION
   instead of UNKNOWN.
2. The live brain must never reply with the canned parse-failure message
   for those inputs (or for fully unknown questions), even when no stored
   knowledge applies.
"""

import pytest

from brain.core.brain import Brain
from brain.nlu.parser import IntentType, NLUParser

_CANNED_PARSE_FAILURE = "ইনটেনট নির্ভুলভাবে parse করতে পারছি না"


@pytest.fixture(name="parser")
def parser() -> NLUParser:
    return NLUParser()


@pytest.fixture(name="brain")
def brain() -> Brain:
    return Brain(use_neural_sim=False)


# ---------------------------------------------------------------------------
# NLU classification
# ---------------------------------------------------------------------------


def test_bn_clarification_is_conversation(parser: NLUParser) -> None:
    for text in ["বুঝলাম না", "বুঝতে পারছি না", "কি ব্যাপার?", "কী ব্যাপার", "কেন?"]:
        assert parser.parse(text).intent is IntentType.CONVERSATION


def test_en_clarification_is_conversation(parser: NLUParser) -> None:
    # Phase 28: "why?" is now a genuine QUERY_WHAT with relation=why (the
    # topic-anchoring why-follow-up feature). It is still handled
    # gracefully — the live-brain no-canned-reply guard below covers it.
    for text in ["I don't understand", "I don't get it", "What's up?"]:
        assert parser.parse(text).intent is IntentType.CONVERSATION


# ---------------------------------------------------------------------------
# Live brain responses
# ---------------------------------------------------------------------------


def test_bn_clarification_no_canned_reply(brain: Brain) -> None:
    for text in ["বুঝলাম না", "কি ব্যাপার?"]:
        output = brain.process(text)
        assert output["response"] is not None
        assert _CANNED_PARSE_FAILURE not in output["response"]


def test_en_clarification_no_canned_reply(brain: Brain) -> None:
    for text in ["I don't understand", "why?"]:
        output = brain.process(text)
        assert output["response"] is not None
        assert _CANNED_PARSE_FAILURE not in output["response"]


def test_unknown_question_graceful_no_canned_reply(brain: Brain) -> None:
    """A question about something completely outside Misty's knowledge must
    get an honest uncertainty reply, never the canned parse-failure line."""
    output = brain.process("টাইটানিকের ক্যাপটেনের নাম কী?")
    assert output["response"] is not None
    assert _CANNED_PARSE_FAILURE not in output["response"]


def test_inference_answer_before_canned(brain: Brain) -> None:
    """Questions with matching stored commonsense must derive an answer."""
    output = brain.process("আকাশের রঙ কী?")
    response = output["response"].lower()
    assert "নীল" in response or "blue" in response
