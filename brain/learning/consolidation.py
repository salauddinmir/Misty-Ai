"""
Memory Consolidation.

Transfers important information from working memory to long-term storage.
"""

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List

from brain.memory.episodic import EpisodicMemory
from brain.memory.semantic import SemanticMemory
from brain.memory.working import WorkingMemory


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
    persistence_sink: Callable[[ConsolidationEvent], None] | None = None
    consolidated_keys: set[str] = field(default_factory=set)

    def consolidate(
        self,
        working_memory: WorkingMemory,
        episodic_memory: EpisodicMemory,
        semantic_memory: SemanticMemory,
    ) -> List[str]:
        """Consolidate active working memory items to long-term storage."""
        consolidated = []

        for key, item in list(working_memory.items.items()):
            if key in self.consolidated_keys or item.activation < self.consolidation_threshold:
                continue

            content = item.content

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
