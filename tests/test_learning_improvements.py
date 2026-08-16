"""Tests for Phase-1 learning improvements.

Covers:
- Epsilon-greedy exploration in ReinforcementLearner
- State bucketing generalisation
- RewardSignal valence modifier and positive streak
- ConsolidationEvent + persistence sink
- Procedural memory influencing the REASON phase
"""

from brain.learning.consolidation import MemoryConsolidator
from brain.learning.reinforcement import ReinforcementLearner
from brain.learning.reward import RewardSignal
from brain.memory.procedural import ProceduralMemory
from brain.memory.working import MemoryItem, WorkingMemory


class TestReinforcementLearnerExploration:
    """Epsilon-greedy exploration keeps the learner from getting stuck."""

    def test_bucket_is_deterministic(self) -> None:
        learner = ReinforcementLearner()
        assert learner.bucket("hello") == learner.bucket("hello")
        assert len(learner.bucket("hello")) > 0

    def test_bucket_spreads_over_bucket_space(self) -> None:
        learner = ReinforcementLearner(n_buckets=16)
        buckets = {learner.bucket(f"state_{i}") for i in range(50)}
        # 50 distinct states should not all land in one bucket
        assert len(buckets) > 1

    def test_value_blends_state_and_bucket(self) -> None:
        learner = ReinforcementLearner()
        learner.update("state_A", "action_1", 1.0)
        # update() writes both the raw state key and the bucket key, so a
        # lookup for the raw state blends both entries.
        assert learner.bucket("state_A") in learner.q_values
        raw_only = learner.q_values["state_A"]["action_1"]
        bucket_only = learner.q_values[learner.bucket("state_A")]["action_1"]
        blended = learner.get_value("state_A", "action_1")
        # The blended value sits between the two entries.
        assert min(raw_only, bucket_only) <= blended <= max(raw_only, bucket_only) + 1e-9

    def test_get_best_action_explores(self) -> None:
        learner = ReinforcementLearner(exploration_rate=1.0)
        learner.update("s", "a", 10.0)
        # With full exploration, suboptimal actions are still picked sometimes
        choices = {learner.get_best_action("s", ["a", "b"]) for _ in range(40)}
        assert choices == {"a", "b"}

    def test_get_best_action_greedy_with_no_exploration(self) -> None:
        learner = ReinforcementLearner(exploration_rate=0.0)
        learner.update("s", "a", 10.0)
        learner.update("s", "b", 0.1)
        assert learner.get_best_action("s", ["a", "b"]) == "a"

    def test_update_writes_bucket_entry(self) -> None:
        learner = ReinforcementLearner()
        learner.update("state_X", "act", 2.0)
        assert learner.bucket("state_X") in learner.q_values


class TestRewardSignalImprovements:
    """Reward signal carries emotion and streak awareness."""

    def test_valence_modifier_scales_reward(self) -> None:
        signal = RewardSignal(valence_modifier=0.5)
        reward = signal.compute_reward(goal_achieved=True)
        # 1.0 * (1 + 0.5) = 1.5
        assert abs(reward - 1.5) < 1e-9

    def test_negative_valence_dampens(self) -> None:
        signal = RewardSignal(valence_modifier=-0.5)
        reward = signal.compute_reward(goal_achieved=True)
        assert reward < 1.0

    def test_positive_streak_increments_and_resets(self) -> None:
        signal = RewardSignal()
        signal.compute_reward(goal_achieved=True)
        signal.compute_reward(prediction_correct=True)
        assert signal.positive_streak == 2
        signal.generate_penalty()
        assert signal.positive_streak == 0

    def test_recent_reward_weights_recent(self) -> None:
        signal = RewardSignal()
        signal._record(0.0)
        signal._record(0.0)
        signal._record(1.0)  # most recent
        assert signal.recent_reward > signal.average_reward


class TestConsolidationSink:
    """Consolidator hands important items to the persistence sink."""

    def test_sink_receives_high_importance_items(self) -> None:
        received: list = []
        consolidator = MemoryConsolidator(
            persistence_threshold=0.5,
            persistence_sink=lambda e: received.append(e),
        )
        memory = WorkingMemory()
        item = MemoryItem(content={"subject": "A", "predicate": "is_b", "object": "B"})
        item.activation = 0.6
        memory.items["fact"] = item

        consolidator.consolidate(memory, *([None, None]))
        assert len(received) == 1
        assert received[0].kind == "fact"
        assert received[0].importance == 0.6

    def test_sink_ignores_low_importance(self) -> None:
        received: list = []
        consolidator = MemoryConsolidator(
            persistence_threshold=0.5,
            persistence_sink=lambda e: received.append(e),
        )
        memory = WorkingMemory()
        item = MemoryItem(content={"subject": "A", "predicate": "is_b", "object": "B"})
        item.activation = 0.2
        memory.items["fact"] = item

        consolidator.consolidate(memory, *([None, None]))
        assert received == []


class TestProceduralMemoryInReasoning:
    """Stored procedures influence the REASON phase output."""

    def test_procedure_stored_and_reinforced(self) -> None:
        memory = ProceduralMemory()
        proc = memory.store(
            name="greet",
            condition="hello",
            action="say_hi",
        )
        proc.reinforce(success=True)
        assert proc.strength > 0.5
        assert memory.get_strongest("hello there") is proc

    def test_strongest_returns_none_when_empty(self) -> None:
        memory = ProceduralMemory()
        assert memory.get_strongest("anything") is None
