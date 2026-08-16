"""
Working Memory.

Short-term buffer with limited capacity and temporal decay.
Items are stored with activation levels that decay over time;
when capacity is exceeded, the least active item is removed.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
import time as time_module


@dataclass
class MemoryItem:
    """A single item in working memory.

    Attributes:
        content: The stored content (concept, relation, text, etc.).
        activation: Current activation level (decays over time).
        timestamp: When this item was added to working memory.
        access_count: How many times this item has been accessed.
    """

    content: Any
    activation: float = 1.0
    timestamp: float = field(default_factory=time_module.time)
    access_count: int = 0

    def decay(self, rate: float = 0.95) -> None:
        """Apply temporal decay to activation."""
        self.activation *= rate

    def boost(self, amount: float = 0.3) -> None:
        """Boost activation (e.g., when item is accessed)."""
        self.activation = min(1.0, self.activation + amount)
        self.access_count += 1


@dataclass
class WorkingMemory:
    """Short-term memory buffer with capacity limits and decay.

    Attributes:
        capacity: Maximum number of items (analogous to Miller's 7+/-2).
        decay_rate: How fast items decay per cycle.
        items: Current items in working memory.
    """

    capacity: int = 7
    decay_rate: float = 0.95
    items: Dict[str, MemoryItem] = field(default_factory=dict)

    def store(self, key: str, content: Any) -> None:
        """Store an item in working memory.

        If at capacity, the least active item is evicted.
        """
        if key in self.items:
            self.items[key].content = content
            self.items[key].boost()
            return

        if len(self.items) >= self.capacity:
            self._evict_least_active()

        self.items[key] = MemoryItem(content=content)

    def retrieve(self, key: str) -> Optional[Any]:
        """Retrieve an item from working memory."""
        item = self.items.get(key)
        if item is not None:
            item.boost()
            return item.content
        return None

    def contains(self, key: str) -> bool:
        """Check if a key exists in working memory."""
        return key in self.items

    def get_all_items(self) -> Dict[str, Any]:
        """Get all items currently in working memory."""
        return {k: v.content for k, v in self.items.items()}

    def decay_all(self) -> None:
        """Apply decay to all items and remove those below threshold."""
        to_remove = []
        for key, item in self.items.items():
            item.decay(self.decay_rate)
            if item.activation < 0.01:
                to_remove.append(key)

        for key in to_remove:
            del self.items[key]

    def clear(self) -> None:
        """Clear all items from working memory."""
        self.items.clear()

    def _evict_least_active(self) -> None:
        """Remove the item with the lowest activation."""
        if not self.items:
            return
        min_key = min(self.items, key=lambda k: self.items[k].activation)
        del self.items[min_key]

    @property
    def size(self) -> int:
        """Current number of items in working memory."""
        return len(self.items)

    def __repr__(self) -> str:
        return f"WorkingMemory(size={self.size}/{self.capacity})"
