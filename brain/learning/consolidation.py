"""
Memory Consolidation.

Transfers important information from working memory to long-term storage.
"""

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List

from brain.memory.episodic import EpisodicMemory
from brain.memory.semantic import SemanticMemory
from brain.memory.working import WorkingMemory
from brain.safety.policy import AutonomyPolicy, Decision, evaluate_learning


@dataclass
class ConsolidationEvent:
    """A single consolidation outcome passed to the persistence sink."""

    kind: str  # "episode" | "fact"
    content: Any
    context: Dict[str, Any]
    importance: float
    source: str = "working_memory"


@dataclass
class MemoryConsolidator:
    """Consolidates working memory to long-term storage.

    When a `persistence_sink` callback is provided, every consolidated
    item above the persistence threshold is also handed to the sink so
    the application layer (e.g. the SQLite database) can flush it in a
    batch instead of losing it when the process exits.
    """

    consolidation_threshold: float = 0.3
    consolidation_count: int = 0
    persistence_threshold: float = 0.5
    # Phase 14: per-cycle budget so a single consolidation pass cannot
    # silently rewrite large parts of durable memory.
    max_consolidations_per_cycle: int = 8
    # Phase 14: items above this threshold are routed through the learning
    # safety gate (evaluate_learning) before entering durable knowledge.
    safety_gate_threshold: float = 0.5
    persistence_sink: Callable[[ConsolidationEvent], None] | None = None
    consolidated_keys: set[str] = field(default_factory=set)
    # Phase 14: structured audit of this cycle's gate outcomes.
    rejected_candidates: List[Dict[str, Any]] = field(default_factory=list)

    def consolidate(
        self,
        working_memory: WorkingMemory,
        episodic_memory: EpisodicMemory,
        semantic_memory: SemanticMemory,
        *,
        policy: AutonomyPolicy | None = None,
    ) -> List[str]:
        """Consolidate active working memory items to long-term storage.

        Phase 14: consolidation is bounded by ``max_consolidations_per_cycle``
        and candidates whose importance meets ``safety_gate_threshold`` must
        pass ``evaluate_learning`` before they enter durable knowledge;
        anything that fails the gate is quarantined in ``rejected_candidates``
        instead of being stored.
        """
        policy = policy or AutonomyPolicy()
        consolidated: List[str] = []
        self.rejected_candidates = []

        for key, item in list(working_memory.items.items()):
            if key in self.consolidated_keys or item.activation < self.consolidation_threshold:
                continue
            # Budget enforcement: stop this cycle once the cap is reached.
            if len(consolidated) >= self.max_consolidations_per_cycle:
                break

            content = item.content
            candidate = {
                "confidence": float(item.activation),
                "observations": int(
                    content.get("observations", 1) if isinstance(content, dict) else 1
                ) + self.consolidation_count,
                "source_ref": content.get("source") if isinstance(content, dict) else None,
                "contradicts_existing": bool(isinstance(content, dict) and content.get("contradicts_existing", False)),
            }
            gated = item.activation >= self.safety_gate_threshold
            decision = evaluate_learning(candidate, policy=policy) if gated else None
            if gated and decision is not None and decision.decision is not Decision.ALLOW:
                # Quarantine the candidate instead of promoting it; durable
                # knowledge stays untouched and the rejection is auditable.
                self.rejected_candidates.append(
                    {
                        "key": key,
                        "candidate": candidate,
                        "decision": decision.decision.value,
                        "reason": decision.reason,
                        "audit_code": decision.audit_code,
                    }
                )
                self.consolidated_keys.add(key)
                continue

            if isinstance(content, dict):
                if "subject" in content and "predicate" in content:
                    if semantic_memory is not None:
                        semantic_memory.store_fact(
                            subject=content["subject"],
                            predicate=content["predicate"],
                            obj=content.get("object", content.get("obj", "")),
                            confidence=content.get("confidence", 1.0),
                            source=content.get("source", "working_memory"),
                        )
                    # Even without an in-memory semantic store, hand the fact
                    # to the persistence sink so it can be flushed elsewhere
                    # (e.g. directly to the database).
                    self._notify_sink("fact", content, {}, item.activation)
                    consolidated.append(key)
                elif episodic_memory is not None:
                    episodic_memory.store(
                        content=content,
                        context=content.get("context", {}) if isinstance(content.get("context"), dict) else {},
                        importance=item.activation,
                    )
                    self._notify_sink(
                        "episode",
                        content,
                        content.get("context", {}) if isinstance(content.get("context"), dict) else {},
                        item.activation,
                    )
                    consolidated.append(key)
            elif episodic_memory is not None:
                episodic_memory.store(
                    content=content,
                    importance=item.activation,
                )
                self._notify_sink("episode", content, {}, item.activation)
                consolidated.append(key)

            self.consolidated_keys.add(key)
            self.consolidation_count += 1

        return consolidated

    def _notify_sink(
        self,
        kind: str,
        content: Any,
        context: Dict[str, Any],
        importance: float,
    ) -> None:
        """Hand a consolidated item to the persistence sink if it matters."""
        if self.persistence_sink is not None and importance >= self.persistence_threshold:
            try:
                self.persistence_sink(
                    ConsolidationEvent(
                        kind=kind,
                        content=content,
                        context=context,
                        importance=importance,
                        source=(
                            str(content.get("source", "working_memory"))
                            if isinstance(content, dict)
                            else "working_memory"
                        ),
                    )
                )
            except Exception:
                pass

    def __repr__(self) -> str:
        return f"MemoryConsolidator(threshold={self.consolidation_threshold}, consolidated={self.consolidation_count})"
