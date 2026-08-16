"""
Tests for Working Memory.

Tests cover:
- Adding items to working memory
- Retrieving items by key
- Capacity overflow and eviction of least active item
- Temporal decay of activations
- Boosting on access
- Clearing memory
"""

from brain.memory.working import MemoryItem, WorkingMemory


class TestWorkingMemoryBasics:
    """Test basic working memory operations."""

    def test_default_capacity(self) -> None:
        """Default capacity is 7 (Miller's law)."""
        wm = WorkingMemory()
        assert wm.capacity == 7
        assert wm.size == 0

    def test_custom_capacity(self) -> None:
        """Working memory respects custom capacity."""
        wm = WorkingMemory(capacity=3)
        assert wm.capacity == 3

    def test_store_and_retrieve(self) -> None:
        """Can store and retrieve items by key."""
        wm = WorkingMemory()
        wm.store("hello", "world")
        result = wm.retrieve("hello")
        assert result == "world"

    def test_retrieve_nonexistent(self) -> None:
        """Retrieving a non-existent key returns None."""
        wm = WorkingMemory()
        result = wm.retrieve("nonexistent")
        assert result is None

    def test_size_increases(self) -> None:
        """Size increases as items are added."""
        wm = WorkingMemory()
        assert wm.size == 0
        wm.store("a", 1)
        assert wm.size == 1
        wm.store("b", 2)
        assert wm.size == 2

    def test_store_overwrites_existing(self) -> None:
        """Storing with same key updates content."""
        wm = WorkingMemory()
        wm.store("key", "value1")
        wm.store("key", "value2")
        assert wm.retrieve("key") == "value2"
        assert wm.size == 1

    def test_contains(self) -> None:
        """Contains checks if key exists."""
        wm = WorkingMemory()
        wm.store("exists", "yes")
        assert wm.contains("exists") is True
        assert wm.contains("nope") is False

    def test_get_all_items(self) -> None:
        """Get all items returns correct dictionary."""
        wm = WorkingMemory()
        wm.store("a", 1)
        wm.store("b", 2)
        wm.store("c", 3)
        all_items = wm.get_all_items()
        assert all_items == {"a": 1, "b": 2, "c": 3}


class TestCapacityOverflow:
    """Test behavior when capacity is exceeded."""

    def test_eviction_at_capacity(self) -> None:
        """Least active item is evicted when at capacity."""
        wm = WorkingMemory(capacity=3)
        wm.store("a", 1)
        wm.store("b", 2)
        wm.store("c", 3)
        assert wm.size == 3

        # Add one more - should evict one
        wm.store("d", 4)
        assert wm.size == 3
        # 'd' should be present
        assert wm.retrieve("d") == 4

    def test_accessed_items_survive_eviction(self) -> None:
        """Items that are accessed get boosted and survive eviction."""
        wm = WorkingMemory(capacity=3, decay_rate=0.5)
        wm.store("a", 1)
        wm.store("b", 2)
        wm.store("c", 3)

        # Decay all items so they drop below 1.0
        wm.decay_all()

        # Access 'a' to boost its activation back up
        wm.retrieve("a")
        wm.retrieve("a")

        # Now 'a' should have higher activation than 'b' or 'c'
        assert wm.items["a"].activation > wm.items["b"].activation

        # Now add new item - 'b' or 'c' should be evicted (not 'a')
        wm.store("d", 4)
        assert wm.contains("a") is True  # 'a' was accessed, should survive
        assert wm.contains("d") is True  # 'd' is the new item

    def test_never_exceeds_capacity(self) -> None:
        """Size never exceeds defined capacity."""
        wm = WorkingMemory(capacity=3)
        for i in range(10):
            wm.store(f"item_{i}", i)
        assert wm.size <= 3


class TestDecay:
    """Test temporal decay of memory items."""

    def test_decay_reduces_activation(self) -> None:
        """Decay reduces activation of all items."""
        wm = WorkingMemory(decay_rate=0.5)
        wm.store("item", "content")

        initial_activation = wm.items["item"].activation
        wm.decay_all()
        assert wm.items["item"].activation < initial_activation

    def test_low_activation_items_removed(self) -> None:
        """Items with activation below threshold are removed after decay."""
        wm = WorkingMemory(decay_rate=0.01)  # Very fast decay
        wm.store("item", "content")

        # Apply many decay cycles
        for _ in range(10):
            wm.decay_all()

        # Item should be removed (activation < 0.01)
        assert wm.size == 0

    def test_decay_rate_effect(self) -> None:
        """Higher decay rate preserves activation better."""
        wm_slow = WorkingMemory(decay_rate=0.99)
        wm_fast = WorkingMemory(decay_rate=0.5)

        wm_slow.store("item", "content")
        wm_fast.store("item", "content")

        # Apply 5 decay cycles
        for _ in range(5):
            wm_slow.decay_all()
            wm_fast.decay_all()

        # Slow decay should preserve more activation
        if "item" in wm_slow.items and "item" in wm_fast.items:
            assert wm_slow.items["item"].activation > wm_fast.items["item"].activation

    def test_clear(self) -> None:
        """Clear removes all items."""
        wm = WorkingMemory()
        wm.store("a", 1)
        wm.store("b", 2)
        wm.store("c", 3)
        assert wm.size == 3
        wm.clear()
        assert wm.size == 0


class TestMemoryItem:
    """Test individual MemoryItem behavior."""

    def test_item_creation(self) -> None:
        """MemoryItem starts with activation 1.0."""
        item = MemoryItem(content="test")
        assert item.activation == 1.0
        assert item.access_count == 0

    def test_item_decay(self) -> None:
        """Decay reduces activation multiplicatively."""
        item = MemoryItem(content="test")
        item.decay(rate=0.5)
        assert item.activation == 0.5
        item.decay(rate=0.5)
        assert item.activation == 0.25

    def test_item_boost(self) -> None:
        """Boost increases activation and access count."""
        item = MemoryItem(content="test", activation=0.5)
        item.boost(amount=0.3)
        assert item.activation == 0.8
        assert item.access_count == 1

    def test_item_boost_capped(self) -> None:
        """Boost is capped at 1.0."""
        item = MemoryItem(content="test", activation=0.9)
        item.boost(amount=0.5)
        assert item.activation == 1.0
