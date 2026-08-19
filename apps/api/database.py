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

import asyncio
import json
import os
import time as time_module
import uuid
from pathlib import Path
from typing import Any, Dict, List, Mapping, Tuple

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
        resolved_url = db_url or _db_url()
        # The on-disk SQLite file path must match the resolved URL, otherwise
        # the legacy db_path default would silently write to the repo-level
        # ``data/misty_brain.db`` even when a test or deployment overrides
        # the URL (for example ``MISTY_DB_URL=sqlite:///test.db``).
        if resolved_url.startswith("sqlite:///"):
            self.db_path = db_path or resolved_url[len("sqlite:///") :]
        else:
            self.db_path = db_path or DEFAULT_DB_PATH
        self._url = resolved_url
        self._connection: Any = None
        # asyncpg connections cannot run overlapping operations; a single
        # lock serializes all queries when several tasks (chat route,
        # consolidation sink, sensor ingestion) share one connection.

        self._lock = asyncio.Lock()

    async def initialize(self) -> None:
        """Connect and apply the appropriate schema."""
        if DRIVER == "postgres":
            # statement_cache_size=0 is required when connecting through Supabase's
            # PgBouncer transaction-mode pool (port 6543), which cannot share
            # prepared statements across connections.
            self._connection = await asyncpg.connect(self._url, statement_cache_size=0)
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
            async with self._lock:
                return await self._connection.execute(sql, *params)
        return await self._connection.execute(sql, params)

    async def fetchall(self, sql: str, params: Tuple[Any, ...] = ()) -> List[Any]:
        """Driver-uniform fetch of all rows."""
        if DRIVER == "postgres":
            async with self._lock:
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

        if DRIVER == "postgres":
            # ``concepts`` has both a PRIMARY KEY (concept_id) and a UNIQUE
            # constraint on (name). A memory concept loaded from the database
            # keeps its original concept_id, so a plain ON CONFLICT
            # (concept_id) upsert fails with UniqueViolation when a *new*
            # concept happens to carry a name that already exists under a
            # different id. Update the existing row by name instead.
            try:
                async with self._lock:
                    await self._connection.execute(
                        "INSERT INTO concepts "
                        "(concept_id, name, concept_type, activation_level, "
                        "created_at, metadata) "
                        f"VALUES ({_placeholders(6)}) "
                        "ON CONFLICT (concept_id) DO UPDATE SET "
                        "name = EXCLUDED.name, concept_type = EXCLUDED.concept_type, "
                        "activation_level = EXCLUDED.activation_level, "
                        "created_at = EXCLUDED.created_at, metadata = EXCLUDED.metadata",
                        concept_id,
                        name,
                        concept_type,
                        activation_level,
                        created_at,
                        metadata_json,
                    )
            except asyncpg.UniqueViolationError:
                # A row with this name exists under a *different* concept_id.
                # Keep its concept_id so relation edges (FK'd to it) are not
                # orphaned; merge the metadata under the existing row.
                async with self._lock:
                    existing = await self._connection.fetchrow(
                        "SELECT concept_id, metadata FROM concepts WHERE name = $1",
                        name,
                    )
                    if existing is None:
                        raise
                    existing_meta = json.loads(existing["metadata"]) if existing["metadata"] else {}
                    existing_meta.update(json.loads(metadata_json))
                    await self._connection.execute(
                        "UPDATE concepts SET "
                        "concept_type = $2, activation_level = $3, "
                        "created_at = $4, metadata = $5 "
                        "WHERE name = $1",
                        name,
                        concept_type,
                        activation_level,
                        created_at,
                        json.dumps(existing_meta),
                    )
            return
        sql = (
            f"{UPSERT_SQLITE} INTO concepts "
            f"(concept_id, name, concept_type, activation_level, created_at, metadata) "
            f"VALUES ({_placeholders(6)})"
        )
        await self._connection.execute(
            sql,
            (concept_id, name, concept_type, activation_level, created_at, metadata_json),
        )
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

    async def update_relation(
        self,
        relation_id: str,
        *,
        weight: float,
        confidence: float,
    ) -> bool:
        """Update a persisted relation's mutable state by durable ID.

        Returns ``True`` only when the durable row exists. Callers can then
        advance their persistence cache after the write has succeeded.
        """
        sql = (
            "UPDATE relations SET weight = $1, confidence = $2 WHERE relation_id = $3"
            if DRIVER == "postgres"
            else "UPDATE relations SET weight = ?, confidence = ? WHERE relation_id = ?"
        )
        result = await self.execute(sql, (float(weight), float(confidence), relation_id))
        if DRIVER == "postgres":
            return str(result).rsplit(" ", 1)[-1] != "0"
        await self._connection.commit()
        return bool(result.rowcount)

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

    async def load_episodes(self, limit: int | None = 100) -> List[Dict[str, Any]]:
        """Load episodes newest first, optionally without a row limit.

        ``limit=None`` is the interim full-history path used to hydrate
        semantic facts while they still share the generic episode table.
        Integer limits retain the established recent-episode behavior. A
        dedicated semantic-fact table should eventually replace this scan.
        """
        if limit is None:
            rows = await self.fetchall("SELECT * FROM episodes ORDER BY timestamp DESC")
        else:
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

    # ==================== Training Packages (Phase 12) ====================

    async def save_training_package(self, package: Mapping[str, Any]) -> None:
        """Persist a versioned training package to the durable catalog.

        The catalog is append-friendly: the same ``package_id`` keeps every
        registered version so the registry can reconstruct full package
        history after a process restart. Registration succeeds even when
        persistence is unreachable (the in-memory registry remains the
        runtime source of truth), but callers should check the returned
        dict for ``persisted: false``.
        """
        package_id: str = str(package.get("package_id", "")).strip()
        version: int = int(package.get("version", 1))
        department: str = str(package.get("department", "general") or "general")
        languages: List[str] = list(package.get("languages", []) or [])
        provenance: str = str(package.get("provenance", "") or "")
        source_ref = (package.get("source") or {}) if isinstance(package.get("source"), Mapping) else {}
        timestamp = time_module.time()
        payload = dict(package)
        payload.setdefault("package_id", package_id)
        payload.setdefault("version", version)
        payload.setdefault("department", department)
        payload.setdefault("languages", languages)
        payload.setdefault("registered_at", timestamp)
        payload.setdefault("updated_at", timestamp)
        package_json = json.dumps(payload, ensure_ascii=False)
        languages_json = json.dumps(languages, ensure_ascii=False)
        if source_ref.get("url") or source_ref.get("name"):
            provenance = provenance or str(source_ref.get("url") or source_ref.get("name"))
        try:
            if DRIVER == "postgres":
                async with self._lock:
                    await self._connection.execute(
                        "INSERT INTO training_packages "
                        "(package_id, version, department, languages, package_json, "
                        "provenance, status, registered_at, updated_at) "
                        f"VALUES ({_placeholders(9)}) "
                        "ON CONFLICT (package_id, version) DO UPDATE SET "
                        "package_json = EXCLUDED.package_json, updated_at = EXCLUDED.updated_at",
                        package_id,
                        version,
                        department,
                        languages_json,
                        package_json,
                        provenance,
                        "active",
                        timestamp,
                        timestamp,
                    )
            else:
                await self.execute(
                    f"{UPSERT_SQLITE} INTO training_packages "
                    "(package_id, version, department, languages, package_json, "
                    "provenance, status, registered_at, updated_at) "
                    f"VALUES ({_placeholders(9)})",
                    (
                        package_id,
                        version,
                        department,
                        languages_json,
                        package_json,
                        provenance,
                        "active",
                        timestamp,
                        timestamp,
                    ),
                )
                await self._connection.commit()
        except Exception:
            raise

    async def load_training_packages(
        self,
        department: str | None = None,
    ) -> List[Dict[str, Any]]:
        """Load the durable training package catalog (newest version first)."""
        base = (
            "SELECT package_id, version, department, languages, package_json, "
            "provenance, status, registered_at, updated_at "
            "FROM training_packages"
        )
        if DRIVER == "postgres":
            sql = f"{base} ORDER BY registered_at DESC"
            rows = (
                await self.fetchall(sql)
                if department is None
                else await self.fetchall(
                    f"{base} WHERE department = $1 ORDER BY registered_at DESC",
                    (department,),
                )
            )
        else:
            sql = f"{base} ORDER BY registered_at DESC"
            rows = (
                await self.fetchall(sql)
                if department is None
                else await self.fetchall(
                    f"{base} WHERE department = ? ORDER BY registered_at DESC",
                    (department,),
                )
            )
        result: List[Dict[str, Any]] = []
        for row in rows:
            parsed = (
                row
                if isinstance(row, dict)
                else {
                    "package_id": row[0],
                    "version": row[1],
                    "department": row[2],
                    "languages": row[3],
                    "package_json": row[4],
                    "provenance": row[5],
                    "status": row[6],
                    "registered_at": row[7],
                    "updated_at": row[8],
                }
            )
            languages = parsed["languages"]
            if isinstance(languages, str):
                languages = json.loads(languages)
            package_json = parsed["package_json"]
            if isinstance(package_json, str):
                package_json = json.loads(package_json)
            result.append(
                {
                    "package_id": parsed["package_id"],
                    "version": int(parsed["version"]),
                    "department": str(parsed["department"]),
                    "languages": languages,
                    "package": package_json,
                    "provenance": str(parsed["provenance"] or ""),
                    "status": str(parsed["status"]),
                    "registered_at": float(parsed["registered_at"]),
                    "updated_at": float(parsed["updated_at"]),
                }
            )
        return result

    # ==================== User Memory (Phase 40) ====================
    async def save_user_memory(self, user_id: str, payload: Mapping[str, Any]) -> None:
        """Upsert per-user memory rows (profile summary, facts, episodes).

        ``payload`` carries ``kind`` (profile|fact|episode), ``memory_key``
        and ``memory_json`` (a plain dict — JSON-encoded here so both
        drivers store the same shape; PostgreSQL's JSONB column accepts
        text automatically).
        """
        timestamp = time_module.time()
        memory_json = json.dumps(payload.get("memory_json", {}))
        kind = str(payload.get("kind", "episode"))
        memory_key = str(payload.get("memory_key", ""))
        if DRIVER == "postgres":
            await self.execute(
                "INSERT INTO misty_user_memory "
                "(user_id, memory_kind, memory_key, memory_json, updated_at) "
                f"VALUES ({_placeholders(5)}) "
                "ON CONFLICT (user_id, memory_kind, memory_key) "
                "DO UPDATE SET memory_json = EXCLUDED.memory_json, "
                "updated_at = EXCLUDED.updated_at",
                (user_id, kind, memory_key, memory_json, timestamp),
            )
        else:
            await self.execute(
                f"{UPSERT_SQLITE} INTO misty_user_memory "
                "(user_id, memory_kind, memory_key, memory_json, updated_at) "
                f"VALUES ({_placeholders(5)})",
                (user_id, kind, memory_key, memory_json, timestamp),
            )
            await self._connection.commit()

    async def load_user_memory(self, user_id: str) -> List[Dict[str, Any]]:
        """Load all persisted memory rows for one user (cold-start rebuild
        of the in-memory user memory layer)."""
        rows = await self.fetchall(
            "SELECT memory_kind, memory_key, memory_json FROM misty_user_memory "
            "WHERE user_id = $1 ORDER BY updated_at DESC LIMIT 500"
            if DRIVER == "postgres"
            else "SELECT memory_kind, memory_key, memory_json FROM misty_user_memory "
            "WHERE user_id = ? ORDER BY updated_at DESC LIMIT 500",
            (user_id,),
        )
        return [
            {
                "kind": row[0],
                "memory_key": row[1],
                "memory_json": json.loads(row[2]) if row[2] else {},
            }
            for row in rows
        ]
