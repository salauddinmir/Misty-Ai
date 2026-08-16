"""
Episodic Memory.

Stores event-based memories with timestamps, context, and
emotional valence. Supports temporal retrieval and context-based recall.
"""

import time as time_module
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class Episode:
    """A single episodic memory entry."""

    content: Any
    context: Dict[str, Any] = field(default_factory=dict)
    episode_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    timestamp: float = field(default_factory=time_module.time)
    emotional_valence: float = 0.0
    importance: float = 0.5
    access_count: int = 0


@dataclass
class EpisodicMemory:
    """Event-based long-term memory system."""

    episodes: List[Episode] = field(default_factory=list)
    max_episodes: int = 1000

    def store(
        self,
        content: Any,
        context: Dict[str, Any] | None = None,
        emotional_valence: float = 0.0,
        importance: float = 0.5,
    ) -> Episode:
        """Store a new episodic memory."""
        episode = Episode(
            content=content,
            context=context or {},
            emotional_valence=emotional_valence,
            importance=importance,
        )
        self.episodes.append(episode)

        if len(self.episodes) > self.max_episodes:
            self.episodes.sort(key=lambda e: e.importance, reverse=True)
            self.episodes = self.episodes[: self.max_episodes]

        return episode

    def recall_recent(self, n: int = 5) -> List[Episode]:
        """Recall the N most recent episodes."""
        sorted_eps = sorted(self.episodes, key=lambda e: e.timestamp, reverse=True)
        for ep in sorted_eps[:n]:
            ep.access_count += 1
        return sorted_eps[:n]

    def recall_by_context(self, context_key: str, context_value: Any) -> List[Episode]:
        """Recall episodes matching a context attribute."""
        matches = [ep for ep in self.episodes if ep.context.get(context_key) == context_value]
        for ep in matches:
            ep.access_count += 1
        return matches

    def recall_by_content(self, query: str) -> List[Episode]:
        """Recall episodes whose content contains the query string."""
        matches = []
        for ep in self.episodes:
            content_str = str(ep.content).lower()
            if query.lower() in content_str:
                ep.access_count += 1
                matches.append(ep)
        return matches

    @property
    def size(self) -> int:
        """Number of stored episodes."""
        return len(self.episodes)

    def __repr__(self) -> str:
        return f"EpisodicMemory(episodes={self.size})"
