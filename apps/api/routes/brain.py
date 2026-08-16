"""
Brain State Routes.

GET /api/brain/state - Current brain state snapshot
GET /api/brain/concepts - All concepts in knowledge graph
GET /api/brain/graph - Full graph structure (nodes + edges)
"""

from typing import Any, Dict, List

from fastapi import APIRouter, Request
from pydantic import BaseModel

router = APIRouter()


class BrainStateResponse(BaseModel):
    """Current brain state snapshot."""

    cycle_count: int
    user_name: Any
    concepts: int
    relations: int
    working_memory_size: int
    episodic_memories: int
    semantic_facts: int
    emotional_state: Dict[str, float]
    active_concepts: Dict[str, float]
    performance: Dict[str, Any]


class ConceptResponse(BaseModel):
    """A single concept from the knowledge graph."""

    concept_id: str
    name: str
    concept_type: str
    activation_level: float
    created_at: float
    metadata: Dict[str, Any]


class RelationResponse(BaseModel):
    """A relation (edge) in the knowledge graph."""

    source: str
    target: str
    relation_type: str
    weight: float
    confidence: float


class GraphResponse(BaseModel):
    """Full graph structure with nodes and edges."""

    nodes: List[ConceptResponse]
    edges: List[RelationResponse]
    num_nodes: int
    num_edges: int


@router.get("/state", response_model=BrainStateResponse)
async def get_brain_state(request: Request) -> BrainStateResponse:
    """Get the current brain state snapshot."""
    brain = request.app.state.brain
    state = brain.get_state()
    return BrainStateResponse(**state)


@router.get("/concepts", response_model=List[ConceptResponse])
async def get_concepts(request: Request) -> List[ConceptResponse]:
    """Get all concepts currently in the knowledge graph."""
    brain = request.app.state.brain
    concepts = [
        ConceptResponse(
            concept_id=concept.concept_id,
            name=concept.name,
            concept_type=concept.concept_type,
            activation_level=concept.activation_level,
            created_at=concept.created_at,
            metadata=concept.metadata,
        )
        for concept in brain.concept_graph._concepts.values()
    ]
    return concepts


@router.get("/graph", response_model=GraphResponse)
async def get_graph(request: Request) -> GraphResponse:
    """Get the full knowledge graph structure (nodes + edges)."""
    brain = request.app.state.brain
    graph = brain.concept_graph

    # Collect nodes
    nodes = [
        ConceptResponse(
            concept_id=concept.concept_id,
            name=concept.name,
            concept_type=concept.concept_type,
            activation_level=concept.activation_level,
            created_at=concept.created_at,
            metadata=concept.metadata,
        )
        for concept in graph._concepts.values()
    ]

    # Collect edges from NetworkX graph
    edges = []
    for source, target, data in graph.graph.edges(data=True):
        edges.append(
            RelationResponse(
                source=source,
                target=target,
                relation_type=data.get("relation_type", "related_to"),
                weight=data.get("weight", 1.0),
                confidence=data.get("confidence", 1.0),
            )
        )

    return GraphResponse(
        nodes=nodes,
        edges=edges,
        num_nodes=len(nodes),
        num_edges=len(edges),
    )
