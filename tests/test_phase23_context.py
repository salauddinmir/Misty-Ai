"""Phase 23: context-aware responses.

The brain must remember what was discussed in earlier turns and resolve
follow-up questions like "কারণ কী?", "আর বলো", "সেটা কী?" against the
prior topic instead of the literal words of the current turn.
"""

import pytest

from brain.core.brain import Brain


@pytest.fixture()
def brain():
    return Brain()


def _ask(brain: Brain, *questions: str) -> str:
    response = ""
    for question in questions:
        response = brain.process(question)["response"]
    return response


def test_follow_up_why_anchors_previous_topic(brain):
    """'কারণ কী?' after asking about the sky must talk about the sky."""
    _ask(brain, "আকাশের রঙ কি?")
    response = _ask(brain, "কারণ কী?")
    assert "আকাশ" in response


def test_continuation_expands_prior_topic(brain):
    """'আর বলো' must keep talking about the previous topic, not 'আর'."""
    _ask(brain, "আকাশের রঙ কি?")
    response = _ask(brain, "আর বলো")
    assert "আর" not in response.split("বলো")[0] or "আকাশ" in response
    assert "আকাশ" in response or "নীল" in response


def test_context_echo_references_recent_discussion(brain):
    """An unresolved statement should acknowledge the recent topic.

    The brain tries knowledge synthesis first; when no facts match (a
    random phrase about the recently discussed topic) the echo handler
    still names the prior topic instead of a generic robot reply.
    """
    _ask(brain, "আকাশের রঙ কি?")
    response = _ask(brain, "আকাশের মাঝে একটা বেলুন")
    assert "আকাশ" in response


def test_follow_up_after_teaching(brain):
    """Follow-up after teaching a fact should recall the taught topic."""
    brain.process("মনে রাখো: স্যাটেলাইট হলো যোগাযোগে ব্যবহৃত কৃত্রিম উপগ্রহ")
    response = _ask(brain, "সেট কী?")
    assert "স্যাটেলাইট" in response
    # The taught fact (subject হলো object) or a richer derived fact may
    # answer; the taught fact must at least be stored in the semantic layer.
    known = {f"{f.subject}:{f.obj}" for f in brain.semantic_memory.facts.values()}
    assert any("স্যাটেলাইট" in k and "উপগ্রহ" in k for k in known), known


def test_follow_up_after_teaching_anchors_taught_topic(brain):
    """Follow-up after teaching must recall the taught concept."""
    brain.process("মনে রাখো: স্যাটেলাইট হলো যোগাযোগে ব্যবহৃত কৃত্রিম উপগ্রহ")
    response = _ask(brain, "সেট কী?")
    assert "স্যাটেলাইট" in response


def test_no_topic_means_honest_no_context(brain):
    """With no prior discussion, continuation admits having no topic."""
    response = _ask(brain, "আর বলো")
    assert "টপিক" in response or "আলো" in response
