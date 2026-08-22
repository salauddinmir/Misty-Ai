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
    # Phase 38: total retrievable facts (semantic + episodic) and the
    # confidence/uncertainty snapshot of the last processed turn (the
    # rolling emotional values decay each tick and would show 0%).
    memory_recall: int = 0
    last_confidence: float = 0.0
    last_uncertainty: float = 0.0
    # Phase 14: latest autonomous reflection tick audit snapshot
    # (tick_index, evidence_budget, evidence_count, elapsed_ms, outcome,
    # quarantined_candidates). Absent until the first tick has run.
    last_autonomous_tick: Dict[str, Any]
    # Phase 39: current self-assessment-driven learning roadmap (plan_id,
    # total_planned_topics, ranked items, topic_scores). None until the
    # brain has run its first gap-based planning cycle.
    learning_roadmap: Dict[str, Any] | None = None
    # Phase 40: per-user memory and personalization summary (user_count,
    # known_users, total_facts, total_episodes). Empty until the first
    # visitor has spoken to the brain.
    user_memory: Dict[str, Any] | None = None
    # Phase 42: fact-verification audit (verified_total, corroborated,
    # retracted, conflicted, single_source, recent verdicts).
    fact_verification: Dict[str, Any] | None = None
    # Phase 44: fact-aging audit (total_decisions, counts by action,
    # recent decay/prune decisions, half-life config). Empty until the
    # brain runs its first autonomous reflection tick.
    fact_aging: Dict[str, Any] | None = None
    # Phase 45: consolidation audit (total_decisions, counts by action,
    # recent rehearsal/merge/removal decisions, sweep config). Empty until
    # the brain runs its first autonomous reflection tick.
    consolidation: Dict[str, Any] | None = None
    # Phase 48: connection-based reasoning audit (total_derived, recent
    # derived facts, per-rule firing counts). Empty until the first turn
    # produces a derived conclusion.
    reasoning: Dict[str, Any] | None = None
    # Phase 49: autonomous learning audit — background gap-assessment
    # and web-learning events.
    autonomous_learning: Dict[str, Any] | None = None
    # Phase 41: self-correction audit (challenges_received,
    # corrections_accepted, last_correction event). Empty until the first
    # visitor challenges one of the brain's answers.
    self_correction: Dict[str, Any] | None = None
    # Phase 43: visitor id bound to the last cycle and the personal
    # facts/episodes that grounded its reply.
    current_user_id: str = "anon"
    personal_recall: Dict[str, Any] | None = None


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
    tick = state.get("last_autonomous_tick")
    state["last_autonomous_tick"] = tick if isinstance(tick, dict) else {}
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
