"""
Database Persistence Layer.

Provides async SQLite operations using aiosqlite for persisting
concepts, relations, episodes, and brain states. Initializes
schema from database/schema.sql.
"""

import json
import os
import time as time_module
import uuid
from pathlib import Path
from typing import Any, Dict, List

import aiosqlite

# Default database path
DEFAULT_DB_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "data",
    "misty_brain.db",
)

# Schema file path
SCHEMA_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "database",
    "schema.sql",
)


class Database:
    """Async SQLite persistence layer for the MISTY brain.

    Handles saving and loading of concepts, relations, episodes,
    and brain state snapshots.

    Attributes:
        db_path: Path to the SQLite database file.
        _connection: Active aiosqlite connection.
    """

    def __init__(self, db_path: str | None = None) -> None:
        """Initialize with database path.

        Args:
            db_path: Path to SQLite database file. Defaults to data/misty_brain.db.
        """
        self.db_path = db_path or DEFAULT_DB_PATH
        self._connection: aiosqlite.Connection | None = None

    async def initialize(self) -> None:
        """Initialize database: create directory, connect, and apply schema."""
        # Ensure data directory exists
        db_dir = os.path.dirname(self.db_path)
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)

        # Connect to database
        self._connection = await aiosqlite.connect(self.db_path)
        self._connection.row_factory = aiosqlite.Row

        # Apply schema
        schema_path = Path(SCHEMA_PATH)
        if schema_path.exists():
            schema_sql = schema_path.read_text(encoding="utf-8")
            await self._connection.executescript(schema_sql)
            await self._connection.commit()

    async def close(self) -> None:
        """Close the database connection."""
        if self._connection:
            await self._connection.close()
            self._connection = None

    @property
    def connection(self) -> aiosqlite.Connection:
        """Get the active connection, raising if not initialized."""
        if self._connection is None:
            raise RuntimeError("Database not initialized. Call initialize() first.")
        return self._connection

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
        """Save or update a concept in the database.

        Args:
            concept_id: Unique concept identifier.
            name: Concept name.
            concept_type: Type category (Person, Entity, etc.).
            activation_level: Current activation level.
            created_at: Creation timestamp.
            metadata: Additional properties as dict.
        """
        created_at = created_at or time_module.time()
        metadata_json = json.dumps(metadata or {})

        await self.connection.execute(
            """INSERT OR REPLACE INTO concepts
               (concept_id, name, concept_type, activation_level, created_at, metadata)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (
                concept_id,
                name,
                concept_type,
                activation_level,
                created_at,
                metadata_json,
            ),
        )
        await self.connection.commit()

    async def load_concepts(self) -> List[Dict[str, Any]]:
        """Load all concepts from the database.

        Returns:
            List of concept dictionaries.
        """
        cursor = await self.connection.execute("SELECT * FROM concepts")
        rows = await cursor.fetchall()
        concepts = [
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
        return concepts

    async def get_concept_by_name(self, name: str) -> Dict[str, Any] | None:
        """Load a concept by its name.

        Args:
            name: Concept name to look up.

        Returns:
            Concept dictionary or None.
        """
        cursor = await self.connection.execute("SELECT * FROM concepts WHERE name = ?", (name,))
        row = await cursor.fetchone()
        if row:
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
        """Save a relation between two concepts.

        Args:
            source_id: Source concept ID.
            target_id: Target concept ID.
            relation_type: Type of relationship.
            weight: Connection strength.
            confidence: Confidence in this relation.
            metadata: Additional properties.

        Returns:
            The relation ID.
        """
        relation_id = str(uuid.uuid4())[:8]
        created_at = time_module.time()
        metadata_json = json.dumps(metadata or {})

        await self.connection.execute(
            """INSERT INTO relations
               (relation_id, source_id, target_id, relation_type, weight, confidence, created_at, metadata)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                relation_id,
                source_id,
                target_id,
                relation_type,
                weight,
                confidence,
                created_at,
                metadata_json,
            ),
        )
        await self.connection.commit()
        return relation_id

    async def load_relations(self) -> List[Dict[str, Any]]:
        """Load all relations from the database.

        Returns:
            List of relation dictionaries.
        """
        cursor = await self.connection.execute("SELECT * FROM relations")
        rows = await cursor.fetchall()
        relations = [
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
        return relations

    # ==================== Episodes ====================

    async def save_episode(
        self,
        content: str,
        context: Dict[str, Any] | None = None,
        emotional_valence: float = 0.0,
        importance: float = 0.5,
    ) -> str:
        """Save an episodic memory.

        Args:
            content: The event content.
            context: Contextual information.
            emotional_valence: Emotional association.
            importance: Importance score.

        Returns:
            The episode ID.
        """
        episode_id = str(uuid.uuid4())[:8]
        timestamp = time_module.time()
        context_json = json.dumps(context or {})

        await self.connection.execute(
            """INSERT INTO episodes
               (episode_id, content, context, timestamp, emotional_valence, importance)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (
                episode_id,
                content,
                context_json,
                timestamp,
                emotional_valence,
                importance,
            ),
        )
        await self.connection.commit()
        return episode_id

    async def load_episodes(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Load recent episodes from the database.

        Args:
            limit: Maximum number of episodes to load.

        Returns:
            List of episode dictionaries (newest first).
        """
        cursor = await self.connection.execute("SELECT * FROM episodes ORDER BY timestamp DESC LIMIT ?", (limit,))
        rows = await cursor.fetchall()
        episodes = [
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
        return episodes

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
        """Save a procedural memory rule.

        Uses INSERT OR REPLACE so re-saving an existing procedure updates
        its learned statistics instead of failing on duplicate keys.
        """
        created_at = time_module.time()
        await self.connection.execute(
            """INSERT OR REPLACE INTO procedures
               (procedure_id, name, condition, action, strength,
                use_count, success_count, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (procedure_id, name, condition, action, strength, use_count, success_count, created_at),
        )
        await self.connection.commit()
        return procedure_id

    async def load_procedures(self) -> List[Dict[str, Any]]:
        """Load all persisted procedures.

        Returns:
            List of procedure dictionaries.
        """
        cursor = await self.connection.execute("SELECT * FROM procedures ORDER BY strength DESC")
        rows = await cursor.fetchall()
        procedures = [
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
        return procedures

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
        """Save a brain state snapshot.

        Args:
            cycle_count: Current cognitive cycle count.
            current_phase: Current processing phase.
            active_concepts: Map of concept_id to activation level.
            emotional_state: Current emotional state values.
            last_input: Most recent input text.
            last_output: Most recent output text.
        """
        timestamp = time_module.time()
        active_json = json.dumps(active_concepts or {})
        emotion_json = json.dumps(emotional_state or {})

        await self.connection.execute(
            """INSERT INTO brain_states
               (cycle_count, current_phase, active_concepts, emotional_state, last_input, last_output, timestamp)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                cycle_count,
                current_phase,
                active_json,
                emotion_json,
                last_input,
                last_output,
                timestamp,
            ),
        )
        await self.connection.commit()

    async def load_brain_states(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Load recent brain state snapshots.

        Args:
            limit: Maximum number of states to load.

        Returns:
            List of brain state dictionaries (newest first).
        """
        cursor = await self.connection.execute("SELECT * FROM brain_states ORDER BY timestamp DESC LIMIT ?", (limit,))
        rows = await cursor.fetchall()
        states = [
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
        return states
