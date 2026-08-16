"""
MISTY FastAPI Application.

Main application entry point with lifespan handler that initializes
the Brain instance and SQLite database. Provides REST and WebSocket
endpoints for the cognitive system.

Run with:
    uvicorn apps.api.main:app --reload
"""

import json
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from apps.api.database import Database
from apps.api.routes.brain import router as brain_router
from apps.api.routes.chat import router as chat_router
from apps.api.websocket.brain_stream import router as ws_router
from brain.core.brain import Brain
from brain.learning.consolidation import ConsolidationEvent


async def _restore_persistent_knowledge(brain: Brain, database: Database) -> None:
    """Rebuild the brain's knowledge graph from the persisted database.

    Restores concepts (nodes) first, then relations (edges), so the brain
    remembers everything it learned in previous sessions instead of
    starting from a blank slate after every restart.
    """
    try:
        persisted_concepts = await database.load_concepts()
        for item in persisted_concepts:
            # Avoid duplicates if the brain already has a concept with this ID
            if not brain.concept_graph.get_concept(item["concept_id"]):
                from brain.graph.concepts import Concept

                concept = Concept(
                    name=item["name"],
                    concept_type=item["concept_type"],
                    concept_id=item["concept_id"],
                    activation_level=item.get("activation_level", 0.0),
                    created_at=item.get("created_at"),
                    metadata=item.get("metadata", {}),
                )
                brain.concept_graph.add_concept(concept)

        persisted_relations = await database.load_relations()
        for item in persisted_relations:
            brain.concept_graph.add_relation(
                source_id=item["source_id"],
                target_id=item["target_id"],
                relation_type=item["relation_type"],
                weight=item.get("weight", 1.0),
                confidence=item.get("confidence", 1.0),
            )

        print(f"Restored {len(persisted_concepts)} concepts and {len(persisted_relations)} relations from database")
    except Exception:
        print("No persisted knowledge to restore; starting with a blank brain")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan handler.

    Initializes Brain instance and database on startup,
    and cleans up resources on shutdown.
    """
    # Startup: Initialize brain and database
    brain = Brain()
    database = Database()
    await database.initialize()

    # Hook the consolidation engine into the database: consolidated items
    # above the importance threshold are flushed to SQLite immediately so
    # nothing is lost if the process exits before a shutdown hook runs.
    async def _consolidation_sink(event: ConsolidationEvent) -> None:
        # The episodes table stores arbitrary dict content as JSON, so both
        # facts and episodes flush there; the semantic memory already keeps
        # the structured fact in the running brain graph as well.
        content = json.dumps(event.content) if isinstance(event.content, dict) else str(event.content)
        await database.save_episode(
            content=content,
            context=event.context,
            emotional_valence=event.importance,
            importance=event.importance,
        )

    def _consolidation_sink_sync(event: ConsolidationEvent) -> None:
        # The consolidator is synchronous; schedule the flush on the event loop.
        import asyncio

        try:
            asyncio.get_running_loop()
        except RuntimeError:
            return
        asyncio.get_running_loop().create_task(_consolidation_sink(event))

    brain.consolidator.persistence_sink = _consolidation_sink_sync

    # Restore previously learned knowledge from the database so the brain
    # remembers concepts and relations across server restarts
    await _restore_persistent_knowledge(brain, database)

    # Store in app state for access in route handlers
    app.state.brain = brain
    app.state.database = database

    yield

    # Shutdown: Close database connection
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

# Configure CORS for frontend at localhost:3000
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(chat_router, prefix="/api")
app.include_router(brain_router, prefix="/api/brain")
app.include_router(ws_router)


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
    """Health check endpoint."""
    return {"status": "healthy"}
