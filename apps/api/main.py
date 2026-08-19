"""
MISTY FastAPI Application.

Main application entry point with lifespan handler that initializes
the Brain instance and SQLite database. Provides REST and WebSocket
endpoints for the cognitive system.

Run with:
    uvicorn apps.api.main:app --reload
"""

import asyncio
import json
import logging
import os
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from apps.api.database import Database
from apps.api.routes.actuators import router as actuators_router
from apps.api.routes.brain import router as brain_router
from apps.api.routes.chat import router as chat_router
from apps.api.routes.media import router as media_router
from apps.api.routes.sensors import router as sensors_router
from apps.api.routes.training import router as training_router
from apps.api.routes.voice import router as voice_router
from apps.api.routes.voice_stream import router as voice_stream_router
from apps.api.websocket.brain_stream import router as ws_router
from brain.cognition import AutonomousInnerLoop, InnerLoopConfig
from brain.core.brain import Brain
from brain.learning.consolidation import ConsolidationEvent
from brain.memory.procedural import Procedure

logger = logging.getLogger(__name__)


async def _restore_persistent_knowledge(brain: Brain, database: Database) -> dict[str, Any]:
    """Hydrate durable knowledge and return pre-request persistence indexes."""
    indexes: dict[str, Any] = {
        "concept_ids": set(),
        "relation_keys": set(),
        "relation_states": {},
        "fact_keys": set(),
    }
    try:
        persisted_concepts = await database.load_concepts()
        indexes["concept_ids"] = {item["concept_id"] for item in persisted_concepts}
        for item in persisted_concepts:
            from brain.graph.concepts import Concept

            concept = Concept(
                name=item["name"],
                concept_type=item["concept_type"],
                concept_id=item["concept_id"],
                activation_level=item.get("activation_level", 0.0),
                created_at=item.get("created_at"),
                metadata=item.get("metadata", {}),
            )
            existing_by_name = brain.concept_graph.get_concept_by_name(item["name"])
            if existing_by_name is not None:
                brain.concept_graph.replace_concept(existing_by_name.concept_id, concept)
            elif not brain.concept_graph.get_concept(item["concept_id"]):
                brain.concept_graph.add_concept(concept)

        persisted_relations = await database.load_relations()
        indexes["relation_keys"] = {
            (item["source_id"], item["target_id"], item["relation_type"]) for item in persisted_relations
        }
        indexes["relation_states"] = {
            (item["source_id"], item["target_id"], item["relation_type"]): {
                "relation_id": item["relation_id"],
                "weight": float(item.get("weight", 1.0)),
                "confidence": float(item.get("confidence", 1.0)),
            }
            for item in persisted_relations
        }
        brain.concept_graph.load_relations(persisted_relations)

        # Interim full scan: semantic facts currently share the episode log.
        # A dedicated semantic-fact table should replace this unbounded path.
        persisted_episodes = await database.load_episodes(limit=None)
        for item in persisted_episodes:
            try:
                content = json.loads(item["content"])
            except (TypeError, json.JSONDecodeError):
                continue
            if not isinstance(content, dict) or content.get("type") != "semantic_fact":
                continue
            subject = str(content.get("subject", ""))
            predicate = str(content.get("predicate", ""))
            obj = str(content.get("obj", ""))
            if not subject or not predicate or not obj:
                continue
            fact_key = f"{subject}:{predicate}:{obj}"
            indexes["fact_keys"].add(fact_key)
            if fact_key not in brain.semantic_memory.facts:
                brain.semantic_memory.store_fact(
                    subject=subject,
                    predicate=predicate,
                    obj=obj,
                    confidence=float(item.get("importance", 0.5)),
                    source=str(item.get("context", {}).get("source", "persistent_storage")),
                )

        persisted_procedures = await database.load_procedures()
        for item in persisted_procedures:
            proc = Procedure(
                procedure_id=item["procedure_id"],
                name=item["name"],
                condition=item["condition"],
                action=item["action"],
                strength=item.get("strength", 0.5),
                use_count=item.get("use_count", 0),
                success_count=item.get("success_count", 0),
            )
            brain.procedural_memory.procedures[proc.procedure_id] = proc

        logger.info(
            "Restored %s concepts, %s relations, %s semantic facts and %s procedures",
            len(persisted_concepts),
            len(persisted_relations),
            len(indexes["fact_keys"]),
            len(persisted_procedures),
        )
    except Exception:
        logger.exception("Persistent knowledge restore failed; continuing with in-memory knowledge")
    return indexes


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Initialize the cognitive runtime and drain persistence on shutdown."""
    brain = Brain()
    database = Database()
    await database.initialize()

    persistence_tasks: set[asyncio.Task] = set()
    app.state.persistence_tasks = persistence_tasks
    # Backward-compatible alias used by route-level tests and diagnostics.
    app.state.pending_chat_persistence_tasks = persistence_tasks
    app.state.chat_persistence_lock = asyncio.Lock()

    def _task_completed(task: asyncio.Task) -> None:
        persistence_tasks.discard(task)
        if task.cancelled():
            return
        try:
            error = task.exception()
        except asyncio.CancelledError:
            return
        if error is not None:
            logger.error("Background persistence task failed: %s", error)

    def _safe_schedule(coro_factory) -> None:
        """Schedule lazily so no coroutine is created without a running loop."""
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            return
        try:
            task = loop.create_task(coro_factory())
        except Exception:
            logger.exception("Could not schedule persistence task")
            return
        persistence_tasks.add(task)
        task.add_done_callback(_task_completed)

    async def _consolidation_sink(event: ConsolidationEvent) -> None:
        content = json.dumps(event.content) if isinstance(event.content, dict) else str(event.content)
        await database.save_episode(
            content=content,
            context=event.context,
            emotional_valence=event.importance,
            importance=event.importance,
        )

    def _consolidation_sink_sync(event: ConsolidationEvent) -> None:
        _safe_schedule(lambda: _consolidation_sink(event))

    brain.consolidator.persistence_sink = _consolidation_sink_sync

    _original_store = brain.procedural_memory.store

    def _procedure_save(proc: Procedure):
        return database.save_procedure(
            procedure_id=proc.procedure_id,
            name=proc.name,
            condition=proc.condition,
            action=proc.action,
            strength=proc.strength,
            use_count=proc.use_count,
            success_count=proc.success_count,
        )

    def _persisting_store(name: str, condition: str, action: str, strength: float = 0.5) -> Procedure:
        proc = _original_store(name, condition, action, strength)
        _safe_schedule(lambda: _procedure_save(proc))
        return proc

    brain.procedural_memory.store = _persisting_store  # type: ignore[method-assign]

    _original_reinforce = Procedure.reinforce

    def _persisting_reinforce(proc: Procedure, success: bool, amount: float = 0.1) -> None:
        _original_reinforce(proc, success, amount)
        _safe_schedule(lambda: _procedure_save(proc))

    Procedure.reinforce = _persisting_reinforce  # type: ignore[method-assign]

    indexes = await _restore_persistent_knowledge(brain, database)
    # These indexes describe durable startup state, not the graph after the
    # first request. Seed and first-turn knowledge therefore persist together.
    app.state.persisted_concept_ids = set(indexes["concept_ids"])
    app.state.persisted_relation_keys = set(indexes["relation_keys"])
    app.state.persisted_relation_state = {key: dict(value) for key, value in indexes["relation_states"].items()}
    app.state.persisted_fact_keys = set(indexes["fact_keys"])

    warmup_complete = False
    try:
        brain.process(" ")
        warmup_complete = True
    except Exception:
        logger.exception("Brain warmup failed; the first request will retry")
    app.state.warmup_complete = warmup_complete
    app.state.brain = brain
    app.state.database = database

    autonomous_task = None
    autonomy_enabled = os.getenv("MISTY_AUTONOMY_ENABLED", "true").casefold() == "true"
    if autonomy_enabled:
        interval = max(30.0, float(os.getenv("MISTY_AUTONOMY_INTERVAL_SECONDS", "300")))
        inner_loop = AutonomousInnerLoop(
            brain.autonomous_reflection_tick,
            InnerLoopConfig(interval_seconds=interval, max_tick_seconds=1.0),
        )
        app.state.inner_loop = inner_loop
        autonomous_task = asyncio.create_task(inner_loop.run())

    try:
        yield
    finally:
        Procedure.reinforce = _original_reinforce  # type: ignore[method-assign]
        brain.procedural_memory.store = _original_store  # type: ignore[method-assign]
        if autonomous_task is not None:
            autonomous_task.cancel()
            await asyncio.gather(autonomous_task, return_exceptions=True)
        # Drain every managed write before closing the shared connection.
        while persistence_tasks:
            pending = list(persistence_tasks)
            results = await asyncio.gather(*pending, return_exceptions=True)
            for error in results:
                if isinstance(error, Exception) and not isinstance(error, asyncio.CancelledError):
                    logger.error("Persistence task failed during shutdown: %s", error)
        await database.close()


# Create FastAPI application
app = FastAPI(
    title="MISTY Brain API",
    description=(
        "REST and WebSocket API for the MISTY Artificial Cognitive System. "
        "No LLM dependency - pure spiking neural network, knowledge graph, "
        "and cognitive cycle processing."
    ),
    version="0.1.0",
    lifespan=lifespan,
)

# Configure CORS for frontends: local dev, production Vercel deployments,
# and managed Manus browser previews. The regex is deliberately limited to
# the Expo web-preview host shape rather than allowing arbitrary origins.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://misty-ai-web.vercel.app",
        "https://misty-ai.vercel.app",
        "https://misty-ai-web-tophyint-9993s-projects.vercel.app",
        "https://misty-ai-4h0xp8q49-tophyint-9993s-projects.vercel.app",
        "https://misty-ai-59nxmmfsm-tophyint-9993s-projects.vercel.app",
    ],
    allow_origin_regex=r"https://8081-[a-z0-9-]+\.sg1\.manus\.computer",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(chat_router, prefix="/api")
app.include_router(media_router, prefix="/api")
app.include_router(voice_router, prefix="/api")
app.include_router(brain_router, prefix="/api/brain")
app.include_router(training_router, prefix="")
app.include_router(sensors_router, prefix="/api")
app.include_router(actuators_router, prefix="/api")
app.include_router(ws_router)
app.include_router(voice_stream_router)


@app.get("/")
async def root() -> dict:
    """Root endpoint - health check and API info."""
    return {
        "name": "MISTY Brain API",
        "version": "0.1.0",
        "status": "running",
        "description": "Artificial Cognitive System - No LLM dependency",
    }


@app.get("/health")
async def health_check() -> dict:
    """Health check endpoint with cold-start readiness status.

    ``status`` is ``warm`` once the startup warmup cycle has run, so
    orchestration (Render readiness probe, smoke scripts) can distinguish
    an accepting-but-cold instance from one still booting.
    """
    ready = getattr(app.state, "warmup_complete", False)
    return {"status": "warm" if ready else "cold", "ready": ready}
