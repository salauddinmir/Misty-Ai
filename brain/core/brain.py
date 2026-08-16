"""
Main Brain Class.

The central orchestrator that initializes all subsystems and
processes input through the cognitive cycle. This is the primary
entry point for the cognitive system.
"""

from typing import Any, Dict, List, Optional
import time as time_module

from brain.neurons.lif import LIFNeuron
from brain.neurons.populations import NeuronPopulation
from brain.synapses.synapse import Synapse
from brain.synapses.stdp import STDPRule
from brain.synapses.plasticity import PlasticityManager
from brain.memory.working import WorkingMemory
from brain.memory.episodic import EpisodicMemory
from brain.memory.semantic import SemanticMemory
from brain.memory.procedural import ProceduralMemory
from brain.graph.concepts import Concept, ConceptGraph
from brain.graph.activation import SpreadingActivation
from brain.reasoning.inference import InferenceEngine
from brain.planner.planner import Planner
from brain.planner.goals import Goal
from brain.learning.reinforcement import ReinforcementLearner
from brain.learning.reward import RewardSignal
from brain.learning.consolidation import MemoryConsolidator
from brain.reflection.reflection import ReflectionEngine
from brain.emotion.state import EmotionalState
from brain.nlu.parser import NLUParser, ParseResult, IntentType
from brain.core.state import BrainState
from brain.core.cycle import CognitiveCycle, CognitivePhase, CycleResult


class Brain:
    """The main cognitive system orchestrator.

    Initializes all subsystems and processes input through
    the cognitive cycle to produce intelligent responses
    WITHOUT any LLM dependency.
    """

    def __init__(self) -> None:
        """Initialize all cognitive subsystems."""
        # Identity
        self.name: Optional[str] = None
        self.user_name: Optional[str] = None

        # Neural substrate
        self.concept_population = NeuronPopulation(name="concepts")
        self.plasticity = PlasticityManager()

        # Memory systems
        self.working_memory = WorkingMemory(capacity=7)
        self.episodic_memory = EpisodicMemory()
        self.semantic_memory = SemanticMemory()
        self.procedural_memory = ProceduralMemory()

        # Knowledge graph
        self.concept_graph = ConceptGraph()
        self.spreading_activation = SpreadingActivation()

        # Reasoning
        self.inference = InferenceEngine()

        # Planning
        self.planner = Planner()

        # Learning
        self.learner = ReinforcementLearner()
        self.reward_system = RewardSignal()
        self.consolidator = MemoryConsolidator()

        # Meta-cognition
        self.reflection = ReflectionEngine()

        # Emotion
        self.emotion = EmotionalState()

        # NLU
        self.nlu = NLUParser()

        # Cognitive cycle
        self.cycle = CognitiveCycle()

        # State
        self.state = BrainState()

    def process(self, text_input: str) -> Dict[str, Any]:
        """Process a text input through the full cognitive cycle.

        This is the main entry point for interacting with the brain.

        Args:
            text_input: Natural language input (Bengali or English).

        Returns:
            Dictionary with response, brain state, and processing details.
        """
        start_time = time_module.time()
        self.state.last_input = text_input

        # Start cognitive cycle
        self.cycle.start_cycle()

        # Phase 1: OBSERVE
        observe_result = self._phase_observe(text_input)
        self.cycle.advance(observe_result)

        # Phase 2: INTERPRET
        interpret_result = self._phase_interpret(text_input)
        self.cycle.advance(interpret_result)

        # Phase 3: RECALL
        recall_result = self._phase_recall(interpret_result.data.get("parse_result"))
        self.cycle.advance(recall_result)

        # Phase 4: ASSOCIATE
        associate_result = self._phase_associate(interpret_result.data.get("parse_result"))
        self.cycle.advance(associate_result)

        # Phase 5: REASON
        reason_result = self._phase_reason(interpret_result.data.get("parse_result"))
        self.cycle.advance(reason_result)

        # Phase 6: PLAN
        plan_result = self._phase_plan(interpret_result.data.get("parse_result"))
        self.cycle.advance(plan_result)

        # Phase 7: ACT
        act_result = self._phase_act(
            interpret_result.data.get("parse_result"),
            recall_result.data,
            associate_result.data,
        )
        self.cycle.advance(act_result)

        # Phase 8: EVALUATE
        evaluate_result = self._phase_evaluate(act_result)
        self.cycle.advance(evaluate_result)

        # Phase 9: LEARN
        learn_result = self._phase_learn(interpret_result.data.get("parse_result"), act_result)
        self.cycle.advance(learn_result)

        # Phase 10: CONSOLIDATE
        consolidate_result = self._phase_consolidate()
        self.cycle.advance(consolidate_result)

        # Update state
        processing_time = time_module.time() - start_time
        response = act_result.data.get("response", "")
        self.state.last_output = response
        self.state.cycle_count = self.cycle.cycle_count
        self.state.current_phase = "idle"
        self.state.timestamp = time_module.time()

        # Record performance
        self.reflection.record_performance(
            input_type=interpret_result.data.get("intent", "unknown"),
            goal_achieved=act_result.success,
            response_quality=evaluate_result.data.get("quality", 0.5),
            processing_time=processing_time,
            confidence=act_result.data.get("confidence", 0.5),
        )

        return {
            "response": response,
            "brain_state": self.get_state(),
            "processing_time": processing_time,
            "cycle_count": self.cycle.cycle_count,
            "active_concepts": self.state.active_concepts,
            "emotional_state": self.emotion.to_dict(),
        }

    def _phase_observe(self, text_input: str) -> CycleResult:
        """OBSERVE phase: Register incoming input."""
        self.state.current_phase = "observe"
        self.working_memory.store("current_input", text_input)

        is_question = "?" in text_input or "কে" in text_input or "কি" in text_input
        self.emotion.update_from_input(is_question=is_question, is_new_info=True)

        return CycleResult(
            phase=CognitivePhase.OBSERVE,
            data={"input": text_input, "is_question": is_question},
            success=True,
        )

    def _phase_interpret(self, text_input: str) -> CycleResult:
        """INTERPRET phase: Parse input using NLU."""
        self.state.current_phase = "interpret"
        parse_result = self.nlu.parse(text_input)

        self.working_memory.store("parse_result", {
            "intent": parse_result.intent.value,
            "entities": parse_result.entities,
            "relations": parse_result.relations,
            "query": parse_result.query,
        })

        return CycleResult(
            phase=CognitivePhase.INTERPRET,
            data={
                "parse_result": parse_result,
                "intent": parse_result.intent.value,
            },
            success=parse_result.confidence > 0.3,
        )

    def _phase_recall(self, parse_result: Optional[ParseResult]) -> CycleResult:
        """RECALL phase: Retrieve relevant memories."""
        self.state.current_phase = "recall"
        recalled: Dict[str, Any] = {}

        if parse_result and parse_result.intent == IntentType.QUERY_WHO:
            target_name = parse_result.query.get("target", "")
            relation = parse_result.query.get("relation", "")

            # Search semantic memory
            facts = self.semantic_memory.query(predicate=relation, obj=target_name)
            if facts:
                recalled["semantic_facts"] = [
                    {"subject": f.subject, "predicate": f.predicate, "obj": f.obj}
                    for f in facts
                ]

            # Search knowledge graph
            target_concept = self.concept_graph.get_concept_by_name(target_name)
            if target_concept:
                relations = self.concept_graph.get_relations(
                    target_concept.concept_id, direction="incoming"
                )
                recalled["graph_relations"] = relations

        return CycleResult(
            phase=CognitivePhase.RECALL,
            data=recalled,
            success=True,
        )

    def _phase_associate(self, parse_result: Optional[ParseResult]) -> CycleResult:
        """ASSOCIATE phase: Spread activation to related concepts."""
        self.state.current_phase = "associate"
        activated: Dict[str, float] = {}

        if parse_result:
            entities = parse_result.entities
            target = (
                entities.get("target")
                or entities.get("name")
                or parse_result.query.get("target")
            )

            if target:
                concept = self.concept_graph.get_concept_by_name(target)
                if concept:
                    activation_map = self.spreading_activation.activate(
                        self.concept_graph, concept.concept_id
                    )
                    activated = activation_map
                    self.state.active_concepts = {
                        k: round(v, 3) for k, v in activation_map.items()
                    }

        return CycleResult(
            phase=CognitivePhase.ASSOCIATE,
            data={"activation_map": activated},
            success=True,
        )

    def _phase_reason(self, parse_result: Optional[ParseResult]) -> CycleResult:
        """REASON phase: Apply inference rules."""
        self.state.current_phase = "reason"
        derived: List[Dict[str, Any]] = []

        if parse_result and parse_result.intent == IntentType.QUERY_WHO:
            target_name = parse_result.query.get("target", "")
            relation = parse_result.query.get("relation", "")

            target_concept = self.concept_graph.get_concept_by_name(target_name)
            if target_concept:
                related = self.concept_graph.find_related(
                    target_concept.concept_id, relation_type=relation, direction="incoming"
                )
                if related:
                    derived = [{"answer": c.name, "relation": relation} for c in related]

        return CycleResult(
            phase=CognitivePhase.REASON,
            data={"derived": derived},
            success=True,
        )

    def _phase_plan(self, parse_result: Optional[ParseResult]) -> CycleResult:
        """PLAN phase: Decide what to do."""
        self.state.current_phase = "plan"

        if not parse_result:
            return CycleResult(
                phase=CognitivePhase.PLAN,
                data={"plan": "acknowledge"},
                success=True,
            )

        if parse_result.intent == IntentType.NAME_DECLARATION:
            plan = "store_identity"
        elif parse_result.intent == IntentType.RELATION_DECLARATION:
            plan = "store_relation"
        elif parse_result.intent in (IntentType.QUERY_WHO, IntentType.QUERY_WHAT):
            plan = "answer_query"
        elif parse_result.intent == IntentType.GREETING:
            plan = "greet_back"
        else:
            plan = "acknowledge"

        return CycleResult(
            phase=CognitivePhase.PLAN,
            data={"plan": plan},
            success=True,
        )

    def _phase_act(
        self,
        parse_result: Optional[ParseResult],
        recall_data: Dict[str, Any],
        associate_data: Dict[str, Any],
    ) -> CycleResult:
        """ACT phase: Execute the plan and generate a response."""
        self.state.current_phase = "act"

        if not parse_result:
            return CycleResult(
                phase=CognitivePhase.ACT,
                data={"response": "...", "confidence": 0.3},
                success=False,
            )

        response = ""
        confidence = 0.5

        if parse_result.intent == IntentType.NAME_DECLARATION:
            response, confidence = self._act_name_declaration(parse_result)

        elif parse_result.intent == IntentType.RELATION_DECLARATION:
            response, confidence = self._act_relation_declaration(parse_result)

        elif parse_result.intent == IntentType.QUERY_WHO:
            response, confidence = self._act_query(parse_result, recall_data)

        elif parse_result.intent == IntentType.GREETING:
            name_part = f", {self.user_name}" if self.user_name else ""
            response = f"Hello{name_part}!"
            confidence = 0.9

        else:
            response = "I received your input but I am not sure how to process it yet."
            confidence = 0.3

        return CycleResult(
            phase=CognitivePhase.ACT,
            data={"response": response, "confidence": confidence},
            success=confidence > 0.5,
        )

    def _act_name_declaration(self, parse_result: ParseResult) -> tuple:
        """Handle name declaration intent."""
        name = parse_result.entities.get("name", "")
        is_self = parse_result.entities.get("is_self", False)

        if is_self:
            self.user_name = name

        # Create concept in knowledge graph
        existing = self.concept_graph.get_concept_by_name(name)
        if not existing:
            self.concept_graph.create_concept(
                name=name,
                concept_type="Person",
                metadata={"is_user": is_self},
            )
            self.semantic_memory.store_fact(
                subject=name, predicate="is_a", obj="Person",
            )
            if is_self:
                self.semantic_memory.store_fact(
                    subject=name, predicate="is", obj="user",
                )

        response = f"I understand. Your name is {name}. I have created a concept for you."
        return response, 0.95

    def _act_relation_declaration(self, parse_result: ParseResult) -> tuple:
        """Handle relation declaration intent."""
        relations = parse_result.relations
        if not relations:
            return "I could not understand the relation.", 0.3

        rel = relations[0]
        source_name = rel.get("source", "")
        relation_type = rel.get("relation_type", "")
        target_name = rel.get("target", "")

        # Resolve __self__ to actual user name
        if source_name == "__self__":
            source_name = self.user_name or "User"

        # Ensure concepts exist
        source_concept = self.concept_graph.get_concept_by_name(source_name)
        if not source_concept:
            source_concept = self.concept_graph.create_concept(
                name=source_name, concept_type="Person"
            )

        target_concept = self.concept_graph.get_concept_by_name(target_name)
        if not target_concept:
            target_concept = self.concept_graph.create_concept(
                name=target_name, concept_type="Entity"
            )

        # Add relation to graph
        self.concept_graph.add_relation(
            source_id=source_concept.concept_id,
            target_id=target_concept.concept_id,
            relation_type=relation_type,
        )

        # Store in semantic memory
        self.semantic_memory.store_fact(
            subject=source_name, predicate=relation_type, obj=target_name,
        )

        response = (
            f"I have learned that {source_name} has relation "
            f"'{relation_type}' with {target_name}."
        )
        return response, 0.9

    def _act_query(self, parse_result: ParseResult, recall_data: Dict[str, Any]) -> tuple:
        """Handle query intent."""
        target_name = parse_result.query.get("target", "")
        relation = parse_result.query.get("relation", "")

        # Strategy 1: Check knowledge graph directly
        target_concept = self.concept_graph.get_concept_by_name(target_name)
        if target_concept:
            related = self.concept_graph.find_related(
                target_concept.concept_id,
                relation_type=relation,
                direction="incoming",
            )
            if related:
                answer = related[0].name
                return f"{answer}", 0.95

        # Strategy 2: Check semantic memory
        facts = self.semantic_memory.query(predicate=relation, obj=target_name)
        if facts:
            answer = facts[0].subject
            return f"{answer}", 0.9

        # Strategy 3: Check recall data
        graph_relations = recall_data.get("graph_relations", [])
        for rel in graph_relations:
            if rel.get("relation_type") == relation:
                source_concept = self.concept_graph.get_concept(rel["source"])
                if source_concept:
                    return f"{source_concept.name}", 0.85

        # No answer found
        self.emotion.update_from_outcome(success=False)
        return (
            f"I do not have information about who has "
            f"'{relation}' relation with {target_name}."
        ), 0.3

    def _phase_evaluate(self, act_result: CycleResult) -> CycleResult:
        """EVALUATE phase: Assess the response quality."""
        self.state.current_phase = "evaluate"
        confidence = act_result.data.get("confidence", 0.5)
        success = act_result.success

        self.emotion.update_from_outcome(success=success)
        quality = confidence * (0.8 if success else 0.4)

        return CycleResult(
            phase=CognitivePhase.EVALUATE,
            data={"quality": quality, "success": success},
            success=True,
        )

    def _phase_learn(
        self, parse_result: Optional[ParseResult], act_result: CycleResult
    ) -> CycleResult:
        """LEARN phase: Update learning systems."""
        self.state.current_phase = "learn"

        success = act_result.success
        confidence = act_result.data.get("confidence", 0.5)

        reward = self.reward_system.compute_reward(
            goal_achieved=success,
            prediction_correct=confidence > 0.7,
        )

        state_key = parse_result.intent.value if parse_result else "unknown"
        action_key = "respond"
        self.learner.update(state_key, action_key, reward)

        return CycleResult(
            phase=CognitivePhase.LEARN,
            data={"reward": reward},
            success=True,
        )

    def _phase_consolidate(self) -> CycleResult:
        """CONSOLIDATE phase: Move working memory to long-term storage."""
        self.state.current_phase = "consolidate"

        consolidated = self.consolidator.consolidate(
            self.working_memory,
            self.episodic_memory,
            self.semantic_memory,
        )

        self.working_memory.decay_all()
        self.emotion.decay()

        return CycleResult(
            phase=CognitivePhase.CONSOLIDATE,
            data={"consolidated_keys": consolidated},
            success=True,
        )

    def get_state(self) -> Dict[str, Any]:
        """Get a snapshot of the current brain state."""
        return {
            "cycle_count": self.cycle.cycle_count,
            "user_name": self.user_name,
            "concepts": self.concept_graph.num_concepts,
            "relations": self.concept_graph.num_relations,
            "working_memory_size": self.working_memory.size,
            "episodic_memories": self.episodic_memory.size,
            "semantic_facts": self.semantic_memory.size,
            "emotional_state": self.emotion.to_dict(),
            "active_concepts": self.state.active_concepts,
            "performance": self.reflection.evaluate_recent_performance(),
        }

    def __repr__(self) -> str:
        return (
            f"Brain(cycles={self.cycle.cycle_count}, "
            f"concepts={self.concept_graph.num_concepts}, "
            f"relations={self.concept_graph.num_relations})"
        )
