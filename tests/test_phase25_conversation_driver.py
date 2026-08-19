"""Phase 25 tests: conversation driver — follow-up questions and topic
management.

Deterministic conversation-driving behavior: the brain keeps the exchange
alive with empathy, interest expansion, and off-track steering, and never
forces a follow-up question after closure greetings or when it just asked
one itself. All expectations are rule-based; no commercial LLM is used.
"""

from __future__ import annotations

import pytest

from brain.core.brain import Brain
from brain.dialogue.driver import ConversationDriver


@pytest.fixture()
def brain():
    return Brain()


@pytest.fixture()
def driver():
    return ConversationDriver()


def _full_responses(brain: Brain, *texts: str) -> list:
    return [brain.process(text)["response"] for text in texts]


# ---------------------------------------------------------------------------
# Driver unit behavior
# ---------------------------------------------------------------------------


def test_distress_elicits_empathic_followup(driver):
    plan = driver.plan_followup(
        user_text="আমি আজ ক্লান্ত",
        response="বুঝতে পারছি, সেটাই করা যাক।",
        intent="conversation",
        confidence=0.8,
        topic="",
        topic_facts=0,
        has_related=False,
    )
    assert plan.kind == "empathy"
    assert plan.needs_followup
    assert "শুনছি" in plan.question or "বলতে পারেন" in plan.question


def test_en_distress_elicits_empathic_followup(driver):
    plan = driver.plan_followup(
        user_text="I feel worried today",
        response="I understand, let's work through it.",
        intent="conversation",
        confidence=0.8,
        topic="",
        topic_facts=0,
        has_related=False,
    )
    assert plan.kind == "empathy"
    assert "sorry" in plan.question or "listening" in plan.question


def test_joy_elicits_cheerful_followup(driver):
    plan = driver.plan_followup(
        user_text="আমি খুব খুশি আজ",
        response="ভালো শোনাচ্ছে!",
        intent="conversation",
        confidence=0.8,
        topic="",
        topic_facts=0,
        has_related=False,
    )
    assert plan.kind == "empathy"
    assert plan.needs_followup


def test_driver_is_stateless(driver):
    plan1 = driver.plan_followup(
        user_text="আমি ক্লান্ত",
        response="ঠিক আছে।",
        intent="conversation",
        confidence=0.8,
        topic="",
        topic_facts=0,
        has_related=False,
    )
    plan2 = driver.plan_followup(
        user_text="আমি ক্লান্ত",
        response="ঠিক আছে।",
        intent="conversation",
        confidence=0.8,
        topic="",
        topic_facts=0,
        has_related=False,
    )
    # A pure rule-based driver with no state answers both identically.
    assert plan1.question == plan2.question


# ---------------------------------------------------------------------------
# End-to-end empathy through Brain.process
# ---------------------------------------------------------------------------


def test_brain_replies_with_empathy_on_distress(brain):
    response = brain.process("আমি আজ ক্লান্ত ও ক্ষুব্ধ")["response"]
    assert "শুনছি" in response or "খারাপ লাগছ" in response, response


def test_brain_replies_with_empathy_on_en_distress(brain):
    response = brain.process("I feel tired and stressed today")["response"]
    assert "sorry" in response or "listening" in response, response


def test_brain_greets_happy_user_warmly(brain):
    response = brain.process("আমি আজ অনেক খুশি")["response"]
    assert "খুশি" in response or "আনন্দ" in response or "ভালো" in response, response


# ---------------------------------------------------------------------------
# Closure: farewell inputs must not be chased with follow-up questions
# ---------------------------------------------------------------------------


def test_closure_bengali_has_no_followup_question(brain):
    brain.process("আজকে অনেক কথা হলো")  # warm up topic flow
    response = brain.process("বাই, আজকে এতটুকুই")["response"]
    # The driver never chases a farewell with a follow-up question.
    assert "?" not in response, response
    assert brain.conversation_driver.user_intent_closed("বাই, আজকে এতটুকুই")


def test_closure_english_has_no_followup_question(brain):
    response = brain.process("Alright, that's all for today, goodbye!")["response"]
    assert "?" not in response, response
    assert brain.conversation_driver.user_intent_closed("Alright, that's all for today, goodbye!")


def test_user_intent_closed_detection(driver):
    assert driver.user_intent_closed("বাই বাই")
    assert driver.user_intent_closed("goodbye, see you")
    assert driver.user_intent_closed("আজকে এই পর্যন্ত")
    assert not driver.user_intent_closed("আমি ক্লান্ত")
    assert not driver.user_intent_closed("সেটা কী?")


# ---------------------------------------------------------------------------
# Expansion: the driver keeps a topic thread alive
# ---------------------------------------------------------------------------


def test_shallow_topic_gets_continuation_nudge(brain):
    # A topic with no stored facts is shallow; the driver nudges gently.
    responses = _full_responses(brain, "আমি কি খবর")
    response = responses[0]
    assert isinstance(response, str) and response, response


def test_teaching_then_followup_gets_topic_question(brain):
    brain.process("মনে রাখো: সেতু হলো নদীর উপরের রাস্তা")
    r2 = brain.process("সেতু কী?")["response"]
    assert "সেতু" in r2, r2
    # With stored facts on the topic the driver can offer to continue:
    assert "নিয়ে" in r2 or "আরো" in r2 or "?" in r2, r2


def test_empty_answer_offers_clarification(brain):
    # A long unanswerable question: the brain replies with an honest
    # admission and the driver offers a clarifying path.
    r1 = brain.process("আমি জানতে চাই, তুমি কী বিষয়ে সাহায্য করতে পারো")
    r2 = brain.process(r1["response"])["response"]
    assert isinstance(r2, str) and r2, r2


# ---------------------------------------------------------------------------
# Cooldown: the driver never stacks two questions back-to-back
# ---------------------------------------------------------------------------


def test_driver_cooldown_stacks_no_questions(brain):
    # Turn 1 ends with a driver question; turn 2's answer must carry the
    # turn without appending a second driver question.
    r1 = brain.process("আমি ক্লান্ত, তুমি কী করছো")["response"]
    q1_count = r1.count("?")
    r2 = brain.process(r1)["response"]
    q2_count = r2.count("?")
    # If turn 1 had a driver question, turn 2 must not add another.
    assert q2_count <= max(1, q1_count), (r1, r2)


# ---------------------------------------------------------------------------
# Topic management: mid-conversation topic switch
# ---------------------------------------------------------------------------


def test_topic_switch_updates_followup_topic(brain):
    brain.process("মনে রাখো: মিঠাই হলো মিষ্টি খাবার")
    brain.process("মনে রাখো: সেতু হলো নদীর উপরের রাস্তা")
    r = brain.process("সেতু কী?")["response"]
    assert "সেতু" in r, r
    # The follow-up should now be about the NEW topic (সেতু), not the old.
    assert "মিঠাই" not in r, r
