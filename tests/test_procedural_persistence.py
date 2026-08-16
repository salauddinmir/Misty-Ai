"""Tests for Phase-2 procedural memory persistence."""

import os
import tempfile

from apps.api.database import Database
from brain.memory.procedural import ProceduralMemory, Procedure


async def _make_db() -> tuple[Database, str]:
    tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    tmp.close()
    db = Database(db_path=tmp.name)
    await db.initialize()
    return db, tmp.name


def _clean(path: str) -> None:
    try:
        os.unlink(path)
    except OSError:
        pass


class TestProcedureSchemaRoundtrip:
    """Procedures survive a save/load cycle through the SQLite schema."""

    def test_save_and_load_procedure(self) -> None:
        db, path = __import__("asyncio").run(_make_db())
        try:

            async def run() -> None:
                await db.save_procedure(
                    procedure_id="p1",
                    name="greet",
                    condition="hello",
                    action="say_hi",
                    strength=0.7,
                    use_count=4,
                    success_count=3,
                )
                loaded = await db.load_procedures()
                assert len(loaded) == 1
                assert loaded[0]["name"] == "greet"
                assert loaded[0]["strength"] == 0.7
                assert loaded[0]["use_count"] == 4
                assert loaded[0]["success_count"] == 3

            __import__("asyncio").run(run())
        finally:
            _clean(path)

    def test_upsert_updates_statistics(self) -> None:
        db, path = __import__("asyncio").run(_make_db())
        try:

            async def run() -> None:
                await db.save_procedure("p1", "greet", "hello", "say_hi", strength=0.5)
                await db.save_procedure("p1", "greet", "hello", "say_hi", strength=0.9, use_count=10)
                loaded = await db.load_procedures()
                assert len(loaded) == 1
                assert loaded[0]["strength"] == 0.9
                assert loaded[0]["use_count"] == 10

            __import__("asyncio").run(run())
        finally:
            _clean(path)

    def test_existing_table_not_dropped(self) -> None:
        """Schema idempotency: re-running the schema preserves rows."""
        db, path = __import__("asyncio").run(_make_db())
        try:

            async def run() -> None:
                await db.save_procedure("p1", "greet", "hello", "say_hi", strength=0.5)
                await db.initialize()  # re-apply schema
                loaded = await db.load_procedures()
                assert len(loaded) == 1

            __import__("asyncio").run(run())
        finally:
            _clean(path)


class TestProcedureReinforcementPersistence:
    """Reinforcement updates propagate to persisted statistics."""

    def test_reinforce_changes_strength(self) -> None:
        proc = Procedure(name="greet", condition="hello", action="say_hi")
        initial = proc.strength
        proc.reinforce(success=True)
        assert proc.strength > initial
        assert proc.use_count == 1
        assert proc.success_count == 1

    def test_procedural_memory_get_strongest(self) -> None:
        memory = ProceduralMemory()
        memory.store(name="a", condition="greet", action="say_hi", strength=0.3)
        strong = memory.store(name="b", condition="greet", action="say_hi_loud", strength=0.9)
        assert memory.get_strongest("please greet me") is strong
        assert memory.size == 2
