"""
Chat Route.

POST /api/chat endpoint that accepts user messages,
processes them through the Brain cognitive cycle, and
returns the response with metadata.
"""

import asyncio
import json
import logging
import re
from collections.abc import AsyncIterator
from typing import Any, Dict

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field, field_validator

router = APIRouter()
logger = logging.getLogger(__name__)


class ChatRequest(BaseModel):
    """Request body for the chat endpoint.

    Attributes:
        message: The user's text input (Bengali or English).
    """

    message: str = Field(
        ...,
        description="Text input to process through the cognitive system.",
        min_length=1,
        max_length=5000,
    )

    @field_validator("message")
    @classmethod
    def normalize_message(cls, value: str) -> str:
        """Preserve user language while rejecting accidental blank messages."""
        normalized = re.sub(r"\s+", " ", value).strip()
        if not normalized:
            raise ValueError("Message cannot be blank.")
        return normalized


class ChatResponse(BaseModel):
    """Response body from the chat endpoint.

    Attributes:
        response: The brain's text response.
        processing_time: Time taken to process (seconds).
        cycle_count: Total cognitive cycles executed.
        active_concepts: Currently activated concepts and their levels.
        emotional_state: Current emotional/motivational state.
        brain_state: Full brain state snapshot.
    """

    response: str
    processing_time: float
    cycle_count: int
    active_concepts: Dict[str, float]
    emotional_state: Dict[str, float]
    brain_state: Dict[str, Any]
    cognitive_workspace: Dict[str, Any] = Field(default_factory=dict)
    thought_trace: Dict[str, Any] = Field(default_factory=dict)
    self_model: Dict[str, Any] = Field(default_factory=dict)
    phase_timings_ms: Dict[str, float] = Field(default_factory=dict)
    grounding: Dict[str, Any] = Field(default_factory=dict)


def _ensure_persistence_indexes(app_state: Any) -> None:
    """Create empty indexes before a turn when startup did not provide them."""
    if not hasattr(app_state, "persisted_concept_ids"):
        app_state.persisted_concept_ids = set()
    if not hasattr(app_state, "persisted_relation_keys"):
        app_state.persisted_relation_keys = set()
    if not hasattr(app_state, "persisted_relation_state"):
        app_state.persisted_relation_state = {}
    if not hasattr(app_state, "persisted_fact_keys"):
        app_state.persisted_fact_keys = set()


def _track_persistence_task(app_state: Any, task: asyncio.Task[Any]) -> None:
    """Keep a strong task reference and report asynchronous write failures."""
    tasks = getattr(app_state, "persistence_tasks", None)
    if tasks is None:
        tasks = set()
        app_state.persistence_tasks = tasks
    app_state.pending_chat_persistence_tasks = tasks
    tasks.add(task)

    def _completed(done: asyncio.Task[Any]) -> None:
        tasks.discard(done)
        if done.cancelled():
            return
        try:
            error = done.exception()
        except asyncio.CancelledError:
            return
        if error is not None:
            logger.error("Background persistence task failed: %s", error)

    task.add_done_callback(_completed)


async def _persist_chat_state(app_state: Any, database: Any, brain: Any, message: str, result: Dict[str, Any]) -> None:
    """Persist state without allowing database latency/failure to block chat."""
    try:
        state = result.get("brain_state", {})
        await database.save_brain_state(
            cycle_count=state["cycle_count"],
            current_phase="idle",
            active_concepts=state.get("active_concepts"),
            emotional_state=state.get("emotional_state"),
            last_input=message,
            last_output=result["response"],
        )
        persistence_lock = getattr(app_state, "chat_persistence_lock", None)
        if persistence_lock is None:
            persistence_lock = asyncio.Lock()
            app_state.chat_persistence_lock = persistence_lock
        async with persistence_lock:
            persisted_concept_ids = app_state.persisted_concept_ids
            persisted_relation_keys = app_state.persisted_relation_keys
            persisted_fact_keys = app_state.persisted_fact_keys
            new_concepts = [
                concept
                for concept in brain.concept_graph._concepts.values()
                if concept.concept_id not in persisted_concept_ids
            ]
            await asyncio.gather(
                *(
                    database.save_concept(
                        concept_id=concept.concept_id,
                        name=concept.name,
                        concept_type=concept.concept_type,
                        activation_level=concept.activation_level,
                        created_at=concept.created_at,
                        metadata=concept.metadata,
                    )
                    for concept in new_concepts
                )
            )
            persisted_concept_ids.update(concept.concept_id for concept in new_concepts)

            persisted_relation_state = app_state.persisted_relation_state
            for rel in brain.concept_graph.get_all_relations():
                relation_key = (rel["source_id"], rel["target_id"], rel["relation_type"])
                relation_id = rel.get("relation_id")
                durable_state = persisted_relation_state.get(relation_key)

                if relation_key not in persisted_relation_keys:
                    try:
                        relation_id = await database.save_relation(
                            source_id=rel["source_id"],
                            target_id=rel["target_id"],
                            relation_type=rel["relation_type"],
                            weight=rel["weight"],
                            confidence=rel["confidence"],
                        )
                    except Exception as error:
                        logger.error("Relation persistence failed for %s: %s", relation_key, error)
                        continue
                    brain.concept_graph.attach_relation_id(
                        rel["source_id"],
                        rel["target_id"],
                        rel["relation_type"],
                        relation_id,
                    )
                    # Advance caches only after the insert succeeds.
                    persisted_relation_keys.add(relation_key)
                    persisted_relation_state[relation_key] = {
                        "relation_id": relation_id,
                        "weight": float(rel["weight"]),
                        "confidence": float(rel["confidence"]),
                    }
                    continue

                if durable_state is None:
                    # Compatibility for callers that seeded only the legacy
                    # key cache. Hydrated startup always supplies full state.
                    if relation_id:
                        persisted_relation_state[relation_key] = {
                            "relation_id": relation_id,
                            "weight": float(rel["weight"]),
                            "confidence": float(rel["confidence"]),
                        }
                    continue

                durable_id = relation_id or durable_state.get("relation_id")
                if relation_id is None and durable_id:
                    brain.concept_graph.attach_relation_id(
                        rel["source_id"],
                        rel["target_id"],
                        rel["relation_type"],
                        durable_id,
                    )
                weight_changed = float(rel["weight"]) != float(durable_state.get("weight", 1.0))
                confidence_changed = float(rel["confidence"]) != float(durable_state.get("confidence", 1.0))
                if not durable_id or not (weight_changed or confidence_changed):
                    continue
                try:
                    updated = await database.update_relation(
                        durable_id,
                        weight=float(rel["weight"]),
                        confidence=float(rel["confidence"]),
                    )
                except Exception as error:
                    logger.error("Relation update failed for %s: %s", relation_key, error)
                    continue
                if not updated:
                    logger.error("Relation update found no durable row for %s", relation_key)
                    continue
                # Advance mutable-state cache only after the update succeeds.
                persisted_relation_state[relation_key] = {
                    "relation_id": durable_id,
                    "weight": float(rel["weight"]),
                    "confidence": float(rel["confidence"]),
                }
            new_facts = [
                (key, fact) for key, fact in brain.semantic_memory.facts.items() if key not in persisted_fact_keys
            ]
            fact_results = await asyncio.gather(
                *(
                    database.save_episode(
                        content=json.dumps(
                            {
                                "type": "semantic_fact",
                                "subject": fact.subject,
                                "predicate": fact.predicate,
                                "obj": fact.obj,
                            }
                        ),
                        context={"source": fact.source},
                        importance=fact.confidence,
                    )
                    for _, fact in new_facts
                ),
                return_exceptions=True,
            )
            for (key, _), saved in zip(new_facts, fact_results, strict=True):
                if isinstance(saved, Exception):
                    logger.error("Semantic-fact persistence failed for %s: %s", key, saved)
                else:
                    persisted_fact_keys.add(key)
    except Exception:
        logger.exception("Chat-state persistence failed")


async def _process_chat_turn(request: Request, body: ChatRequest) -> ChatResponse:
    """Process one message and schedule state persistence.

    Phase 19: if the app is still booting (brain not attached) the chat
    endpoint answers 503 with a Retry-After header instead of crashing
    the worker; if the startup warmup has not run yet, it is executed
    lazily on the first request.
    """
    brain = getattr(request.app.state, "brain", None)
    if brain is None:
        raise HTTPException(
            status_code=503,
            detail="MISTY brain is still booting. Retry in a few seconds.",
            headers={"Retry-After": "3"},
        )
    app_state = request.app.state
    _ensure_persistence_indexes(app_state)
    database = app_state.database
    if not getattr(app_state, "warmup_complete", False):
        try:
            brain.process(" ")
        except Exception:  # Warmup failure must never break a user turn
            pass
        request.app.state.warmup_complete = True
    result = brain.process(body.message)
    response_text = str(result.get("response") or "").strip()
    result["response"] = response_text or "I need a moment to form that reply. Please try asking again."
    persistence_task = asyncio.create_task(_persist_chat_state(app_state, database, brain, body.message, result))
    _track_persistence_task(app_state, persistence_task)

    return ChatResponse(
        response=result["response"],
        processing_time=result["processing_time"],
        cycle_count=result["cycle_count"],
        active_concepts=result["active_concepts"],
        emotional_state=result["emotional_state"],
        brain_state=result["brain_state"],
        cognitive_workspace=result.get("cognitive_workspace", {}),
        thought_trace=result.get("thought_trace", {}),
        self_model=result.get("self_model", {}),
        phase_timings_ms=result.get("phase_timings_ms", {}),
        grounding=result.get("grounding", {}),
    )


def _chunk_response_text(text: str, words_per_chunk: int = 4) -> list[str]:
    """Split a reply at readable word boundaries for progressive rendering."""
    parts = re.findall(r"\S+\s*", text)
    if not parts:
        return []
    return ["".join(parts[index : index + words_per_chunk]) for index in range(0, len(parts), words_per_chunk)]


def _sse(event: str, data: dict[str, Any]) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


@router.post("/chat", response_model=ChatResponse)
async def chat(request: Request, body: ChatRequest) -> ChatResponse:
    """Process a message and return Misty's complete response as JSON."""
    return await _process_chat_turn(request, body)


@router.post("/chat/stream")
async def chat_stream(request: Request, body: ChatRequest) -> StreamingResponse:
    """Stream cognitive status followed by progressive response text via SSE."""

    async def event_generator() -> AsyncIterator[str]:
        yield _sse("status", {"status": "thinking"})
        # Let the client render the thinking state before the synchronous
        # cognitive cycle begins.
        await asyncio.sleep(0)

        try:
            result = await _process_chat_turn(request, body)
        except Exception:
            yield _sse("error", {"message": "Misty could not finish that reply. Please try again."})
            return

        yield _sse("status", {"status": "writing"})
        for chunk in _chunk_response_text(result.response):
            yield _sse("token", {"text": chunk})
            await asyncio.sleep(0.018)

        yield _sse(
            "done",
            {
                "processing_time": result.processing_time,
                "cycle_count": result.cycle_count,
            },
        )

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/training/catalog")
async def training_catalog(request: Request) -> Dict[str, Any]:
    """Read-only view of the durable versioned training package catalog."""
    database = getattr(request.app.state, "database", None)
    if database is None:
        return {"packages": [], "count": 0, "source": "not_ready"}
    try:
        packages = await database.load_training_packages()
    except Exception:
        packages = []
    return {"packages": packages, "count": len(packages), "source": "catalog"}
