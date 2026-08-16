"""
Chat Route.

POST /api/chat endpoint that accepts user messages,
processes them through the Brain cognitive cycle, and
returns the response with metadata.
"""

from typing import Any, Dict

from fastapi import APIRouter, Request
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


@router.post("/chat", response_model=ChatResponse)
async def chat(request: Request, body: ChatRequest) -> ChatResponse:
    """Process a message through the Brain cognitive cycle.

    The brain will:
    1. Parse the input using rule-based NLU
    2. Run through all cognitive phases (observe, interpret, recall, etc.)
    3. Create/update concepts and relations as needed
    4. Generate a response without any LLM

    Args:
        request: The FastAPI request object (contains app state).
        body: The chat request with the user's message.

    Returns:
        ChatResponse with the brain's response and metadata.
    """
    brain = request.app.state.brain
    database = request.app.state.database

    # Process through cognitive cycle
    result = brain.process(body.message)

    # Persist brain state to database
    state = brain.get_state()
    await database.save_brain_state(
        cycle_count=state["cycle_count"],
        current_phase="idle",
        active_concepts=state.get("active_concepts"),
        emotional_state=state.get("emotional_state"),
        last_input=body.message,
        last_output=result["response"],
    )

    # Persist any new concepts to database
    for concept in brain.concept_graph._concepts.values():
        await database.save_concept(
            concept_id=concept.concept_id,
            name=concept.name,
            concept_type=concept.concept_type,
            activation_level=concept.activation_level,
            created_at=concept.created_at,
            metadata=concept.metadata,
        )

    # Persist knowledge graph relations (edges) so learned knowledge survives
    # server restarts, matching the persistence already done for concepts
    for rel in brain.concept_graph.get_all_relations():
        try:
            await database.save_relation(
                source_id=rel["source_id"],
                target_id=rel["target_id"],
                relation_type=rel["relation_type"],
                weight=rel["weight"],
                confidence=rel["confidence"],
            )
        except Exception:
            pass

    return ChatResponse(
        response=result["response"],
        processing_time=result["processing_time"],
        cycle_count=result["cycle_count"],
        active_concepts=result["active_concepts"],
        emotional_state=result["emotional_state"],
        brain_state=result["brain_state"],
    )
