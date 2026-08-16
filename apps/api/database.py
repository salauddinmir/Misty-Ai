"""
Database Persistence Layer.

Provides async persistence for concepts, relations, episodes,
procedures, and brain states. The backend is chosen by the
MISTY_DB_URL environment variable:

- ``sqlite:///path`` or any non-postgres URL (default) -> SQLite (aiosqlite)
  for local development.
- ``postgresql://...`` (Supabase / Render Postgres) -> PostgreSQL
  (asyncpg with SQLAlchemy Core-style parameterized queries).

Schema is applied on startup from database/schema.sql (SQLite) or
database/schema_postgres.sql (PostgreSQL).
"""

import json
import os
import time as time_module
import uuid
from pathlib import Path
from typing import Any, Dict, List, Tuple

# ---------------------------------------------------------------------------
# Driver selection: asyncpg is the production PostgreSQL driver; both
# drivers are soft dependencies so the package still installs without them.
DRIVER = "sqlite"
if os.environ.get("MISTY_DB_URL", "").startswith("postgresql"):
    import asyncpg  # type: ignore

    DRIVER = "postgres"
else:
    import aiosqlite  # type: ignore

# ---------------------------------------------------------------------------
# Paths

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DEFAULT_DB_PATH = os.path.join(REPO_ROOT, "data", "misty_brain.db")
SCHEMA_SQLITE = os.path.join(REPO_ROOT, "database", "schema.sql")
SCHEMA_POSTGRES = os.path.join(REPO_ROOT, "database", "schema_postgres.sql")
UPSERT_SQLITE = "INSERT OR REPLACE"
UPSERT_POSTGRES = "INSERT"


def _db_url() -> str:
    return os.environ.get("MISTY_DB_URL") or f"sqlite:///{DEFAULT_DB_PATH}"


def _placeholders(count: int) -> str:
    """Parameter marker for the active driver: ``?`` (SQLite) or ``$n`` (postgres)."""
    if DRIVER == "postgres":
        return ", ".join(f"${n}" for n in range(1, count + 1))
    return ", ".join("?" for _ in range(count))


# ---------------------------------------------------------------------------


class Database:
    """Async persistence layer for the MISTY brain.

    SQLite (default) keeps local development friction-free; PostgreSQL
    (Supabase / Render) is used for production. The public API is
    identical for both drivers.
    """

    def __init__(self, db_path: str | None = None, db_url: str | None = None) -> None:
        self.db_path = db_path or DEFAULT_DB_PATH
        self._url = db_url or _db_url()
        self._connection: Any = None

    async def initialize(self) -> None:
        """Connect and apply the appropriate schema."""
        if DRIVER == "postgres":
            self._connection = await asyncpg.connect(self._url)
            schema_path = Path(SCHEMA_POSTGRES)
            if schema_path.exists():
                await self._connection.execute(schema_path.read_text(encoding="utf-8"))
        else:
            db_dir = os.path.dirname(self.db_path)
            if db_dir:
                os.makedirs(db_dir, exist_ok=True)
            self._connection = await aiosqlite.connect(self.db_path)
            self._connection.row_factory = aiosqlite.Row
            schema_path = Path(SCHEMA_SQLITE)
            if schema_path.exists():
                await self._connection.executescript(schema_path.read_text(encoding="utf-8"))
                await self._connection.commit()

    async def close(self) -> None:
        """Close the active connection."""
        if self._connection is not None:
            await self._connection.close()
            self._connection = None

    @property
    def connection(self) -> Any:
        """Get the active connection, raising if not initialized."""
        if self._connection is None:
            raise RuntimeError("Database not initialized. Call initialize() first.")
        return self._connection

    async def execute(self, sql: str, params: Tuple[Any, ...] = ()) -> Any:
        """Driver-uniform statement execution."""
        if DRIVER == "postgres":
            return await self._connection.execute(sql, *params)
        return await self._connection.execute(sql, params)

    async def fetchall(self, sql: str, params: Tuple[Any, ...] = ()) -> List[Any]:
        """Driver-uniform fetch of all rows."""
        if DRIVER == "postgres":
            return await self._connection.fetch(sql, *params)
        cursor = await self._connection.execute(sql, params)
        return await cursor.fetchall()

    # ==================== Concepts ====================

    async def save_concept(
        self,
        concept_id: str,
        name: str,
        concept_type: str = "generic",
        activation_level: float = 0.0,
        created_at: float | None = None,
        metadata: Dict[str, Any] | None = None,
    ) -> None:
        """Save or update a concept in the database."""
        created_at = created_at or time_module.time()
        metadata_json = json.dumps(metadata or {})

        base = UPSERT_POSTGRES if DRIVER == "postgres" else UPSERT_SQLITE
        sql = (
            f"{base} INTO concepts "
            f"(concept_id, name, concept_type, activation_level, created_at, metadata) "
            f"VALUES ({_placeholders(6)})"
        )
        if DRIVER == "postgres":
            sql += (
                " ON CONFLICT (concept_id) DO UPDATE SET "
                "name = EXCLUDED.name, concept_type = EXCLUDED.concept_type, "
                "activation_level = EXCLUDED.activation_level, "
                "created_at = EXCLUDED.created_at, metadata = EXCLUDED.metadata"
            )
        await self.execute(sql, (concept_id, name, concept_type, activation_level, created_at, metadata_json))
        if DRIVER != "postgres":
            await self._connection.commit()

    async def load_concepts(self) -> List[Dict[str, Any]]:
        """Load all concepts from the database."""
        rows = await self.fetchall("SELECT * FROM concepts")
        return [
            {
                "concept_id": row[0],
                "name": row[1],
                "concept_type": row[2],
                "activation_level": row[3],
                "created_at": row[4],
                "metadata": json.loads(row[5]) if row[5] else {},
            }
            for row in rows
        ]

    async def get_concept_by_name(self, name: str) -> Dict[str, Any] | None:
        """Load a concept by its name."""
        if DRIVER == "postgres":
            rows = await self.fetchall("SELECT * FROM concepts WHERE name = $1", (name,))
        else:
            rows = await self.fetchall("SELECT * FROM concepts WHERE name = ?", (name,))
        if rows:
            row = rows[0]
            return {
                "concept_id": row[0],
                "name": row[1],
                "concept_type": row[2],
                "activation_level": row[3],
                "created_at": row[4],
                "metadata": json.loads(row[5]) if row[5] else {},
            }
        return None

    # ==================== Relations ====================

    async def save_relation(
        self,
        source_id: str,
        target_id: str,
        relation_type: str,
        weight: float = 1.0,
        confidence: float = 1.0,
        metadata: Dict[str, Any] | None = None,
    ) -> str:
        """Save a relation between two concepts. Returns the relation ID."""
        relation_id = str(uuid.uuid4())[:8]
        created_at = time_module.time()
        metadata_json = json.dumps(metadata or {})

        await self.execute(
            "INSERT INTO relations "
            "(relation_id, source_id, target_id, relation_type, weight, confidence, created_at, metadata) "
            f"VALUES ({_placeholders(8)})",
            (relation_id, source_id, target_id, relation_type, weight, confidence, created_at, metadata_json),
        )
        if DRIVER != "postgres":
            await self._connection.commit()
        return relation_id

    async def load_relations(self) -> List[Dict[str, Any]]:
        """Load all relations from the database."""
        rows = await self.fetchall("SELECT * FROM relations")
        return [
            {
                "relation_id": row[0],
                "source_id": row[1],
                "target_id": row[2],
                "relation_type": row[3],
                "weight": row[4],
                "confidence": row[5],
                "created_at": row[6],
                "metadata": json.loads(row[7]) if row[7] else {},
            }
            for row in rows
        ]

    # ==================== Episodes ====================

    async def save_episode(
        self,
        content: str,
        context: Dict[str, Any] | None = None,
        emotional_valence: float = 0.0,
        importance: float = 0.5,
    ) -> str:
        """Save an episodic memory. Returns the episode ID."""
        episode_id = str(uuid.uuid4())[:8]
        timestamp = time_module.time()
        context_json = json.dumps(context or {})

        await self.execute(
            "INSERT INTO episodes "
            "(episode_id, content, context, timestamp, emotional_valence, importance) "
            f"VALUES ({_placeholders(6)})",
            (episode_id, content, context_json, timestamp, emotional_valence, importance),
        )
        if DRIVER != "postgres":
            await self._connection.commit()
        return episode_id

    async def load_episodes(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Load recent episodes from the database (newest first)."""
        rows = await self.fetchall(
            "SELECT * FROM episodes ORDER BY timestamp DESC LIMIT $1"
            if DRIVER == "postgres"
            else "SELECT * FROM episodes ORDER BY timestamp DESC LIMIT ?",
            (limit,),
        )
        return [
            {
                "episode_id": row[0],
                "content": row[1],
                "context": json.loads(row[2]) if row[2] else {},
                "timestamp": row[3],
                "emotional_valence": row[4],
                "importance": row[5],
                "access_count": row[6],
            }
            for row in rows
        ]

    # ==================== Procedures ====================

    async def save_procedure(
        self,
        procedure_id: str,
        name: str,
        condition: str,
        action: str,
        strength: float = 0.5,
        use_count: int = 0,
        success_count: int = 0,
    ) -> str:
        """Save a procedural memory rule (upsert)."""
        created_at = time_module.time()
        sql = (
            (
                "INSERT INTO procedures "
                "(procedure_id, name, condition, action, strength, use_count, success_count, created_at) "
                f"VALUES ({_placeholders(8)}) "
                "ON CONFLICT (procedure_id) DO UPDATE SET "
                "strength = EXCLUDED.strength, use_count = EXCLUDED.use_count, "
                "success_count = EXCLUDED.success_count, created_at = EXCLUDED.created_at"
            )
            if DRIVER == "postgres"
            else f"{UPSERT_SQLITE} INTO procedures "
            "(procedure_id, name, condition, action, strength, "
            " use_count, success_count, created_at) "
            f"VALUES ({_placeholders(8)})"
        )
        await self.execute(sql, (procedure_id, name, condition, action, strength, use_count, success_count, created_at))
        if DRIVER != "postgres":
            await self._connection.commit()
        return procedure_id

    async def load_procedures(self) -> List[Dict[str, Any]]:
        """Load all persisted procedures (strongest first)."""
        rows = await self.fetchall("SELECT * FROM procedures ORDER BY strength DESC")
        return [
            {
                "procedure_id": row[0],
                "name": row[1],
                "condition": row[2],
                "action": row[3],
                "strength": row[4],
                "use_count": row[5],
                "success_count": row[6],
                "created_at": row[7],
            }
            for row in rows
        ]

    # ==================== Brain States ====================

    async def save_brain_state(
        self,
        cycle_count: int,
        current_phase: str,
        active_concepts: Dict[str, float] | None = None,
        emotional_state: Dict[str, float] | None = None,
        last_input: str = "",
        last_output: str = "",
    ) -> None:
        """Save a brain state snapshot."""
        timestamp = time_module.time()
        active_json = json.dumps(active_concepts or {})
        emotion_json = json.dumps(emotional_state or {})

        await self.execute(
            "INSERT INTO brain_states "
            "(cycle_count, current_phase, active_concepts, emotional_state, last_input, last_output, timestamp) "
            f"VALUES ({_placeholders(7)})",
            (cycle_count, current_phase, active_json, emotion_json, last_input, last_output, timestamp),
        )
        if DRIVER != "postgres":
            await self._connection.commit()

    async def load_brain_states(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Load recent brain state snapshots (newest first)."""
        rows = await self.fetchall(
            "SELECT * FROM brain_states ORDER BY timestamp DESC LIMIT $1"
            if DRIVER == "postgres"
            else "SELECT * FROM brain_states ORDER BY timestamp DESC LIMIT ?",
            (limit,),
        )
        return [
            {
                "state_id": row[0],
                "cycle_count": row[1],
                "current_phase": row[2],
                "active_concepts": json.loads(row[3]) if row[3] else {},
                "emotional_state": json.loads(row[4]) if row[4] else {},
                "last_input": row[5],
                "last_output": row[6],
                "timestamp": row[7],
            }
            for row in rows
        ]
