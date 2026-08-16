"""
Main Brain Class.

The central orchestrator that initializes all subsystems and
processes input through the cognitive cycle. This is the primary
entry point for the cognitive system.
"""

import time as time_module
from typing import Any, Dict, List

import numpy as np

from brain.core.cycle import CognitiveCycle, CognitivePhase, CycleResult
from brain.core.state import BrainState
from brain.emotion.state import EmotionalState
from brain.graph.activation import SpreadingActivation
from brain.graph.concepts import ConceptGraph
from brain.learning.consolidation import MemoryConsolidator
from brain.learning.reinforcement import ReinforcementLearner
from brain.learning.reward import RewardSignal
from brain.memory.episodic import EpisodicMemory
from brain.memory.procedural import ProceduralMemory
from brain.memory.semantic import SemanticMemory
from brain.memory.working import WorkingMemory
from brain.neurons.populations import NeuronPopulation
from brain.nlu.parser import IntentType, NLUParser, ParseResult
from brain.planner.planner import Planner
from brain.reasoning.inference import InferenceEngine
from brain.reflection.reflection import ReflectionEngine
from brain.synapses.plasticity import PlasticityManager


class Brain:
    """The main cognitive system orchestrator.

    Initializes all subsystems and processes input through
    the cognitive cycle to produce intelligent responses
    WITHOUT any LLM dependency.

    Supports an optional neural simulation mode that uses vectorized
    populations and brain regions for concept activation and association.
    """

    def __init__(self, use_neural_sim: bool = False) -> None:
        """Initialize all cognitive subsystems.

        Args:
            use_neural_sim: If True, enables the neural simulation engine
                          for concept activation and association using
                          vectorized populations and brain regions.
                          Default False preserves Phase 0 behavior.
        """
        # Identity
        self.name: str | None = None
        self.user_name: str | None = None
        self.use_neural_sim: bool = use_neural_sim

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

        # Neural simulation (Phase 1)
        self._neural_sim_engine = None
        self._neural_regions: Dict[str, Any] = {}
        self._concept_encoder = None
        self._neural_network = None
        if use_neural_sim:
            self._init_neural_simulation()

    def _init_neural_simulation(self) -> None:
        """Initialize the neural simulation engine with brain regions.

        Creates vectorized populations for sensory, association, and memory
        regions, connects them via a synaptic network, and sets up the
        simulation engine and concept encoder.
        """
        from brain.encoding.concept_encoder import ConceptEncoder
        from brain.regions.association import AssociationRegion
        from brain.regions.memory_region import MemoryRegion
        from brain.regions.sensory import SensoryRegion
        from brain.simulation.config import SimulationConfig
        from brain.simulation.engine import SimulationEngine
        from brain.synapses.network import SynapticNetwork

        # Create brain regions
        sensory = SensoryRegion(name="sensory", size=256, gain=2.0)
        association = AssociationRegion(name="association", size=512)
        memory = MemoryRegion(name="memory", size=512)

        self._neural_regions = {
            "sensory": sensory,
            "association": association,
            "memory": memory,
        }

        # Create synaptic network
        network = SynapticNetwork()
        network.connect_populations(
            sensory.population,
            association.population,
            probability=0.1,
            weight_range=(0.02, 0.08),
            seed=42,
        )
        network.connect_populations(
            association.population,
            memory.population,
            probability=0.08,
            weight_range=(0.02, 0.06),
            seed=43,
        )
        # Recurrent connections in association cortex
        network.connect_self(association.population, probability=0.05, weight_range=(0.01, 0.04), seed=44)
        self._neural_network = network

        # Create simulation engine
        config = SimulationConfig(
            record_spikes=True,
            record_rates=True,
            stdp_enabled=True,
        )
        regions_list = [sensory, association, memory]
        self._neural_sim_engine = SimulationEngine(regions_list, network, config)

        # Concept encoder for neural patterns
        self._concept_encoder = ConceptEncoder(population_size=512, sparsity=0.07)

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

        is_question = "?" in text_input or "\u0995\u09c7" in text_input or "\u0995\u09bf" in text_input
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

        self.working_memory.store(
            "parse_result",
            {
                "intent": parse_result.intent.value,
                "entities": parse_result.entities,
                "relations": parse_result.relations,
                "query": parse_result.query,
            },
        )

        return CycleResult(
            phase=CognitivePhase.INTERPRET,
            data={
                "parse_result": parse_result,
                "intent": parse_result.intent.value,
            },
            success=parse_result.confidence > 0.3,
        )

    def _phase_recall(self, parse_result: ParseResult | None) -> CycleResult:
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
                    {"subject": f.subject, "predicate": f.predicate, "obj": f.obj} for f in facts
                ]

            # Search episodic memory: past interactions about this target
            # (experience-based recall, not just stored facts)
            episode_hits = self.episodic_memory.recall_by_content(target_name)
            if episode_hits:
                recalled["episode_hits"] = [
                    {
                        "event": ep.content.get("event") if isinstance(ep.content, dict) else str(ep.content),
                        "result": ep.content.get("result") if isinstance(ep.content, dict) else "",
                        "importance": ep.importance,
                    }
                    for ep in episode_hits[:5]
                ]

            # Search knowledge graph
            target_concept = self.concept_graph.get_concept_by_name(target_name)
            if target_concept:
                relations = self.concept_graph.get_relations(target_concept.concept_id, direction="incoming")
                recalled["graph_relations"] = relations

        return CycleResult(
            phase=CognitivePhase.RECALL,
            data=recalled,
            success=True,
        )

    def _phase_associate(self, parse_result: ParseResult | None) -> CycleResult:
        """ASSOCIATE phase: Spread activation to related concepts.

        If neural simulation is enabled, uses the neural engine to
        spread activation via spike propagation through the synaptic
        network. Otherwise, uses the graph-based spreading activation.
        """
        self.state.current_phase = "associate"
        activated: Dict[str, float] = {}

        if parse_result:
            entities = parse_result.entities
            target = entities.get("target") or entities.get("name") or parse_result.query.get("target")

            if target:
                concept = self.concept_graph.get_concept_by_name(target)
                if concept:
                    if self.use_neural_sim and self._neural_sim_engine is not None:
                        # Neural simulation path: encode concept and run simulation
                        activated = self._neural_associate(concept.concept_id)
                    else:
                        # Graph-based path (Phase 0 default)
                        activation_map = self.spreading_activation.activate(self.concept_graph, concept.concept_id)
                        activated = activation_map

                    self.state.active_concepts = {k: round(v, 3) for k, v in activated.items()}

        return CycleResult(
            phase=CognitivePhase.ASSOCIATE,
            data={"activation_map": activated},
            success=True,
        )

    def _neural_associate(self, concept_id: str) -> Dict[str, float]:
        """Run neural association using the simulation engine.

        Encodes the concept as a spike pattern, injects it into the
        sensory region, runs the simulation for a few steps, and
        reads out activations from the association region.

        Args:
            concept_id: The concept to activate neurally.

        Returns:
            Dictionary mapping concept IDs to activation levels.
        """
        if self._concept_encoder is None or self._neural_sim_engine is None:
            return {}

        # Encode concept as spike pattern
        pattern = self._concept_encoder.encode_concept(concept_id)

        # Inject into sensory region
        sensory = self._neural_regions.get("sensory")
        if sensory is None:
            return {}

        # Resize pattern to sensory region size
        sensory_input = np.zeros(sensory.size, dtype=np.float64)
        n = min(len(pattern), sensory.size)
        sensory_input[:n] = pattern[:n] * sensory.population.threshold[0] * 2.0
        sensory.receive_input(sensory_input)

        # Run simulation for a few steps
        for _ in range(5):
            self._neural_sim_engine.step()

        # Read association region activity as activation map
        association = self._neural_regions.get("association")
        if association is None:
            return {}

        # Convert spikes to activation levels
        activation_map: Dict[str, float] = {}
        rate = association.get_firing_rate()
        if rate > 0:
            activation_map[concept_id] = min(1.0, rate * 10.0)

        # Check other known concepts
        for cid in self._concept_encoder.get_all_concepts():
            if cid != concept_id:
                c_pattern = self._concept_encoder.patterns[cid]
                # Check overlap with current association activity
                assoc_activity = association.output_spikes.astype(np.float64)
                if np.sum(assoc_activity) > 0:
                    # Simple overlap score
                    resized_pattern = np.zeros(association.size, dtype=np.float64)
                    m = min(len(c_pattern), association.size)
                    resized_pattern[:m] = c_pattern[:m]
                    overlap = np.dot(assoc_activity, resized_pattern)
                    if overlap > 0:
                        activation_map[cid] = min(1.0, float(overlap) / 5.0)

        return activation_map

    def _phase_reason(self, parse_result: ParseResult | None) -> CycleResult:
        """REASON phase: Apply inference rules."""
        self.state.current_phase = "reason"
        derived: List[Dict[str, Any]] = []

        if parse_result and parse_result.intent == IntentType.QUERY_WHO:
            target_name = parse_result.query.get("target", "")
            relation = parse_result.query.get("relation", "")

            target_concept = self.concept_graph.get_concept_by_name(target_name)
            if target_concept:
                related = self.concept_graph.find_related(
                    target_concept.concept_id,
                    relation_type=relation,
                    direction="incoming",
                )
                if related:
                    derived = [{"answer": c.name, "relation": relation} for c in related]

        # Consult procedural memory: apply the strongest learned
        # if-then procedure matching the current context so stored
        # procedures actually influence reasoning instead of sitting idle
        context = parse_result.raw_text if parse_result else ""
        if context and hasattr(self, "procedural_memory") and self.procedural_memory.size > 0:
            procedure = self.procedural_memory.get_strongest(context)
            if procedure:
                procedure.reinforce(success=True, amount=0.05)
                derived.append(
                    {
                        "procedure": procedure.name,
                        "action": procedure.action,
                        "strength": procedure.strength,
                    }
                )
        return CycleResult(
            phase=CognitivePhase.REASON,
            data={"derived": derived},
            success=True,
        )

    def _phase_plan(self, parse_result: ParseResult | None) -> CycleResult:
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
        parse_result: ParseResult | None,
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
            # Unknown/unsupported input: give a contextual fallback instead
            # of a flat "I don't know" so the user understands the brain's
            # current capability boundary and what it CAN learn.
            response, confidence = self._act_unknown(parse_result)

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
                subject=name,
                predicate="is_a",
                obj="Person",
            )
            if is_self:
                self.semantic_memory.store_fact(
                    subject=name,
                    predicate="is",
                    obj="user",
                )

        # Register concept in neural encoder if simulation is active
        if self.use_neural_sim and self._concept_encoder is not None:
            self._concept_encoder.encode_concept(name)

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
            source_concept = self.concept_graph.create_concept(name=source_name, concept_type="Person")

        target_concept = self.concept_graph.get_concept_by_name(target_name)
        if not target_concept:
            target_concept = self.concept_graph.create_concept(name=target_name, concept_type="Entity")

        # Add relation to graph
        self.concept_graph.add_relation(
            source_id=source_concept.concept_id,
            target_id=target_concept.concept_id,
            relation_type=relation_type,
        )

        # Store in semantic memory
        self.semantic_memory.store_fact(
            subject=source_name,
            predicate=relation_type,
            obj=target_name,
        )

        # Register concepts in neural encoder if simulation is active
        if self.use_neural_sim and self._concept_encoder is not None:
            self._concept_encoder.encode_concept(source_name)
            self._concept_encoder.encode_concept(target_name)

        response = f"I have learned that {source_name} has relation '{relation_type}' with {target_name}."
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
        return (f"I do not have information about who has '{relation}' relation with {target_name}."), 0.3

    def _act_unknown(self, parse_result: ParseResult) -> tuple:
        """Handle inputs the brain cannot yet understand.

        Gives a contextual fallback response that acknowledges the input,
        signals humility (low confidence), and invites the user to teach
        the brain using supported phrasings. This keeps the conversation
        flowing instead of dead-ending on unknown input.
        """
        raw = parse_result.raw_text or "your message"
        self.emotion.update_from_outcome(success=False)
        # Remember the unknown input as a learning opportunity
        self.working_memory.store("unknown_input", raw)
        response = (
            "I heard you, but I am still learning and cannot fully "
            "understand that yet. You can teach me things like "
            '"আমার নাম X", "আমি Y-এর creator", or ask '
            '"Y কে তৈরি করেছে?"'
        )
        return response, 0.3

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

    def _phase_learn(self, parse_result: ParseResult | None, act_result: CycleResult) -> CycleResult:
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

        # Store the interaction as an episodic memory so experiences can
        # be recalled later (event + context + action + result + reward).
        episode = {
            "event": self.state.last_input if not parse_result else parse_result.raw_text,
            "intent": state_key,
            "action": action_key,
            "result": act_result.data.get("response", ""),
            "reward": reward,
            "context": {
                "user_name": self.user_name,
                "cycle_count": self.cycle.cycle_count,
            },
        }
        self.episodic_memory.store(
            content=episode,
            emotional_valence=reward,
            importance=confidence,
        )

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
        state_dict = {
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

        # Add neural simulation state if active
        if self.use_neural_sim and self._neural_sim_engine is not None:
            state_dict["neural_simulation"] = {
                "enabled": True,
                "regions": list(self._neural_regions.keys()),
                "simulation_step": self._neural_sim_engine.current_step,
            }

        return state_dict

    def __repr__(self) -> str:
        sim_info = ", neural_sim=True" if self.use_neural_sim else ""
        return (
            f"Brain(cycles={self.cycle.cycle_count}, "
            f"concepts={self.concept_graph.num_concepts}, "
            f"relations={self.concept_graph.num_relations}{sim_info})"
        )
