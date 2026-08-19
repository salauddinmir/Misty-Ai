"""Phase 43: personal recall integration in conversation responses.

The visitor id binds a cognitive cycle to the person Misty is talking to,
so remembered facts and recent episodes that overlap the query join the
cycle's recall evidence as `personal_context`, are broadcast as
workspace evidence, and are exposed in the chat reply and brain state.
"""

import importlib
from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from brain.core.brain import Brain


@pytest.fixture()
def brain() -> Brain:
    return Brain()


def _remember(brain: Brain, user_id: str) -> None:
    memory = brain.user_memory
    memory.record_turn(user_id, "আমার নাম রাহুল", intent="general")
    memory.record_turn(user_id, "আমি একজন শিক্ষক", intent="general")
    memory.record_turn(user_id, "আমি ফুটবল খেলতে ভালোবাসি", intent="general")


def _chat_client(brain: Brain) -> tuple[TestClient, Brain]:
    module = importlib.import_module("apps.api.routes.chat")
    module = importlib.reload(module)
    app = FastAPI()
    app.include_router(module.router, prefix="/api")
    app.state.brain = brain
    app.state.warmup_complete = True
    # The persistence path reads app_state.database; give it a dev SQLite
    # store so background persistence never crashes the turn.
    database_module = importlib.import_module("apps.api.database")
    app.state.database = database_module.Database()
    pass  # persistence failures are tolerated by the chat route
    brain_module = importlib.import_module("apps.api.routes.brain")
    app.include_router(brain_module.router, prefix="/api/brain")
    return TestClient(app), brain


def test_user_id_default_is_anon(brain: Brain) -> None:
    assert brain.current_user_id == "anon"


def test_process_bind_visits_id(brain: Brain) -> None:
    brain.process("হাল্লো", user_id="rahu123")
    assert brain.current_user_id == "rahu123"


def test_empty_header_id_fallback_to_anon(brain: Brain) -> None:
    brain.process("হাল্লো", user_id="  ")
    assert brain.current_user_id == "anon"


def test_recalled_fact_merges_personal_context(brain: Brain) -> None:
    _remember(brain, "rahu123")
    result = brain.process("আমার নাম কি?", user_id="rahu123")
    personal: dict[str, Any] = result.get("personal_recall", {})
    assert personal.get("user_id") == "rahu123"
    assert any("রাহুল" in str(fact) for fact in personal.get("fact_matches", []))


def test_recalled_episode_merges_personal_context(brain: Brain) -> None:
    _remember(brain, "rahu123")
    result = brain.process("ফুটবল", user_id="rahu123")
    personal: dict[str, Any] = result.get("personal_recall", {})
    episode_texts = [ep.get("user_utterance", "") for ep in personal.get("episode_matches", [])]
    assert any("ফুটবল" in text for text in episode_texts)


def test_other_user_facts_not_visible(brain: Brain) -> None:
    _remember(brain, "visitor_a")
    result = brain.process("আমার নাম", user_id="visitor_b")
    assert brain.current_user_id == "visitor_b"
    personal: dict[str, Any] = result.get("personal_recall", {})
    assert not personal.get("fact_matches")


def test_anon_bucket_sees_nothing_without_prior_turns(brain: Brain) -> None:
    result = brain.process("আমার নাম কি?", user_id="anon")
    assert brain.current_user_id == "anon"
    personal: dict[str, Any] = result.get("personal_recall", {})
    assert personal.get("fact_matches") in ([], None)
    assert personal.get("episode_matches") in ([], None)


def test_evidence_ids_included(brain: Brain) -> None:
    _remember(brain, "rahu123")
    result = brain.process("আমার নাম", user_id="rahu123")
    personal: dict[str, Any] = result.get("personal_recall", {})
    evidence_ids = [fact.get("evidence_id") for fact in personal.get("fact_matches", []) if fact.get("evidence_id")]
    assert evidence_ids


def test_brain_state_exposes_fields(brain: Brain) -> None:
    _remember(brain, "rahu123")
    brain.process("আমার নাম", user_id="rahu123")
    state = brain.get_state()
    assert state["current_user_id"] == "rahu123"
    assert isinstance(state["personal_recall"], dict)


def test_chat_endpoint_returns_personal_recall_and_user_id(brain: Brain) -> None:
    client, brain = _chat_client(brain)
    _remember(brain, "web-user-99")
    response = client.post(
        "/api/chat",
        json={"message": "আমার নাম কি?"},
        headers={"x-misty-user-id": "web-user-99"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload.get("personal_recall", {}).get("user_id") == "web-user-99"
    assert any("রাহুল" in str(fact) for fact in payload["personal_recall"].get("fact_matches", []))

    state = client.get("/api/brain/state").json()
    assert state.get("current_user_id") == "web-user-99"
    assert isinstance(state.get("personal_recall"), dict)


def test_no_user_header_uses_anon_bucket(brain: Brain) -> None:
    client, _ = _chat_client(brain)
    response = client.post("/api/chat", json={"message": "নমস্কার"})
    assert response.status_code == 200
    payload = response.json()
    assert brain.current_user_id == "anon"
    recall = payload.get("personal_recall", {})
    assert recall in ({}, None) or recall.get("fact_matches") in ([], None)
    state = client.get("/api/brain/state").json()
    assert state.get("current_user_id") == "anon"
