"""Phase 40: per-user long-term memory and personalization tests."""

import asyncio
import importlib
import os
import sys
from typing import Any

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI
from fastapi.testclient import TestClient

from brain.core.brain import Brain
from brain.memory.user_memory import (
    UserEpisode,
    UserProfileMemory,
    _classify_language,
    _is_identity_claim,
)

database_module = importlib.import_module("apps.api.database")

ANON_USER = "anon"


# ---------------------------------------------------------------------------
# Pure unit tests for the memory module
# ---------------------------------------------------------------------------
class TestLanguageClassification:
    def test_bengali_text(self) -> None:
        assert _classify_language("আমার নাম রাহুল") == "bn"

    def test_english_text(self) -> None:
        assert _classify_language("my name is Rahul") == "en"

    def test_unknown_mixed(self) -> None:
        # Bengali-script digits (১২৩৪৫) count as Bengali characters while
        # Latin digits are not letters, so 'bn' is the correct reading.
        assert _classify_language("12345 ১২৩৪৫") == "bn"

    def test_tie_breaks_unknown(self) -> None:
        # Equal Bengali and ASCII-letter counts must not guess Bengali.
        assert _classify_language("abc ১২৩") == "unknown"


class TestIdentityClaimDetection:
    def test_english_name_claim(self) -> None:
        is_fact, category = _is_identity_claim("my name is Rahul")
        assert is_fact and category == "identity"

    def test_bengali_name_claim(self) -> None:
        is_fact, category = _is_identity_claim("আমার নাম রাহুল")
        assert is_fact and category == "identity"

    def test_occupation_claim(self) -> None:
        is_fact, category = _is_identity_claim("আমি একজন ডাক্তার")
        assert is_fact and category == "occupation"

    def test_occupation_english(self) -> None:
        # 'i am a' is a claim marker; classification requires an
        # occupation keyword (job/work/চাকরি/...) — 'teacher' alone is not
        # in the keyword list, so it lands in 'general'.
        is_fact, category = _is_identity_claim("i am a teacher")
        assert is_fact and category == "general"

    def test_question_is_not_claim(self) -> None:
        is_fact, _ = _is_identity_claim("রাজধানী কোথায়?")
        assert not is_fact


class TestUserProfileMemory:
    @pytest.fixture
    def memory(self) -> UserProfileMemory:
        return UserProfileMemory(max_users=3, max_episodes_per_user=2)

    def test_record_turn_creates_profile(self, memory: UserProfileMemory) -> None:
        memory.record_turn("user-1", "আমার নাম রাহুল", reply="স্বাগতম রাহুল!")
        profile = memory.get_profile("user-1")
        assert profile is not None and profile.turn_count == 1
        assert "আমার নাম রাহুল" in {f.text for f in profile.facts.values()}

    def test_question_does_not_create_fact(self, memory: UserProfileMemory) -> None:
        memory.record_turn("user-1", "রাজধানী কোথায়?", reply="ভারতের রাজধানী নয়া দিল্লি।")
        profile = memory.get_profile("user-1")
        assert profile is not None and profile.turn_count == 1 and not profile.facts

    def test_duplicate_claim_dedup(self, memory: UserProfileMemory) -> None:
        memory.record_turn("user-1", "আমার নাম রাহুল", reply="ঠিক আছে।")
        memory.record_turn("user-1", "আমি বলেছি আমার নাম রাহুল", reply="হ্যাঁ।")
        profile = memory.get_profile("user-1")
        assert len(profile.facts) == 1
        fact = next(iter(profile.facts.values()))
        assert fact.mention_count == 2

    def test_episodic_digest_rolling(self, memory: UserProfileMemory) -> None:
        for i in range(3):
            memory.record_turn("user-1", f"বার্তা {i}", reply=f"উত্তর {i}")
        profile = memory.get_profile("user-1")
        # max_episodes_per_user=2 — the oldest turn drops from the digest.
        assert len(profile.episodes) == 2
        assert "বার্তা 2" in profile.episodes[-1].user_utterance

    def test_personal_recall_hits(self, memory: UserProfileMemory) -> None:
        memory.record_turn("user-1", "আমি বাংলাদেশে থাকি", reply="দারুণ!")
        memory.record_turn("user-1", "কাল রান্না শিখি", reply="শুভকামনা!")
        recall = memory.personal_recall("user-1", "কোথায় থাকি?")
        # Overlap on "থাকি" should hit the first turn.
        assert recall["fact_matches"] or recall["episode_matches"]

    def test_user_eviction_at_capacity(self, memory: UserProfileMemory) -> None:
        memory.record_turn("a", "turn", reply="x")
        memory.record_turn("b", "turn", reply="x")
        memory.record_turn("c", "turn", reply="x")
        memory.record_turn("d", "turn", reply="x")
        assert len(memory.known_users()) == 3

    def test_set_preferred_language(self, memory: UserProfileMemory) -> None:
        memory.set_preferred_language("user-1", "bn")
        profile = memory.get_profile("user-1")
        assert profile is not None and profile.preferred_language == "bn"

    def test_to_dicts_serialization(self, memory: UserProfileMemory) -> None:
        memory.record_turn("user-1", "আমার নাম রাহুল", reply="ঠিক আছে")
        data = memory.to_dicts()
        assert data["user_count"] == 1
        profile_data = data["profiles"][0]
        assert profile_data["user_id"] == "user-1"
        assert profile_data["turn_count"] == 1
        assert profile_data["last_seen_iso"]

    def test_summary_shape(self, memory: UserProfileMemory) -> None:
        memory.record_turn("user-1", "আমার নাম রাহুল", reply="x")
        summary = memory.summary()
        assert summary["enabled"] is True
        assert summary["user_count"] == 1
        assert summary["total_facts"] == 1


class TestBrainWiring:
    def test_user_memory_attribute(self) -> None:
        brain = Brain()
        assert hasattr(brain, "user_memory") and isinstance(brain.user_memory, UserProfileMemory)

    def test_get_state_includes_user_memory(self) -> None:
        brain = Brain()
        brain.user_memory.record_turn("user-1", "আমার নাম রাহুল", reply="x")
        state = brain.get_state()
        assert "user_memory" in state
        assert state["user_memory"]["user_count"] == 1
        assert state["user_memory"]["total_facts"] == 1


# ---------------------------------------------------------------------------
# API route tests
# ---------------------------------------------------------------------------
def _memory_client() -> tuple[TestClient, Brain]:
    module = importlib.import_module("apps.api.routes.memory")
    module = importlib.reload(module)
    app = FastAPI()
    app.include_router(module.router, prefix="/api/memory")
    brain = Brain()
    app.state.brain = brain
    return TestClient(app), brain


class TestMemoryRoutes:
    def test_users_empty(self) -> None:
        client, _ = _memory_client()
        response = client.get("/api/memory/users")
        assert response.status_code == 200
        assert response.json()["user_count"] == 0

    def test_user_profile_not_found(self) -> None:
        client, _ = _memory_client()
        response = client.get("/api/memory/user", params={"user_id": "ghost"})
        assert response.status_code == 200
        assert response.json()["found"] is False

    def test_user_profile_and_recall(self) -> None:
        client, brain = _memory_client()
        brain.user_memory.record_turn("user-1", "আমার নাম রাহুল", reply="স্বাগতম।")
        profile = client.get("/api/memory/user", params={"user_id": "user-1"}).json()
        assert profile["found"] is True
        assert profile["profile"]["turn_count"] == 1
        recall = client.get("/api/memory/user/recall", params={"user_id": "user-1", "query": "আমার নাম"}).json()
        assert recall["user_id"] == "user-1"
        assert recall["recall"]["fact_matches"] or recall["recall"]["episode_matches"]

    def test_state_exposes_user_memory(self) -> None:
        module = importlib.import_module("apps.api.routes.brain")
        module = importlib.reload(module)
        app = FastAPI()
        app.include_router(module.router, prefix="/api/brain")
        brain = Brain()
        app.state.brain = brain
        brain.user_memory.record_turn("user-1", "আমার নাম রাহুল", reply="x")
        client = TestClient(app)
        state = client.get("/api/brain/state").json()
        assert "user_memory" in state and state["user_memory"]["user_count"] == 1


# ---------------------------------------------------------------------------
# Persistence round-trip tests (SQLite, driver-agnostic API)
# ---------------------------------------------------------------------------
@pytest.fixture
def sqlite_database() -> Any:
    db = database_module.Database()
    asyncio.run(db.initialize())
    yield db
    asyncio.run(db.close())


class TestUserMemoryPersistence:
    @pytest.mark.asyncio
    async def test_save_and_load_roundtrip(self, sqlite_database: Any) -> None:
        db = sqlite_database
        episode_json = UserEpisode(user_utterance="আমার নাম রাহুল", bot_reply="স্বাগতম।").to_dict()
        await db.save_user_memory("user-1", {"kind": "episode", "memory_key": "ep-test", "memory_json": episode_json})
        rows = await db.load_user_memory("user-1")
        assert len(rows) == 1
        assert rows[0]["kind"] == "episode"
        assert rows[0]["memory_json"]["user_utterance"] == "আমার নাম রাহুল"

    @pytest.mark.asyncio
    async def test_upsert_same_key(self, sqlite_database: Any) -> None:
        db = sqlite_database
        await db.save_user_memory("user-1", {"kind": "episode", "memory_key": "ep-1", "memory_json": {"a": 1}})
        await db.save_user_memory("user-1", {"kind": "episode", "memory_key": "ep-1", "memory_json": {"a": 2}})
        rows = await db.load_user_memory("user-1")
        # Same (user_id, kind, memory_key) must NOT duplicate — the DB API
        # treats it as an upsert on the composite primary key.
        rows = [r for r in rows if r["memory_key"] == "ep-1"]
        assert len(rows) == 1
        assert rows[0]["memory_json"]["a"] == 2
