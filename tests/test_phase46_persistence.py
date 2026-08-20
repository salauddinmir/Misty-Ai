"""Phase 46: persistent semantic fact storage and audit log."""

import asyncio
import os
import sys
import time

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from apps.api.database import Database


@pytest.fixture
def database(tmp_path):
    db_path = tmp_path / "misty_phase46.db"
    db = Database(db_path=str(db_path))
    asyncio.run(db.initialize())
    yield db
    asyncio.run(db.close())
    if db_path.exists():
        db_path.unlink()


@pytest.fixture
def sample_facts():
    now = time.time()
    return {
        "sun:rises_in:east": {
            "subject": "sun",
            "predicate": "rises_in",
            "obj": "east",
            "confidence": 0.92,
            "source": "web_learning",
            "created_at": now - 60,
            "accessed_at": now - 10,
        },
        "water:boils_at:100C": {
            "subject": "water",
            "predicate": "boils_at",
            "obj": "100C",
            "confidence": 0.8,
            "source": "training",
            "created_at": now - 30,
            "accessed_at": now,
        },
        "dhaka:capital_of:bangladesh": {
            "subject": "dhaka",
            "predicate": "capital_of",
            "obj": "bangladesh",
            "confidence": 0.99,
            "source": "curriculum",
            "created_at": now - 10,
            "accessed_at": now,
        },
    }


class TestFactPersistence:
    def test_save_and_load_roundtrip(self, database, sample_facts):
        asyncio.run(database.save_facts(sample_facts))
        loaded = asyncio.run(database.load_facts())
        keys = {row["fact_key"] for row in loaded}
        assert keys == set(sample_facts)
        for row in loaded:
            original = sample_facts[row["fact_key"]]
            assert row["confidence"] == original["confidence"]
            assert row["source"] == original["source"]
            assert abs(row["created_at"] - original["created_at"]) < 1

    def test_upsert_updates_confidence(self, database, sample_facts):
        asyncio.run(database.save_facts(sample_facts))
        updated = {"sun:rises_in:east": {**sample_facts["sun:rises_in:east"], "confidence": 0.7}}
        asyncio.run(database.save_facts(updated))
        loaded = {row["fact_key"]: row for row in asyncio.run(database.load_facts())}
        assert loaded["sun:rises_in:east"]["confidence"] == 0.7
        assert len(loaded) == 3

    def test_timestamps_preserved_across_restarts(self, database, sample_facts, tmp_path):
        # Simulate two separate brain lifetimes sharing one DB file.
        asyncio.run(database.save_facts(sample_facts))
        asyncio.run(database.close())
        db_path = str(tmp_path / "misty_phase46.db")
        second = Database(db_path=db_path)
        asyncio.run(second.initialize())
        loaded = asyncio.run(second.load_facts())
        row = next(row for row in loaded if row["fact_key"] == "sun:rises_in:east")
        assert abs(row["created_at"] - sample_facts["sun:rises_in:east"]["created_at"]) < 1
        asyncio.run(second.close())

    def test_load_respects_limit(self, database, sample_facts):
        asyncio.run(database.save_facts(sample_facts))
        loaded = asyncio.run(database.load_facts(limit=2))
        assert len(loaded) == 2

    def test_save_empty_facts_is_noop(self, database):
        asyncio.run(database.save_facts({}))
        assert asyncio.run(database.load_facts()) == []

    def test_cold_start_restore_into_semantic_memory(self, database, sample_facts, tmp_path):
        """Facts saved by one brain lifetime must restore with timestamps."""
        asyncio.run(database.save_facts(sample_facts))
        asyncio.run(database.close())

        from brain.core.brain import Brain

        brain = Brain()
        asyncio.run(database.initialize())
        records = asyncio.run(database.load_facts())
        restored = 0
        for record in records:
            key = brain.semantic_memory.store_fact(
                subject=record["subject"],
                predicate=record["predicate"],
                obj=record["obj"],
                confidence=record["confidence"],
                source=record["source"],
            )
            fact = brain.semantic_memory.facts.get(key)
            if fact is not None:
                fact.created_at = record["created_at"]
                fact.accessed_at = record["accessed_at"]
                restored += 1
        assert restored == 3
        fact = brain.semantic_memory.facts["sun:rises_in:east"]
        assert abs(fact.created_at - sample_facts["sun:rises_in:east"]["created_at"]) < 1
        # Aging must see the restored birth time, not a huge negative age.
        summary = brain.fact_ager.age_facts(now=sample_facts["sun:rises_in:east"]["created_at"] + 5)
        assert "sun:rises_in:east" in brain.semantic_memory.facts
        assert summary["pruned"] == 0


class TestAuditLogPersistence:
    def test_save_and_load_audit_rows(self, database):
        rows = [
            {"audit_kind": "aging", "fact_key": "a:b:c", "action": "decayed", "confidence": 0.7},
            {"audit_kind": "consolidation", "fact_key": "x:y:z", "action": "rehearsed", "confidence": 0.6},
        ]
        asyncio.run(database.save_audit_rows(rows))
        loaded = asyncio.run(database.load_audit_rows(limit=100))
        kinds = {row["audit_kind"] for row in loaded}
        assert {"aging", "consolidation"}.issubset(kinds)

    def test_kind_filter(self, database):
        asyncio.run(
            database.save_audit_rows(
                [
                    {"audit_kind": "aging", "fact_key": "a:b:c", "action": "decayed", "confidence": 0.7},
                    {"audit_kind": "consolidation", "fact_key": "x:y:z", "action": "rehearsed", "confidence": 0.6},
                ]
            )
        )
        loaded = asyncio.run(database.load_audit_rows(kind="aging"))
        assert all(row["audit_kind"] == "aging" for row in loaded)

    def test_audit_log_is_bounded(self, database):
        # Write well past the 4000-row cap.
        batch = [
            {"audit_kind": "aging", "fact_key": f"f{i}", "action": "decayed", "confidence": 0.5} for i in range(4200)
        ]
        asyncio.run(database.save_audit_rows(batch))
        rows = asyncio.run(database.load_audit_rows())
        assert len(rows) <= 4000

    def test_empty_rows_is_noop(self, database):
        asyncio.run(database.save_audit_rows([]))
        assert asyncio.run(database.load_audit_rows()) == []
