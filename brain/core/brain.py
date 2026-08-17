"""
Main Brain Class.

The central orchestrator that initializes all subsystems and
processes input through the cognitive cycle. This is the primary
entry point for the cognitive system.
"""

import time as time_module
from typing import Any, Dict, List

import numpy as np

from brain.actuators import ActuatorBridge
from brain.core.cycle import CognitiveCycle, CognitivePhase, CycleResult
from brain.core.state import BrainState
from brain.dialogue.context import DialogueContext
from brain.emotion.state import EmotionalState
from brain.goals.manager import GoalManager
from brain.graph.activation import SpreadingActivation
from brain.graph.concepts import ConceptGraph
from brain.graph.hebbian import HebbianLearner
from brain.learning.consolidation import MemoryConsolidator
from brain.learning.curiosity import CuriosityExplorer
from brain.learning.reinforcement import ReinforcementLearner
from brain.learning.reward import RewardSignal
from brain.math_engine import MATH_ENGINE
from brain.memory.episodic import EpisodicMemory
from brain.memory.procedural import ProceduralMemory
from brain.memory.semantic import SemanticMemory
from brain.memory.weighted_recall import WeightedRecall
from brain.memory.working import WorkingMemory
from brain.neurons.populations import NeuronPopulation
from brain.nlu.coreference import resolve_entities
from brain.nlu.parser import IntentType, NLUParser, ParseResult
from brain.physics_engine import PHYSICS_ENGINE
from brain.planner.planner import Planner
from brain.reasoning.inference import InferenceEngine
from brain.reflection.reflection import ReflectionEngine
from brain.sensors import SensorEvent, SensorHub
from brain.synapses.plasticity import PlasticityManager
from brain.world import WorldModel


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
        # Phase 4: associative learning depth
        self.hebbian = HebbianLearner()
        self.recall_scorer = WeightedRecall()
        self.curiosity = CuriosityExplorer()
        # Phase 5: world model (entity registry + intent prediction)
        self.world = WorldModel()
        # Phase 6: goal-driven behavior (hierarchical decomposition)
        self.goal_manager = GoalManager()
        # Phase 9: hardware sensor abstraction (transport-agnostic)
        self.sensors = SensorHub()
        # Phase 10: physical robot actuators (safety-gated)
        self.actuators = ActuatorBridge()

        # Meta-cognition
        self.reflection = ReflectionEngine()

        # Emotion
        self.emotion = EmotionalState()

        # NLU
        self.nlu = NLUParser()

        # Multi-turn dialogue context (Phase 3)
        self.dialogue_context = DialogueContext()

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

        # Identity: self-knowledge and training data are injected at
        # initialization so MISTY knows who she is from the very first
        # interaction. Runs after the neural encoder exists so trained
        # concepts can be registered in the simulation.
        self._inject_training_knowledge()

    def _inject_training_knowledge(self) -> None:
        """Inject identity and general training knowledge at startup.

        Seeds the knowledge graph (concepts and relations), semantic
        memory (facts), and the persistence database so MISTY knows her
        own identity — a Smart Artificial Brain created by Pixline
        Incorporate (founder Salauddin Mir, known as Netvai) — from the
        very first interaction, and remembers it across restarts.
        """
        from brain.knowledge.training import combined_package

        package = combined_package()

        # Register concepts and their relations in the knowledge graph
        created_concepts: Dict[str, str] = {}  # name -> concept_id
        for entry in package.concepts:
            name = entry["name"]
            if name not in created_concepts and self.concept_graph.get_concept_by_name(name) is None:
                concept = self.concept_graph.create_concept(
                    name=name,
                    concept_type=entry.get("type", "Entity"),
                )
                created_concepts[name] = concept.concept_id

        # Ensure all relation endpoints exist in the graph
        for entry in package.relations:
            for endpoint in ("source", "target"):
                name = entry[endpoint]
                if name not in created_concepts and self.concept_graph.get_concept_by_name(name) is None:
                    concept = self.concept_graph.create_concept(
                        name=name,
                        concept_type="Entity",
                    )
                    created_concepts[name] = concept.concept_id

        # Add directed relations between concepts
        for entry in package.relations:
            source_id = created_concepts.get(entry["source"])
            target_id = created_concepts.get(entry["target"])
            if source_id and target_id:
                self.concept_graph.add_relation(
                    source_id=source_id,
                    target_id=target_id,
                    relation_type=entry["type"],
                    weight=1.0,
                    confidence=1.0,
                )

        # Store facts in semantic memory for fast recall
        for fact in package.facts:
            self.semantic_memory.store_fact(
                subject=fact["subject"],
                predicate=fact["predicate"],
                obj=fact["obj"],
                confidence=1.0,
                source="training",
            )

        # Register trained concepts in the neural encoder when active
        if self.use_neural_sim and self._concept_encoder is not None:
            for name in created_concepts:
                self._concept_encoder.encode_concept(name)

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
        return self._run_cycle(text_input=text_input, source="text")

    def process_sensor_event(self, event: SensorEvent) -> Dict[str, Any]:
        """Process a hardware sensor reading through the cognitive cycle.

        The event is rendered as a structured statement (e.g. "sensor
        distance 0.35") so sensors feed the same learning path as
        language. The percept is also registered in the world model.
        """
        self.world.add_entity(
            entity_id=f"sensor:{event.sensor_id}",
            entity_type="sensor",
            attributes={
                "event_type": event.event_type,
                "unit": event.unit,
                "last_value": event.value,
                "last_seen": event.timestamp,
            },
        )
        return self._run_cycle(text_input=event.text_input, source="sensor", sensor_event=event)

    def _run_cycle(
        self,
        text_input: str,
        source: str = "text",
        sensor_event: SensorEvent | None = None,
    ) -> Dict[str, Any]:
        """Shared cognitive-cycle implementation for text and sensor input."""
        start_time = time_module.time()
        self.state.last_input = text_input

        # Record the user turn in the dialogue context so later turns
        # can resolve pronouns ("সে", "it", "its") back to this turn.
        self.dialogue_context.add_turn(text_input, role="user")

        # Start cognitive cycle
        self.cycle.start_cycle()

        # Phase 1: OBSERVE
        observe_result = self._phase_observe(text_input)
        self.cycle.advance(observe_result)

        # Phase 2: INTERPRET
        interpret_result = self._phase_interpret(text_input, source=source)
        self.cycle.advance(interpret_result)
        # Phase 5: compare actual intent against the prediction; the
        # resulting prediction error is stored in the brain state and can
        # feed downstream learners.
        actual_intent = interpret_result.data.get("intent", "unknown")
        intent_outcome = self.world.record_intent(actual_intent)
        # Phase 5: entities mentioned in the input join the world model
        # (location is inferred from dialogue context when present).
        parse_result_obj = interpret_result.data.get("parse_result")
        entities = getattr(parse_result_obj, "entities", {}) or {}
        if isinstance(entities, dict):
            for candidate in entities.values():
                if isinstance(candidate, str) and candidate and candidate not in self._PRONOUN_TOKENS:
                    self.world.add_entity(candidate, "concept")
                elif isinstance(candidate, list):
                    for item in candidate:
                        if isinstance(item, str) and item and item not in self._PRONOUN_TOKENS:
                            self.world.add_entity(item, "concept")

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
        # Keep the interpreted intent accessible to API consumers.
        intent_value = interpret_result.data.get("intent", "unknown") if interpret_result is not None else "unknown"

        # Record the brain turn so the next user turn can resolve
        # pronouns back to this exchange.
        self.dialogue_context.add_turn(
            text=response,
            role="brain",
            entities=self.dialogue_context.extract_from_text(response)
            if hasattr(self.dialogue_context, "extract_from_text")
            else None,
            intent=(interpret_result.data.get("intent", "unknown") if interpret_result is not None else "unknown"),
        )
        self.state.cycle_count = self.cycle.cycle_count
        self.state.current_phase = "idle"
        self.state.timestamp = time_module.time()

        # Phase 5: expose prediction outcome in the returned state.
        self.state.last_prediction_error = intent_outcome.get("error", 0.0)
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
            "intent": intent_value,
            "confidence": act_result.data.get("confidence", 0.5),
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

    def _phase_interpret(self, text_input: str, source: str = "text") -> CycleResult:
        """INTERPRET phase: Parse input using NLU."""
        self.state.current_phase = "interpret"
        parse_result = self.nlu.parse(text_input)
        if source == "sensor" and parse_result.intent == IntentType.PHYSICS:
            parse_result.intent = IntentType.STATEMENT
            parse_result.confidence = 0.8

        # Phase 3 coreference resolution: map pronoun-targeted queries and
        # pronoun-only inputs to the most salient entity from the ongoing
        # conversation (e.g. "সে কে?" -> target = last mentioned name).
        self._resolve_coreference(parse_result)

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

    def _resolve_coreference(self, parse_result: ParseResult) -> None:
        """Resolve pronoun references in a freshly parsed result.

        Empty or pronoun query targets are replaced with the most
        salient entity from the dialogue context, and pronoun-only
        inputs inherit that entity so the ACT phase can answer them.
        """
        salient = self.dialogue_context.get_salient_entities()
        if not salient:
            return

        target = parse_result.query.get("target", "")
        if parse_result.intent in (IntentType.QUERY_WHO, IntentType.QUERY_WHAT):
            if not target or target in self._PRONOUN_TOKENS:
                parse_result.query["target"] = salient[0]
                parse_result.entities["coreference_target"] = salient[0]

        if not parse_result.entities and parse_result.intent in (
            IntentType.STATEMENT,
            IntentType.UNKNOWN,
            IntentType.CONTINUATION,
            IntentType.CORRECTION,
            IntentType.TEACH,
        ):
            resolved = resolve_entities(parse_result.raw_text, salient)
            if resolved:
                parse_result.entities["resolved_entities"] = resolved

    def _curiosity_prompt(self, activation_map: Dict[str, float]) -> str | None:
        """Phase 4 curiosity: ask about an under-explored neighbor concept.

        Returns a Bengali question or None when curiosity stays below
        threshold (high urgency, well-known neighbors, cooldown).
        """
        if not activation_map:
            return None
        suggestion = self.curiosity.evaluate(
            self.concept_graph,
            activation_map,
            urgency=self.emotion.to_dict().get("urgency", 0.0),
            satisfaction=self.emotion.to_dict().get("satisfaction", 0.0),
        )
        question = suggestion.get("question")
        if question:
            self.working_memory.store("curiosity_target", suggestion.get("target"))
            self.working_memory.store("curiosity_bonus", suggestion.get("bonus", 0.0))
        return question

    _PRONOUN_TOKENS = frozenset(
        {
            # Bengali pronouns
            "সে",
            "তার",
            "এটা",
            "ওটা",
            "এই",
            "সেই",
            "এ",
            "ও",
            "তারা",
            # English pronouns
            "it",
            "its",
            "him",
            "her",
            "he",
            "she",
            "this",
            "that",
            "these",
            "those",
            "them",
            "their",
        }
    )

    def _phase_recall(self, parse_result: ParseResult | None) -> CycleResult:
        """RECALL phase: Retrieve relevant memories."""
        self.state.current_phase = "recall"
        recalled: Dict[str, Any] = {}

        if parse_result:
            # Phase 4: mark recalled targets and score by recency/
            # frequency/emotion so retrieval favors human-like recall.
            target_name = parse_result.query.get("target", "")
            if target_name:
                target_concept = self.concept_graph.get_concept_by_name(target_name)
                if target_concept:
                    self.recall_scorer.record_recall(target_concept.concept_id)
                    recalled["recall_scores"] = self.recall_scorer.score(
                        target_concept.concept_id,
                        emotional_valence=self._current_valence(),
                    )

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
                    # Phase 4: Hebbian learning — strengthen edges between
                    # concepts that fired together this cycle.
                    hebbian_updates = self.hebbian.update(self.concept_graph, list(activated.keys()))
                    if hebbian_updates:
                        self.working_memory.store("hebbian_updates", hebbian_updates)
        # Phase 4: Hebbian bookkeeping (also covers the neural path).
        self.hebbian.register_activations(self.state.active_concepts.keys())
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
        """PLAN phase: Decide what to do.

        Phase 6: the current intent is decomposed into a hierarchical goal
        with ordered plan steps so the next cycles can drive progress
        tracking step by step.
        """
        self.state.current_phase = "plan"
        if not parse_result:
            return CycleResult(
                phase=CognitivePhase.PLAN,
                data={"plan": "acknowledge"},
                success=True,
            )
        intent = parse_result.intent.value
        # Priority: corrections and queries matter more than greetings.
        priority = {
            "correction": 0.9,
            "teach": 0.8,
            "query_who": 0.85,
            "query_what": 0.85,
            "relation_declaration": 0.7,
            "name_declaration": 0.7,
            "statement": 0.6,
            "continuation": 0.5,
            "greeting": 0.4,
        }.get(intent, 0.5)
        goal = self.goal_manager.decompose_hierarchy(
            intent=intent,
            description=f"handle {intent}: {parse_result.raw_text[:60]}",
            priority=priority,
        )
        self.state.context["active_goal"] = goal.goal_id

        if parse_result.intent == IntentType.NAME_DECLARATION:
            plan = "store_identity"
        elif parse_result.intent == IntentType.RELATION_DECLARATION:
            plan = "store_relation"
        elif parse_result.intent in (IntentType.QUERY_WHO, IntentType.QUERY_WHAT):
            plan = "answer_query"
        elif parse_result.intent == IntentType.GREETING:
            plan = "greet_back"
        elif parse_result.intent == IntentType.MATH:
            plan = "solve_mathematics"
        elif parse_result.intent == IntentType.PHYSICS:
            plan = "solve_physics"
        elif parse_result.intent in (IntentType.TEACH, IntentType.STATEMENT, IntentType.CORRECTION):
            plan = "absorb_knowledge"
        elif parse_result.intent == IntentType.CONTINUATION:
            plan = "continue_topic"
        else:
            plan = "acknowledge"
        return CycleResult(
            phase=CognitivePhase.PLAN,
            data={"plan": plan, "active_goal": goal.goal_id},
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

        elif parse_result.intent == IntentType.QUERY_WHAT:
            response, confidence = self._act_query_what(parse_result, recall_data)

        elif parse_result.intent == IntentType.STATEMENT:
            response, confidence = self._act_statement(parse_result)

        elif parse_result.intent == IntentType.TEACH:
            response, confidence = self._act_teach(parse_result)

        elif parse_result.intent == IntentType.CORRECTION:
            response, confidence = self._act_correction(parse_result)

        elif parse_result.intent == IntentType.CONTINUATION:
            response, confidence = self._act_continuation(parse_result)

        elif parse_result.intent == IntentType.GREETING:
            name_part = f", {self.user_name}" if self.user_name else ""
            response = (
                f"হ্যালো{name_part}! আমি Misty - Smart Artificial Brain, "
                f"Pixline Incorporate-এর তৈরি। কীভাবে সাহায্য করতে পারি?"
            )
            confidence = 0.9

        elif parse_result.intent == IntentType.MATH:
            response, confidence = self._act_math(parse_result)

        elif parse_result.intent == IntentType.PHYSICS:
            response, confidence = self._act_physics(parse_result)

        else:
            # Unknown/unsupported input: give a contextual fallback instead
            # of a flat "I don't know" so the user understands the brain's
            # current capability boundary and what it CAN learn.
            response, confidence = self._act_unknown(parse_result)

        # Phase 4: curiosity-driven exploration — when an under-explored
        # neighbor concept earns a bonus above threshold, append a question
        # so the agent actively seeks missing knowledge.
        curiosity_question = self._curiosity_prompt(self.state.active_concepts)
        if curiosity_question:
            response = (response + " " + curiosity_question) if response else curiosity_question

        return CycleResult(
            phase=CognitivePhase.ACT,
            data={"response": response, "confidence": confidence},
            success=confidence > 0.5,
        )

    def _act_math(self, parse_result: ParseResult) -> tuple:
        """Solve a supported math query without an LLM."""
        text = parse_result.entities.get("math_text", parse_result.raw_text)
        result = MATH_ENGINE.solve(text)
        if result is None:
            return (
                "আমি এই mathematical format-টি এখনো সমর্থন করি না। উদাহরণ: calculate 2 + 2 অথবা 2x + 4 = 10 সমাধান করো।",
                0.3,
            )
        self.state.context["last_math_result"] = {
            "category": result.category,
            "exact": result.exact,
            "steps": list(result.steps),
        }
        return result.answer, result.confidence

    def _act_physics(self, parse_result: ParseResult) -> tuple:
        """Solve a supported Physics query without an LLM."""
        text = parse_result.entities.get("physics_text", parse_result.raw_text)
        result = PHYSICS_ENGINE.solve(text)
        if result is None:
            return (
                "এই Physics format-টি এখনো সমর্থিত নয়। উদাহরণ: velocity distance 100 time 20 "
                "অথবা force mass 5 acceleration 2।",
                0.3,
            )
        self.state.context["last_physics_result"] = {
            "category": result.category,
            "exact": result.exact,
            "steps": list(result.steps),
        }
        return result.answer, result.confidence

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

        # Identity shortcuts: if asked about MISTY herself, answer from
        # self-knowledge before the generic graph/semantic lookup so the
        # answer always reflects the trained identity.
        if target_name.lower() == "misty":
            return self._act_query_self(parse_result)

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

    def _act_query_self(self, parse_result: ParseResult) -> tuple:
        """Answer identity questions about MISTY herself.

        Produces a contextual self-introduction from the trained
        self-knowledge graph rather than a bare relation lookup, so
        questions like "who are you?", "মিস্টি কে?", "who created you?"
        receive a complete and confident identity answer.
        """
        relation = parse_result.query.get("relation", "")
        if relation in ("creator_of", "made_by"):
            return (
                "আমি Misty - Smart Artificial Brain। আমাকে তৈরি করেছে "
                "Pixline Incorporate, যার Founder হলেন Salauddin Mir (Netvai নামে পরিচিত)। "
                "আমি হলো ভারতের প্রথম Smart AI Brain যেটি কোনো LLM-এর উপর নির্ভরশীল নয়।"
            ), 0.95
        # Default: full self-introduction
        return (
            "আমি Misty - Smart Artificial Brain। আমি Pixline Incorporate-এর তৈরি "
            "একটি কৃত্রিম কগনিটিভ সিস্টেম — ভারতের প্রথম Smart AI Brain যেটি "
            "কোনো LLM dependency ছাড়াই কাজ করে। আমার তৈরিকারী হলেন "
            "Salauddin Mir, যিনি Netvai নামে পরিচিত। আমি স্পাইকিং নিউরাল নেটওয়ার্ক "
            "ও নলেজ গ্রাফ ব্যবহার করি এবং বাংলা ও ইংরেজি দুই ভাষায় কথা বলতে পারি।"
        ), 0.95

    def _act_query_what(self, parse_result: ParseResult, recall_data: Dict[str, Any]) -> tuple:
        """Handle definition (is_a / means) queries like "মিস্টি মানে কী?".

        Looks up is_a facts in the knowledge graph and semantic memory,
        and falls back to a humble "still learning" answer that mentions
        the asked-about entity so the user can teach it.
        """
        target_name = parse_result.query.get("target", "")
        if not target_name:
            return self._act_unknown(parse_result)

        facts = self.semantic_memory.query(subject=target_name, predicate="is_a")
        if facts:
            definitions = [fact.obj for fact in facts]
            return f"{target_name} হলো {', '.join(definitions[:3])}।", 0.9

        concept = self.concept_graph.get_concept_by_name(target_name)
        if concept and concept.concept_type and concept.concept_type != "Entity":
            return f"{target_name} হলো {concept.concept_type}।", 0.8

        recalled = recall_data.get("semantic_facts", [])
        for fact in recalled:
            if fact.get("subject") == target_name and fact.get("predicate") == "is_a":
                return f"{target_name} হলো {fact.get('obj', '')}।", 0.85

        self.emotion.update_from_outcome(success=False)
        return (f'আমি এখনো {target_name} সম্পর্কে জানি না। আপনি বলতে পারেন: "{target_name} হলো X" — তাহলে আমি মনে রাখব।'), 0.3

    def _act_statement(self, parse_result: ParseResult) -> tuple:
        """Handle ordinary assertions like "মিস্টি হলো এআই" (is_a fact)
        or plain statements without actionable structure.

        Extracted is_a facts are stored in the knowledge graph and
        semantic memory; unresolved statements are acknowledged with
        context-aware humility referencing recent conversation.
        """
        facts = parse_result.facts if hasattr(parse_result, "facts") and parse_result.facts else []
        stored = []
        for fact in facts:
            subject = fact.get("subject", "").strip()
            obj = fact.get("obj", "").strip()
            if not subject or not obj:
                continue
            concept = self.concept_graph.get_concept_by_name(subject)
            if not concept:
                concept = self.concept_graph.create_concept(name=subject, concept_type="Entity")
            target = self.concept_graph.get_concept_by_name(obj)
            if not target:
                target = self.concept_graph.create_concept(name=obj, concept_type="Category")
            self.concept_graph.add_relation(
                source_id=concept.concept_id,
                target_id=target.concept_id,
                relation_type="is_a",
            )
            self.semantic_memory.store_fact(subject=subject, predicate="is_a", obj=obj)
            if self.use_neural_sim and self._concept_encoder is not None:
                self._concept_encoder.encode_concept(subject)
                self._concept_encoder.encode_concept(obj)
            stored.append(f"{subject} -> is_a -> {obj}")

        if stored:
            response = f"ধন্যবাদ! আমি শিখেছি: {', '.join(stored)}। এটা আমার জ্ঞান গ্রাফে সংরক্ষিত হয়েছে।"
            return response, 0.9

        # Plain statement without extractable facts: acknowledge using
        # the current conversation context so it does not feel robotic.
        salient = self.dialogue_context.get_salient_entities()
        context_hint = salient[0] if salient else ""
        context_part = f" ({context_hint} নিয়ে)" if context_hint else ""
        return (
            f"আমি আপনার কথাটি শুনলাম{context_part}, কিন্তু এখনো "
            "এটি সম্পূর্ণ বুঝতে শিখিনি। আপনি চাইলে শেখাতে পারেন: "
            '"মনে রাখো ..." বা "X হলো Y" ফরম্যাটে।'
        ), 0.5

    def _act_teach(self, parse_result: ParseResult) -> tuple:
        """Handle explicit teaching ("মনে রাখো ...", "I know that ...").

        The full statement is stored verbatim in episodic memory and the
        extracted fact (if any) is added to the semantic layer.
        """
        raw = parse_result.raw_text
        facts = parse_result.facts if hasattr(parse_result, "facts") and parse_result.facts else []
        for fact in facts:
            subject, obj = fact.get("subject", ""), fact.get("obj", "")
            if subject and obj:
                self.semantic_memory.store_fact(subject=subject, predicate="is_a", obj=obj)
                self.episodic_memory.store(
                    content={"type": "taught_fact", "subject": subject, "obj": obj},
                    emotional_valence=0.7,
                    importance=0.8,
                )
                return f"মনে রাখা হয়েছে: {subject} হলো {obj}।", 0.9

        self.episodic_memory.store(
            content={"type": "taught_statement", "text": raw},
            emotional_valence=0.6,
            importance=0.7,
        )
        return f"আমি মনে রাখলাম: {raw}", 0.7

    def _act_correction(self, parse_result: ParseResult) -> tuple:
        """Handle corrections ("আসলে মিস্টি", "no, it is Misty").

        Treats the first resolved entity in the correction as the
        intended identity and acknowledges it.
        """
        candidates = []
        for value in parse_result.entities.values():
            if isinstance(value, str) and value:
                candidates.append(value)
            elif isinstance(value, list):
                candidates.extend(v for v in value if isinstance(v, str))
        if candidates:
            correction_target = candidates[0]
            return (f"ধন্যবাদ সংশোধনের জন্য। আপনি ঠিক বলছেন — {correction_target}। আমি এটা মনে রাখলাম।"), 0.8
        return ("আমি বুঝতে পেরেছি আপনি সংশোধন করছেন, কিন্তু কী সংশোধন করতে চাইছেন সেটা স্পষ্ট করে বলুন।"), 0.5

    def _act_continuation(self, parse_result: ParseResult) -> tuple:
        """Handle conversational continuations ("আরো বলো", "more").

        Reuses the most salient topic from the ongoing dialogue so the
        brain keeps talking about what the user just asked about.
        """
        salient = self.dialogue_context.get_salient_entities()
        topic = salient[0] if salient else None
        if not topic:
            name_part = f" আপনার নাম {self.user_name}" if self.user_name else ""
            return (
                f"আপনি আমাকে আলো করার জন্য বলছেন{name_part}, কিন্তু "
                "আমার মনে এখনো আগের কোনো টপিক নেই যেটা আমি আরো বলতে "
                "পারি। আমাকে কিছু শেখান বা কিছু জিজ্ঞেস করুন।"
            ), 0.6

        facts = self.semantic_memory.query(subject=topic, predicate="is_a")
        if facts:
            detail = ", ".join(fact.obj for fact in facts[:2])
            return (
                f"আমি {topic} নিয়ে বলছি — {topic} হলো {detail}। এর বেশি জানতে চাইলে বলুন 'আমি {topic}-এর তথ্য দাও'।"
            ), 0.8

        topic_concept = self.concept_graph.get_concept_by_name(topic)
        related = []
        if topic_concept:
            related = self.concept_graph.find_related(topic_concept.concept_id, direction="outgoing")
        if related:
            names = [concept.name for concept in related[:3]]
            return f"{topic} নিয়ে আমার জ্ঞান: সম্পর্কিত ধারণা — {', '.join(names)}।", 0.7
        return (f"{topic} নিয়ে আমি এখনো বেশি কিছু জানি না। আপনি কি আমাকে আরো শেখাবেন?"), 0.5

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
        # Phase 6: advance the active goal's plan progress. Root goals
        # only achieve once their children are done, so drive progress on
        # the deepest (leaf) active goal each cycle.
        leaf = self.goal_manager.leaf_active_goal()
        goal_update: Dict[str, Any] = {}
        if leaf is not None:
            goal_update = self.goal_manager.advance_goal(leaf.goal_id)
            # Reward shaping: reward proportional to goal progress.
            self.learner.update(
                f"goal_{leaf.intent}",
                action_key,
                reward + 0.1 * goal_update.get("progress", 0.0),
            )
        return CycleResult(
            phase=CognitivePhase.LEARN,
            data={"reward": reward, "goal_update": goal_update},
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
        # Phase 4: slowly decay unused Hebbian edge weights so the graph
        # forgets weak associations over time.
        decayed = self.hebbian.decay_unused(self.concept_graph)
        if decayed:
            self.working_memory.store("hebbian_decay", len(decayed))
        # Phase 4: tick curiosity cooldowns once per cycle.
        self.curiosity.step_cooldowns()
        # Phase 6: prune terminal goals once the registry exceeds
        # capacity so the goal history stays bounded.
        goal_stats = self.goal_manager.stats()
        pruned = goal_stats.get("achieved", 0) + goal_stats.get("abandoned", 0)
        return CycleResult(
            phase=CognitivePhase.CONSOLIDATE,
            data={
                "consolidated_keys": consolidated,
                "hebbian_decayed": len(decayed),
                "goal_stats": goal_stats,
                "pruned_terminal_goals": pruned,
            },
            success=True,
        )

    def _current_valence(self) -> float:
        """Current emotional valence as a signed scalar in [-1, 1].

        Positive emotions contribute positively, negative ones
        negatively; used by the recall scorer.
        """
        emotions = self.emotion.to_dict()
        positive = sum(emotions.get(k, 0.0) for k in ("satisfaction", "confidence", "curiosity"))
        negative = sum(emotions.get(k, 0.0) for k in ("frustration", "urgency", "uncertainty"))
        total = positive + negative
        if total <= 0:
            return 0.0
        return (positive - negative) / total

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
            # Phase 5: structured world state and last prediction error.
            "world_entities": list(self.world.entities.keys()),
            "last_prediction_error": self.state.last_prediction_error,
            # Phase 6: goal-driven behavior snapshot.
            "active_goal": (
                {"goal_id": g.goal_id, "description": g.description, "progress": g.progress, "status": g.status.value}
                if (g := self.goal_manager.active_goal())
                else None
            ),
            "goal_stats": self.goal_manager.stats(),
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
