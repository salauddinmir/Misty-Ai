"""
Chat Route.

POST /api/chat endpoint that accepts user messages,
processes them through the Brain cognitive cycle, and
returns the response with metadata.
"""

import asyncio
import json
import re
from collections.abc import AsyncIterator
from typing import Any, Dict

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

router = APIRouter()


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
    grounding: Dict[str, Any] = Field(default_factory=dict)


async def _process_chat_turn(request: Request, body: ChatRequest) -> ChatResponse:
    """Process one message and persist the resulting cognitive state."""
    brain = request.app.state.brain
    database = request.app.state.database

    # Process through cognitive cycle
    result = brain.process(body.message)

    # Persist the brain snapshot every turn, but flush graph/fact records only
    # when they are new. The previous implementation re-inserted the complete
    # graph and all training facts after every message, which made a fast
    # deterministic brain appear slow over a network database.
    state = brain.get_state()
    await database.save_brain_state(
        cycle_count=state["cycle_count"],
        current_phase="idle",
        active_concepts=state.get("active_concepts"),
        emotional_state=state.get("emotional_state"),
        last_input=body.message,
        last_output=result["response"],
    )

    persistence_lock = getattr(app_state := request.app.state, "chat_persistence_lock", None)
    if persistence_lock is None:
        persistence_lock = asyncio.Lock()
        app_state.chat_persistence_lock = persistence_lock
    async with persistence_lock:
        if not hasattr(app_state, "persisted_concept_ids"):
            app_state.persisted_concept_ids = set(brain.concept_graph._concepts)
        if not hasattr(app_state, "persisted_relation_keys"):
            app_state.persisted_relation_keys = set()
        if not hasattr(app_state, "persisted_fact_keys"):
            app_state.persisted_fact_keys = set()

        # New concepts are persisted once; activation is already represented in
        # the per-turn brain_states snapshot and need not rewrite every node.
        new_concepts = [
            concept
            for concept in brain.concept_graph._concepts.values()
            if concept.concept_id not in app_state.persisted_concept_ids
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
        app_state.persisted_concept_ids.update(concept.concept_id for concept in new_concepts)

        # Relations are keyed by their endpoints and type so a chat turn cannot
        # create duplicate edges in PostgreSQL.
        new_relations = []
        for rel in brain.concept_graph.get_all_relations():
            relation_key = (rel["source_id"], rel["target_id"], rel["relation_type"])
            if relation_key not in app_state.persisted_relation_keys:
                new_relations.append((relation_key, rel))
        relation_results = await asyncio.gather(
            *(
                database.save_relation(
                    source_id=rel["source_id"],
                    target_id=rel["target_id"],
                    relation_type=rel["relation_type"],
                    weight=rel["weight"],
                    confidence=rel["confidence"],
                )
                for _, rel in new_relations
            ),
            return_exceptions=True,
        )
        for (relation_key, _), saved in zip(new_relations, relation_results, strict=True):
            if not isinstance(saved, Exception):
                app_state.persisted_relation_keys.add(relation_key)

        # Facts are flushed once per process and newly learned facts are picked
        # up on later turns. This preserves learning without repeated inserts.
        new_facts = [
            (key, fact) for key, fact in brain.semantic_memory.facts.items() if key not in app_state.persisted_fact_keys
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
            if not isinstance(saved, Exception):
                app_state.persisted_fact_keys.add(key)

    return ChatResponse(
        response=result["response"],
        processing_time=result["processing_time"],
        cycle_count=result["cycle_count"],
        active_concepts=result["active_concepts"],
        emotional_state=result["emotional_state"],
        brain_state=result["brain_state"],
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
