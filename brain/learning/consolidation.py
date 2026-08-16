"""
Memory Consolidation.

Transfers important information from working memory to long-term storage.
"""

from dataclasses import dataclass, field
from typing import List

from brain.memory.working import WorkingMemory
from brain.memory.episodic import EpisodicMemory
from brain.memory.semantic import SemanticMemory


@dataclass
class MemoryConsolidator:
    """Consolidates working memory to long-term storage."""

    consolidation_threshold: float = 0.3
    consolidation_count: int = 0

    def consolidate(
        self,
        working_memory: WorkingMemory,
        episodic_memory: EpisodicMemory,
        semantic_memory: SemanticMemory,
    ) -> List[str]:
        """Consolidate active working memory items to long-term storage."""
        consolidated = []

        for key, item in list(working_memory.items.items()):
            if item.activation < self.consolidation_threshold:
                continue

            content = item.content

            if isinstance(content, dict):
                if "subject" in content and "predicate" in content:
                    semantic_memory.store_fact(
                        subject=content["subject"],
                        predicate=content["predicate"],
                        obj=content.get("object", content.get("obj", "")),
                        confidence=content.get("confidence", 1.0),
                    )
                    consolidated.append(key)
                else:
                    episodic_memory.store(
                        content=content,
                        context=content.get("context", {}),
                        importance=item.activation,
                    )
                    consolidated.append(key)
            else:
                episodic_memory.store(
                    content=content,
                    importance=item.activation,
                )
                consolidated.append(key)

            self.consolidation_count += 1

        return consolidated

    def __repr__(self) -> str:
        return (
            f"MemoryConsolidator(threshold={self.consolidation_threshold}, "
            f"consolidated={self.consolidation_count})"
        )
