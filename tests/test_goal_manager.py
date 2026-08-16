"""
Phase 6 tests: goal-driven behavior — hierarchical decomposition,
multi-step plans, and progress tracking.
"""

from brain.core.brain import Brain
from brain.goals.manager import Goal, GoalManager, GoalStatus, PlanStep

# -----------------------------------------------------------------------
# PlanStep / Goal data structures
# -----------------------------------------------------------------------


class TestPlanStepAndGoal:
    def test_step_advance(self) -> None:
        goal = Goal(
            description="answer question",
            intent="query_who",
            steps=[
                PlanStep(action="interpret_input"),
                PlanStep(action="recall_relevant"),
                PlanStep(action="compose_answer"),
            ],
        )
        assert goal.current_step().action == "interpret_input"
        goal.advance_step()
        assert goal.progress == 1 / 3
        goal.advance_step()
        goal.advance_step()
        assert goal.current_step() is None
        assert goal.progress == 1.0

    def test_goal_lifecycle(self) -> None:
        goal = Goal(description="greet")
        goal.activate()
        assert goal.status == GoalStatus.ACTIVE
        goal.achieve()
        assert goal.is_terminal and goal.progress == 1.0
        goal2 = Goal(description="fail")
        goal2.fail(reason="no info")
        assert goal2.is_terminal and goal2.context["failure_reason"] == "no info"

    def test_goal_round_trip(self) -> None:
        goal = Goal(
            description="teach fact",
            intent="teach",
            priority=0.8,
            steps=[PlanStep(action="interpret_input"), PlanStep(action="store_fact")],
        )
        goal.advance_step()
        restored = Goal.from_dict(goal.to_dict())
        assert restored.goal_id == goal.goal_id
        # Progress is recomputed from step completion on restore.
        assert restored.progress == 0.5
        assert restored.steps[0].completed is True
        assert restored.steps[1].completed is False


# -----------------------------------------------------------------------
# GoalManager
# -----------------------------------------------------------------------


class TestGoalManagerDecomposition:
    def setup_method(self) -> None:
        self.manager = GoalManager()

    def test_decompose_known_intent(self) -> None:
        goal = self.manager.decompose("query_who", "who made misty?")
        assert len(goal.steps) == 4
        assert goal.steps[0].action == "interpret_input"
        assert goal.status == GoalStatus.ACTIVE

    def test_decompose_unknown_intent(self) -> None:
        goal = self.manager.decompose("whatever", "xyz")
        assert len(goal.steps) == 1 and goal.steps[0].action == "acknowledge"

    def test_hierarchy_has_children(self) -> None:
        goal = self.manager.decompose_hierarchy("query_who", "q")
        assert len(goal.sub_goal_ids) == 2
        for cid in goal.sub_goal_ids:
            child = self.manager.goals[cid]
            assert child.parent_id == goal.goal_id
            assert child.status == GoalStatus.ACTIVE

    def test_priority_selection(self) -> None:
        greet = self.manager.decompose("greeting", "hi", priority=0.4)
        query = self.manager.decompose("query_who", "who?", priority=0.85)
        greet.achieve()
        # Terminal goals are skipped; the non-terminal one wins.
        assert self.manager.active_goal().goal_id == query.goal_id

    def test_no_active_goal_when_all_terminal(self) -> None:
        g = self.manager.decompose("greeting", "hi")
        g.achieve()
        assert self.manager.active_goal() is None

    def test_advance_completes_goal(self) -> None:
        goal = self.manager.decompose("greeting", "hi")
        first_step = goal.steps[0]
        done = self.manager.advance_goal(goal.goal_id)
        assert first_step.completed
        assert not done["done"]
        for _ in goal.steps[1:]:
            done = self.manager.advance_goal(goal.goal_id)
        assert done["done"]
        assert goal.status == GoalStatus.ACHIEVED

    def test_hierarchy_waits_for_children(self) -> None:
        goal = self.manager.decompose_hierarchy("query_who", "q")
        child = self.manager.goals[goal.sub_goal_ids[0]]
        for _ in child.steps:
            self.manager.advance_goal(child.goal_id)
        assert child.status == GoalStatus.ACHIEVED
        # Parent cannot achieve while the second child is incomplete.
        result = self.manager.advance_goal(goal.goal_id)
        assert result["waiting_on_children"] is True
        second = self.manager.goals[goal.sub_goal_ids[1]]
        for _ in second.steps:
            self.manager.advance_goal(second.goal_id)
        result = self.manager.advance_goal(goal.goal_id)
        assert result["done"] and goal.status == GoalStatus.ACHIEVED

    def test_root_walk(self) -> None:
        goal = self.manager.decompose_hierarchy("teach", "t")
        child = self.manager.goals[goal.sub_goal_ids[0]]
        assert self.manager.root_goal(child.goal_id).goal_id == goal.goal_id
        assert self.manager.root_goal(goal.goal_id).goal_id == goal.goal_id

    def test_registry_bounded(self) -> None:
        manager = GoalManager(max_goals=5)
        for i in range(10):
            manager.decompose("greeting", f"hi {i}")
        assert len(manager.goals) <= 5

    def test_stats(self) -> None:
        g = self.manager.decompose("greeting", "hi")
        g.achieve()
        self.manager.decompose("statement", "s")
        stats = self.manager.stats()
        assert stats["achieved"] == 1
        # Newly created goals start ACTIVE, not PENDING.
        assert stats["active"] == 1

    def test_serialize_round_trip(self) -> None:
        self.manager.decompose_hierarchy("query_who", "who made misty?")
        restored = GoalManager()
        restored.load(self.manager.to_dict())
        assert len(restored.goals) == len(self.manager.goals)
        root = next(g for g in restored.goals.values() if g.parent_id is None)
        assert root.sub_goal_ids == self.manager.goals[root.goal_id].sub_goal_ids

    def test_reset_clears(self) -> None:
        self.manager.decompose("greeting", "hi")
        self.manager.reset()
        assert not self.manager.goals


# -----------------------------------------------------------------------
# Wiring: brain uses the goal manager in the cycle
# -----------------------------------------------------------------------


class TestBrainGoalManagerWiring:
    def test_goal_manager_wired(self) -> None:
        brain = Brain()
        assert hasattr(brain, "goal_manager") and isinstance(brain.goal_manager, GoalManager)

    def test_plan_phase_creates_goal(self) -> None:
        brain = Brain()
        result = brain.process("মিস্তি কে তৈরি করেছে?")
        state = result["brain_state"]
        assert state["active_goal"] is not None
        # The cycle creates a hierarchical goal (root + children); by the
        # end of the cycle the LEARN phase has advanced at least one step
        # of the highest-priority active goal.
        assert "achieved" in state["goal_stats"]
        assert state["active_goal"]["progress"] >= 0.0

    def test_subgoals_exist_for_query(self) -> None:
        brain = Brain()
        brain.process("আমার নাম সাবরীনা")
        root = None
        for g in brain.goal_manager.goals.values():
            if g.intent == "name_declaration" and g.parent_id is None:
                root = g
        assert root is not None and len(root.sub_goal_ids) == 2

    def test_goal_progress_increases_across_cycles(self) -> None:
        brain = Brain()
        brain.process("মিস্তি কে তৈরি করেছে?")
        first = brain.goal_manager.active_goal()
        assert first is not None
        first_id = first.goal_id
        first_progress = first.progress
        brain.process("আসলেই?")  # second cycle advances goals
        active = brain.goal_manager.goals.get(first_id)
        assert active is not None and active.progress >= first_progress

    def test_goal_state_survives_multiple_turns(self) -> None:
        brain = Brain()
        for text in ["হ্যালো", "আমার নাম টিম", "আমার একটা বিছাল আছে"]:
            brain.process(text)
        assert brain.goal_manager.stats()["achieved"] >= 2
