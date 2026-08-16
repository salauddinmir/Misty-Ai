"""Tests for the Phase 3 dialogue context memory module."""

from brain.dialogue.context import DialogueContext


def test_bounded_history() -> None:
    ctx = DialogueContext(max_history=3)
    for i in range(5):
        ctx.add_turn(text=f"message {i}", role="user")
    assert len(ctx.history) == 3
    assert ctx.history[0].text == "message 2"


def test_bounded_salience() -> None:
    ctx = DialogueContext(max_salience=2)
    ctx.add_turn(text="আলফা বিটা গাম্মা", role="user")
    assert len(ctx.salient_entities) <= 2
    assert ctx.salient_entities[0] == "আলফা"


def test_newest_entity_ranked_first() -> None:
    ctx = DialogueContext()
    ctx.add_turn(text="আমার নাম রাহুল", role="user")
    ctx.add_turn(text="মিস্তি হলো এআই", role="user")
    assert ctx.salient_entities[0] == "মিস্তি"


def test_banned_words_never_salient() -> None:
    ctx = DialogueContext()
    ctx.add_turn(text="আসলে মিস্তি", role="user")
    assert "আসলে" not in ctx.salient_entities


def test_brain_turns_do_not_pollute_salience() -> None:
    ctx = DialogueContext()
    ctx.add_turn(text="আমার নাম রাহুল", role="user")
    ctx.add_turn(text="ধন্যবাদ রাহুল, আমি মিস্তি", role="brain")
    # The brain turn mentions 'মিস্তি' but brain turns must not feed salience
    assert "মিস্তি" not in ctx.salient_entities
    assert ctx.most_salient_entity == "রাহুল"


def test_topic_tracks_latest_user_entity() -> None:
    ctx = DialogueContext()
    ctx.add_turn(text="মিস্তি হলো এআই", role="user")
    assert ctx.topic == "মিস্তি"


def test_topic_set_on_user_turns_only() -> None:
    ctx = DialogueContext()
    ctx.add_turn(text="মিস্তি হলো এআই", role="user")
    ctx.add_turn(text="রোবট নতুন টেকনোলজি", role="brain")
    assert ctx.topic == "মিস্তি"


def test_history_texts() -> None:
    ctx = DialogueContext()
    ctx.add_turn(text="এক", role="user")
    ctx.add_turn(text="দুই", role="user")
    texts = ctx.get_history_texts()
    assert texts == ["এক", "দুই"]


def test_to_dict_and_reset() -> None:
    ctx = DialogueContext()
    ctx.add_turn(text="এক", role="user")
    data = ctx.to_dict()
    assert data["salient_entities"]
    ctx.reset()
    assert not ctx.salient_entities
    assert not ctx.history
