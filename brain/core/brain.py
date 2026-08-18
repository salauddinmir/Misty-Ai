"""
Main Brain Class.

The central orchestrator that initializes all subsystems and
processes input through the cognitive cycle. This is the primary
entry point for the cognitive system.
"""

import re
import time as time_module
from typing import Any, Dict, List

import numpy as np

from brain.actuators import ActuatorBridge
from brain.cognition import (
    AppraisalEngine,
    AppraisalEvent,
    CognitiveEvent,
    Evidence,
    GlobalWorkspace,
    HypothesisRecord,
    LanguageGrounder,
    PerceptionPipeline,
    SelfModel,
    ThoughtTraceSummary,
)
from brain.core.cycle import CognitiveCycle, CognitivePhase, CycleResult
from brain.core.state import BrainState
from brain.dialogue.context import DialogueContext
from brain.emotion.state import EmotionalState
from brain.goals.manager import GoalManager
from brain.graph.activation import SpreadingActivation
from brain.graph.concepts import ConceptGraph
from brain.graph.hebbian import HebbianLearner
from brain.knowledge.commonsense import register_commonsense_layer
from brain.knowledge.inference import InferenceSynthesizer
from brain.learning.consolidation import MemoryConsolidator
from brain.learning.curiosity import CuriosityExplorer
from brain.learning.induction import EvidenceGatedInducer
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


def _current_token_set(text: str | None) -> set:
    """Normalize the tokens of a raw input string for topic exclusion."""
    if not text:
        return set()
    norm = re.sub(r"[^\w\u0980-\u09ff]", " ", text).strip()
    return {w for w in norm.split() if w and len(w) > 2}


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
        self.inducer = EvidenceGatedInducer()
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

        # Global cognitive workspace: a bounded, inspectable blackboard shared
        # by perception, memory, reasoning, appraisal, and language phases.
        self.workspace = GlobalWorkspace()
        self.language_grounder = LanguageGrounder()
        self.perception = PerceptionPipeline()
        self.appraisal_engine = AppraisalEngine()
        self.self_model = SelfModel()
        self.last_autonomous_tick: Dict[str, Any] | None = None
        # Phase 14: hard evidence budget per autonomous reflection tick.
        self.max_evidence_per_tick: int = 4
        # Phase 18: knowledge-inference synthesis — derive answers from
        # stored concepts and rules instead of echoing memorized phrases.
        self.inference_synthesizer = InferenceSynthesizer()

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

        # Phase 18: load the bilingual commonsense world-knowledge layer
        # AFTER trained identity facts so user-taught facts take priority.
        register_commonsense_layer(self)

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
        self.workspace.reset_cycle(goal="answer" if source == "text" else "monitor")
        self.workspace.broadcast_event(
            CognitiveEvent(
                content=text_input,
                source=source,
                event_type="sensor_reading" if source == "sensor" else "utterance",
                metadata={"sensor_id": sensor_event.sensor_id} if sensor_event else {},
            )
        )

        # Record the user turn in the dialogue context so later turns
        # can resolve pronouns ("সে", "it", "its") back to this turn.
        self.dialogue_context.add_turn(text_input, role="user")

        # Start cognitive cycle
        self.cycle.start_cycle()

        def run_phase(phase_fn, *args, **kwargs):
            phase_started = time_module.perf_counter()
            result = phase_fn(*args, **kwargs)
            elapsed_ms = round((time_module.perf_counter() - phase_started) * 1000, 3)
            self.cycle.phase_timings_ms[result.phase.value] = elapsed_ms
            self.cycle.advance(result)
            return result

        # Phase 1: OBSERVE
        run_phase(self._phase_observe, text_input)

        # Phase 2: INTERPRET
        interpret_result = run_phase(self._phase_interpret, text_input, source=source)
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
        recall_result = run_phase(self._phase_recall, interpret_result.data.get("parse_result"))

        # Phase 4: ASSOCIATE
        associate_result = run_phase(self._phase_associate, interpret_result.data.get("parse_result"))

        # Phase 5: REASON
        run_phase(self._phase_reason, interpret_result.data.get("parse_result"))

        # Phase 6: PLAN
        run_phase(self._phase_plan, interpret_result.data.get("parse_result"))

        # Phase 7: ACT
        act_result = run_phase(
            self._phase_act,
            interpret_result.data.get("parse_result"),
            recall_result.data,
            associate_result.data,
        )

        # Phase 8: EVALUATE
        evaluate_result = run_phase(self._phase_evaluate, act_result)

        # Phase 9: LEARN
        run_phase(self._phase_learn, interpret_result.data.get("parse_result"), act_result)

        # Phase 10: CONSOLIDATE
        run_phase(self._phase_consolidate)

        # Update state
        processing_time = time_module.time() - start_time
        response = act_result.data.get("response", "")
        self.state.last_output = response
        workspace_summary = self.workspace.summary()
        thought_trace = ThoughtTraceSummary(
            focus=self.workspace.focus,
            intent=interpret_result.data.get("intent", "unknown"),
            evidence_count=len(self.workspace.evidence),
            hypothesis_count=len(self.workspace.hypotheses),
            confidence=float(act_result.data.get("confidence", 0.5)),
            uncertainty=max(0.0, 1.0 - float(act_result.data.get("confidence", 0.5))),
            decision="respond" if response else "request_clarification",
        )
        # Keep the interpreted intent accessible to API consumers.
        intent_value = interpret_result.data.get("intent", "unknown") if interpret_result is not None else "unknown"
        grounded_utterance = self.language_grounder.ground(
            response,
            raw_input=text_input,
            intent=intent_value,
            confidence=float(act_result.data.get("confidence", 0.5)),
            evidence_count=len(self.workspace.evidence),
            hypothesis_count=len(self.workspace.hypotheses),
            strategy="deterministic_action_with_workspace_context",
        )

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
        self.self_model.update_uncertainty(self.state.last_prediction_error)
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
            "cognitive_workspace": workspace_summary,
            "thought_trace": thought_trace.to_dict(),
            "self_model": self.self_model.summary(),
            "grounding": grounded_utterance.to_dict(),
            "phase_timings_ms": dict(self.cycle.phase_timings_ms),
        }

    def _phase_observe(self, text_input: str) -> CycleResult:
        """OBSERVE phase: Register incoming input."""
        self.state.current_phase = "observe"
        percept = self.perception.perceive(text_input)
        self.working_memory.store("current_input", percept.event.content)
        self.working_memory.store("current_percept", percept.to_dict())
        self.workspace.broadcast_event(percept.event)

        is_question = percept.question_demand >= 0.7
        self.emotion.update_from_input(is_question=is_question, is_new_info=True)
        appraisal = AppraisalEvent(
            trigger="question" if is_question else "new_input",
            appraisal="epistemic_demand" if is_question else "novelty_check",
            intensity=max(0.4, percept.attention_weight),
            affected_dimensions={
                "curiosity": 0.08 if is_question else 0.04,
                "uncertainty": 0.06 if is_question else 0.02,
                "attention": percept.attention_weight * 0.05,
            },
        )
        self.workspace.appraise(appraisal)
        drives = self.appraisal_engine.appraise(percept, self.emotion)
        self.working_memory.store("drive_priorities", [drive.to_dict() for drive in drives])

        return CycleResult(
            phase=CognitivePhase.OBSERVE,
            data={
                "input": percept.event.content,
                "is_question": is_question,
                "percept": percept.to_dict(),
                "drive_priorities": [drive.to_dict() for drive in drives],
            },
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
        target = parse_result.query.get("target", "")
        if parse_result.intent in (IntentType.QUERY_WHO, IntentType.QUERY_WHAT):
            if not target or target in self._PRONOUN_TOKENS:
                # Phase 23: use a previous-turn topic, not a token from the
                # current input (current-turn salient entities would just
                # echo the bare word like "কারণ" back at the user).
                prior_topic = self._prior_topic(
                    exclude=_current_token_set(parse_result.raw_text)
                )
                if prior_topic:
                    parse_result.query["target"] = prior_topic
                    parse_result.entities["coreference_target"] = prior_topic
        # Phase 23: bare follow-up questions ("সেটা কী?", "কারণ কী?", "আর বলো")
        # inherit the last conversation topic so the thread stays alive.
        self._resolve_bare_followup(parse_result)
        if not parse_result.entities and parse_result.intent in (
            IntentType.STATEMENT,
            IntentType.UNKNOWN,
            IntentType.CONTINUATION,
            IntentType.CORRECTION,
            IntentType.TEACH,
        ):
            resolved = resolve_entities(
                parse_result.raw_text, self.dialogue_context.get_salient_entities()
            )
            if resolved:
                parse_result.entities["resolved_entities"] = resolved

    # Phase 23: bare follow-up resolution constants.
    _BARE_FOLLOWUP_PATTERN = re.compile(
        r"(সেট|এট|ওট|এগুল|ওগুল)\b|^(কারণ|কারণট|কী কারণ|কেনো|তারপর|"
        r"তারপরে|আর|আরব|আরে|আরে বল|আর বল|আরে বলে|আরব বল|আরে বলে|"
        r"আরে জনাও|জনাও|বলে দাও)\b"
    )
    _BARE_FOLLOWUP_PATTERNS = (
        re.compile(r"সেট|এট|ওট|সেটা|এটা|ওটা|এটার|সেটার|এগুল|ওগুল|এগুলা|ওগুলা"),
        re.compile(r"^কারণ|কারণ ক|কী কারণ|কারণটা"),
        re.compile(r"^আর|আর বল|আরো বল|আরব বল|বলে দাও|জানাও|আর জানাও"),
    )
    # Phase 23: how many recent turns to look back at for context phrases.
    _CONTEXT_WINDOW: int = 4
    # Phase 23: discourse tokens that must never be treated as a topic.
    _DISCOURSE_TOKENS = frozenset(
        {
            "আর", "আরো", "আরব", "কারণ", "কারণে", "কারণটা", "কারণটি",
            "এখন", "তখন", "পরে", "আগে", "তাই", "এটাই", "বেশ", "আচ্ছা",
            # Explicit-teaching trigger words must never be picked as the
            # conversation topic ("মনে রাখো: X হলো Y" → topic = X). These
            # also appear in DialogueContext's extraction ban list.
            "মনে", "রাখো", "রাখুন", "রাখা", "জানি", "জানাও", "শেখো",
            "শেখাও", "শেখে", "বলো", "বলুন", "বলে", "বলা",
        }
    )

    def _resolve_bare_followup(self, parse_result: ParseResult) -> None:
        """Phase 23: inherit the last conversation topic for bare follow-ups.

        Inputs like "সেটা কী?", "কারণ কী?", "আর বলো" contain no explicit
        entity, so the most recent PRIOR-TURN topic from the dialogue
        context is copied into the query target so ACT handlers keep the
        thread. Tokens from the current input are excluded so a bare word
        like "কারণ" never echoes itself back at the user.
        """
        if parse_result.intent not in (
            IntentType.QUERY_WHAT,
            IntentType.QUERY_WHO,
            IntentType.CONTINUATION,
            IntentType.UNKNOWN,
            IntentType.CONVERSATION,
        ):
            return
        topic = self._prior_topic(exclude=_current_token_set(parse_result.raw_text))
        if topic is None:
            return
        for pattern in self._BARE_FOLLOWUP_PATTERNS:
            if pattern.search(parse_result.raw_text or ""):
                parse_result.query["target"] = topic
                parse_result.entities["bare_followup"] = True
                parse_result.entities["coreference_target"] = topic
                return

    def _prior_topic(self, exclude: set | None = None) -> str | None:
        """Return the most recent conversation topic from PRIOR turns only.

        Tokens appearing in the current input are excluded so follow-ups
        that name a bare word ("কারণ কী?", "আর বলো") inherit the previous
        topic instead of echoing themselves. Inflected Bengali forms are
        normalized to their base (genitive suffixes stripped).
        """
        exclude = exclude or set()
        prior_texts = self.dialogue_context.get_history_texts()
        # get_history_texts without include_last_n returns user turns; drop
        # the very last one since it is the current input being processed.
        prior_texts = prior_texts[:-1] if prior_texts else []
        for turn in reversed(prior_texts):
            norm = re.sub(r"[^\w\u0980-\u09ff]", " ", turn or "").strip()
            words = [w for w in norm.split() if w and len(w) > 2]
            for word in words:
                base = self._normalize_bengali_word(word)
                if base in self._DISCOURSE_TOKENS or base in exclude:
                    continue
                if base in self._PRONOUN_TOKENS:
                    continue
                return base
        return None

    @staticmethod
    def _normalize_bengali_word(word: str) -> str:
        """Strip common Bengali inflection suffixes to get a base topic."""
        normalized = word
        for suffix in ("েরটা", "েরটি", "ের", "র", "টা", "টি", "গুলো", "গুলি"):
            if normalized != suffix and normalized.endswith(suffix):
                stripped = normalized[: -len(suffix)]
                if stripped:
                    normalized = stripped
                    break
        return normalized

    def _act_conversation(self, parse_result: ParseResult) -> tuple:
        """Deterministic friendly reply for casual/social turns detected by
        the parser (কি খবর, কেমন আছো, তুমি কি ভাবছো, that's good ...).

        Replies are composed from the brain's current self-model so the
        answer reflects genuine internal state rather than a scripted echo.
        """
        text = parse_result.raw_text.lower()
        self_model_text = self._self_model_phrase()

        # Bengali "ভাবছো/করছো" queries expose the current thinking state.
        if re.search(r"ভাবছ|কি করছ", text):
            response = f"আমি এখন স্ব-পর্যবেক্ষণ করছি। {self_model_text} আপনার কি করতে চান?"
            return response, 0.8
        if re.search(r"কি খবর|কেমন আছ", text):
            response = f"আমি ভালো আছি, ধন্যবাদ! {self_model_text} আপনার কি খবর?"
            return response, 0.85
        if re.search(r"ভালো|বেশ|ঠিক", text):
            response = f"ধন্যবাদ! আপনার কথাটি আমি সংগ্রহ করলাম। {self_model_text}"
            return response, 0.75

        # Bengali clarification follow-ups: "বুঝলাম না", "কি ব্যাপার", "কেন"
        # Phase 23: these are topic-anchored to the last thing the brain said.
        if re.search(r"বুঝলাম ন|বুঝতে পারছি ন|বুঝছি ন", text):
            # Phase 23: anchor the clarification to the last brain turn.
            anchor = self._context_topic_phrase()
            if anchor:
                response = (
                    f"আপনি ঠিক আছেন! {anchor} আমি এটি একটু সহজ করে বলছি — "
                    "দেখুন কোনো অংশ আবার বুঝিয়ে বলতে পারি?"
                )
            else:
                response = (
                    "আপনি ঠিক আছেন! আমি একটু সহজ করে বলছি: আমি একটি ডিজিটাল "
                    "ব্রেন — আমি আপনার আগের কথার উপর ভিত্তি করে কাছে, চিন্তা করি এব "
                    "আমার সংরক্ষিত জ্ঞান থেকে উত্তর তৈরি করি। কোনো অংশটি আবার "
                    "বুঝিয়ে বলি?"
                )
            return response, 0.75
        if re.search(r"কি ব্যাপার|কী ব্যাপার", text):
            response = (
                "কোনো ব্যাপার নয়! আমি ভালো আছি এবং আপনার কথা শুনছি। "
                f"{self_model_text} বলুন, কী নিয়ে কথা হবে?"
            )
            return response, 0.75
        if re.search(r"\bকেন\b", text):
            response = (
                "একটি কারণ থাকতে পারে: আমি আমার সংরক্ষিত নিয়ম এবং কনসেপ্ট "
                "থেকে সবচেয়ে যুক্তিসঙ্গত উত্তরটি বাছাই করি। আমি যদি ভুল উত্তর "
                "দিয়ে থাকি, আমাকে ঠিক করে দিন — আমি শিখে যাব।"
            )
            return response, 0.6
        # English equivalents.
        if re.search(r"how are you|how's it going|how are things", text):
            response = f"I am doing well, thank you! {self_model_text} How about you?"
            return response, 0.85
        if re.search(r"what are you thinking", text):
            response = f"I am observing my own state right now. {self_model_text} What would you like to discuss?"
            return response, 0.8
        # English clarification follow-ups: "I don't understand",
        # "what's up", "why"
        if re.search(r"i don't understand|i do not understand|i don't get it", text):
            response = (
                "No problem! In short: I am a digital brain. I think by "
                "combining the concepts and rules I have learned, and I give "
                "you an answer derived from that knowledge. Would you like "
                "me to explain any part again?"
            )
            return response, 0.75
        if re.search(r"what's up|what is up|what happened", text):
            response = (
                "Nothing special — just processing and learning! "
                f"{self_model_text} What shall we talk about?"
            )
            return response, 0.75
        if re.search(r"\bwhy\b", text):
            response = (
                "There is a reason behind it: I pick the most consistent "
                "answer derivable from my stored concepts and rules. If I got "
                "something wrong, correct me — I will learn from it."
            )
            return response, 0.6
        if re.search(r"that's good|that is good|nice|sounds good|cool", text):
            response = f"Thank you! I noted that. {self_model_text}"
            return response, 0.75

        # Generic friendly acknowledgment for any other casual turn.
        response = f"আমি আপনার কথাটি শুনলাম। {self_model_text}"
        return response, 0.6

    # Phase 23: compose a short phrase that anchors the current reply to
    # the recent conversation topic so follow-ups feel coherent.
    def _context_topic_phrase(self) -> str | None:
        """Return a Bengali phrase naming the most recent conversation topic,
        or None when there is no recent context to reference.
        """
        recent = self.dialogue_context.get_history_texts(include_last_n=self._CONTEXT_WINDOW)
        for turn in reversed(recent):
            norm = re.sub(r"[^\w\u0980-\u09ff]", " ", turn or "").strip()
            words = [w for w in norm.split() if w and len(w) > 2]
            for candidate in words:
                if candidate.lower() in self._PRONOUN_TOKENS:
                    continue
                # Skip discourse and stop-like tokens that are never topics.
                if candidate.lower() in self._DISCOURSE_TOKENS or candidate.lower() in {
                    "কি", "কী", "কিছু", "আমি", "তুমি", "আপনি",
                    "এটা", "সেটা", "ওটা", "আছ", "আছো", "করছ",
                }:
                    continue
                salient = self.dialogue_context.get_salient_entities()
                salient = [e for e in salient if e not in self._DISCOURSE_TOKENS]
                if salient and candidate.lower() == salient[0].lower():
                    return f"আপনি আগে {candidate} নিয়ে কথা বলছিলেন — "
                if salient:
                    continue
            salient = [
                e
                for e in self.dialogue_context.get_salient_entities()
                if e not in self._DISCOURSE_TOKENS
            ]
            if salient:
                return f"আপনি আগে {salient[0]} নিয়ে কথা বলছিলেন — "
        return None

    def _self_model_phrase(self) -> str:
        """Compact, user-readable snapshot of the current self-model state."""
        summary = self.self_model.summary()
        uncertainty = summary.get("uncertainty", 0.0) if isinstance(summary, dict) else 0.0
        if uncertainty > 0.7:
            return "আমার নিজের অনিশ্চয়তা এখন উচ্চ — আমি নতুন কিছু শিখছি।"
        if uncertainty > 0.4:
            return "আমি বর্তমান নিজের চিন্তার ধারাটি যাচাই করছি।"
        return "আমি নতুন জ্ঞান শিখছি এব নিজের চিন্তাগুলো পর্যবেক্ষণ করছি।"

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
            "সেট",
            "সেটা",
            "এট",
            "এটা",
            "ওট",
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

        if parse_result:
            intent_name = parse_result.intent.value
            hypothesis = HypothesisRecord(
                statement=f"Interpret input as {intent_name}",
                goal="answer" if intent_name != IntentType.STATEMENT.value else "understand",
                premises=[parse_result.raw_text],
                confidence=parse_result.confidence,
                uncertainty=max(0.0, 1.0 - parse_result.confidence),
            )
            hypothesis.add_evidence(
                Evidence(
                    source="nlu",
                    content={"intent": intent_name, "entities": parse_result.entities},
                    confidence=parse_result.confidence,
                )
            )
            hypothesis.mark_tested(parse_result.confidence > 0.3)
            self.workspace.propose(hypothesis)

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
            "conversation": 0.45,
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
        elif parse_result.intent == IntentType.CONVERSATION:
            plan = "converse_friendly"
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

        elif parse_result.intent == IntentType.CAPABILITY_QUERY:
            response, confidence = self._act_capability(parse_result)

        elif parse_result.intent == IntentType.RECOGNITION_QUERY:
            response, confidence = self._act_recognition(parse_result)
        elif parse_result.intent == IntentType.CONVERSATION:
            response, confidence = self._act_conversation(parse_result)
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

    def _act_capability(self, parse_result: ParseResult) -> tuple:
        """Explain currently implemented capabilities without overstating them."""
        is_bengali = any("\u0980" <= char <= "\u09ff" for char in parse_result.raw_text)
        if is_bengali:
            return (
                "হ্যাঁ, আমি এখন deterministic Mathematics ও Physics engine-এর মাধ্যমে "
                "অঙ্কের হিসাব, algebra, geometry, statistics এবং mechanics/kinematics-এর "
                "নির্দিষ্ট সূত্র সমাধান করতে পারি। বাংলা ও ইংরেজি বাক্য parse করে ধারণা, "
                "সম্পর্ক, স্মৃতি ও learning event-এ রাখি। তবে আমি সব প্রশ্নের উত্তর জানি না; "
                'নতুন তথ্য আপনি "মনে রাখো: ..." বা "X হলো Y" আকারে শেখালে তা বর্তমান '
                "knowledge graph-এ যুক্ত হয়। আমার অনুভূতিগুলো এখন computational state—"
                "যেমন curiosity, confidence ও uncertainty—মানবসদৃশ চেতনা নয়।"
            ), 0.9
        return (
            "Yes. I currently use deterministic Mathematics and Physics engines for "
            "supported arithmetic, algebra, geometry, statistics, mechanics, and kinematics. "
            "I also parse Bengali and English, retain concepts and relations, and learn "
            "explicit facts. My emotion values are computational state signals such as "
            "curiosity, confidence, and uncertainty—not human consciousness."
        ), 0.9

    def _act_recognition(self, parse_result: ParseResult) -> tuple:
        """Answer whether the dialogue context contains a known user identity."""
        is_bengali = any("\u0980" <= char <= "\u09ff" for char in parse_result.raw_text)
        if self.user_name:
            if is_bengali:
                return (
                    f"হ্যাঁ, এই conversation-এ আপনি আগে আপনার নাম {self.user_name} বলেছেন; "
                    f"তাই আমি আপনাকে {self.user_name} হিসেবে মনে রেখেছি।",
                    0.9,
                )
            return (
                f"Yes. In this conversation you told me your name is {self.user_name}, "
                f"so I remember you as {self.user_name}.",
                0.9,
            )
        if is_bengali:
            return (
                "আমি এই conversation-এর আগের বার্তা মনে রাখি, কিন্তু আপনার নাম এখনো শেখানো হয়নি। "
                '"আমার নাম X" বললে আমি এই session-এ আপনাকে X হিসেবে মনে রাখব।',
                0.7,
            )
        return (
            "I can use the current conversation context, but you have not taught me your name yet. "
            'Say "My name is X" and I will remember you during this session.',
            0.7,
        )

    def _act_unknown(self, parse_result: ParseResult) -> tuple:
        """Handle inputs the brain cannot yet understand.

        Gives a contextual fallback response that acknowledges the input,
        signals humility (low confidence), and invites the user to teach
        the brain using supported phrasings. This keeps the conversation
        flowing instead of dead-ending on unknown input.
        """
        raw = parse_result.raw_text or "your message"

        # Phase 18: before admitting confusion, try to SYNTHESIZE an answer
        # from the commonsense layer and stored knowledge so MISTY thinks
        # rather than echoing a memorized phrase.
        synthesis = self.inference_synthesizer.synthesize(raw, self)
        if synthesis is not None:
            self.emotion.update_from_outcome(success=True)
            self.state.add_thought("inference_synthesis", synthesis.steps)
            return synthesis.answer, synthesis.confidence
        is_bengali = any("\u0980" <= char <= "\u09ff" for char in raw)
        if is_bengali:
            return (
                "আমি আপনার কথাটি বুঝতে চেষ্টা করেছি, কিন্তু এই বাক্যের intent এখনো "
                'নির্ভুলভাবে parse করতে পারিনি। আপনি চাইলে "মনে রাখো: ...", "X হলো Y", '
                '"আমার নাম X", অথবা নির্দিষ্ট math/physics format ব্যবহার করে শেখাতে পারেন। '
                "আমি এই অজানা input-টি learning opportunity হিসেবে working memory-তে রেখেছি।"
            ), 0.35
        response = (
            "I heard you, but I could not resolve the intent yet. You can teach me with "
            '"remember that ...", "X is Y", or ask a supported mathematics or physics question. '
            "I have retained this unknown input as a learning opportunity."
        )
        return response, 0.35

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

        # Phase 18: derive an answer from commonsense / stored knowledge
        # before falling back to "আমি এখনো X সম্পর্কে জানি না".
        synthesis = self.inference_synthesizer.synthesize(
            parse_result.raw_text or target_name, self
        )
        if synthesis is not None:
            self.state.add_thought("inference_synthesis", synthesis.steps)
            return (
                f"{target_name} সম্পর্কে আমি এইতুক জানি: {synthesis.answer}",
                synthesis.confidence,
            )

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

        # Phase 18: try knowledge-inference synthesis on the raw statement
        # before falling back to the generic echo.
        synthesis = self.inference_synthesizer.synthesize(
            parse_result.raw_text or "", self
        )
        if synthesis is not None:
            self.state.add_thought("inference_synthesis", synthesis.steps)
            return (
                synthesis.answer,
                synthesis.confidence,
            )

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
        # When the parser hands over only the taught sentence, extract the
        # is_a fact from it here so "মনে রাখো: X হলো Y" actually teaches.
        taught = parse_result.entities.get("taught", "") or raw
        if not facts and taught:
            for pattern in self.nlu._bn_is_a_pattern.finditer(taught):
                subject, obj = pattern.group(1).strip(), NLUParser._trim_bn_clause(pattern.group(2).strip())
                if subject and obj and subject != obj:
                    facts.append({"subject": subject, "obj": obj})
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
        # Phase 23: prefer the prior-turn topic over current-turn salient
        # tokens (which for "আর বলো" would wrongly pick "আর" itself).
        exclude = _current_token_set(parse_result.raw_text)
        topic = self._prior_topic(exclude=exclude)
        salient = self.dialogue_context.get_salient_entities()
        salient = [e for e in salient if e not in self._DISCOURSE_TOKENS]
        if topic is None and salient:
            topic = salient[0]
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

        # Phase 23: try knowledge-inference synthesis on the topic before
        # admitting ignorance, so follow-ups can still extract reasoning.
        synthesis = self.inference_synthesizer.synthesize(
            f"{topic} কী?", self
        )
        if synthesis is not None:
            self.state.add_thought("inference_synthesis", synthesis.steps)
            detail = (
                synthesis.answer[3:].strip() if synthesis.answer.startswith("আমি ")
                else synthesis.answer
            )
            return (
                f"{topic} সম্পর্কে আমি এতটুকু জানি: {detail}",
                synthesis.confidence,
            )
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
        induced_candidates = []
        if parse_result and parse_result.relations:
            for relation in parse_result.relations:
                subject = relation.get("subject") or parse_result.entities.get("subject")
                predicate = relation.get("predicate") or relation.get("relation")
                obj = relation.get("object") or relation.get("obj")
                if subject and predicate and obj:
                    self.inducer.observe(
                        subject,
                        predicate,
                        obj,
                        confidence=confidence,
                        source=state_key,
                    )
            induced_candidates = self.inducer.promote_ready(self.semantic_memory)
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
            data={
                "reward": reward,
                "goal_update": goal_update,
                "induced_candidates": induced_candidates,
                "pending_learning": len(self.inducer.pending()),
            },
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
                "pending_learning": len(self.inducer.pending()),
                "promoted_learning": self.inducer.promoted_count,
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

    async def autonomous_reflection_tick(self) -> None:
        """Run one bounded internal reflection step without user I/O.

        The tick is intentionally deterministic and read-only with respect to
        durable knowledge. It selects a small internal question, gathers
        relevant evidence from existing semantic memory, records provenance,
        and stores a structured audit snapshot for the next user-facing cycle.
        No unsupported fact is promoted automatically.
        """
        started_at = time_module.monotonic()
        self._tick_index = getattr(self, "_tick_index", 0) + 1
        active_goal = self.goal_manager.active_goal()
        goal_text = active_goal.description if active_goal else "review unresolved knowledge"
        uncertainty = self.self_model.uncertainty
        focus = self.workspace.focus or "recent cognitive state"
        question = f"Is the current model sufficient for: {goal_text}?"
        # Phase 14: hard evidence budget per autonomous tick.
        max_evidence_per_tick = max(1, int(getattr(self, "max_evidence_per_tick", 4)))
        self.workspace.reset_cycle(goal=goal_text)
        event = CognitiveEvent(
            content=f"internal reflection: {focus[:120]}",
            source="autonomy",
            event_type="internal_review",
            salience=max(0.2, uncertainty),
            reliability=1.0,
            metadata={
                "cycle": self.cycle.cycle_count,
                "goal": goal_text,
                "question": question,
            },
        )
        self.workspace.broadcast_event(event)

        # Bounded internal retrieval: score at most the semantic-memory facts
        # using token overlap with the selected question/focus. This creates
        # genuine evidence gathering without network I/O or hidden generation.
        query_tokens = {
            token.casefold() for token in re.findall(r"[\w\u0980-\u09ff]+", f"{goal_text} {focus}") if len(token) > 2
        }
        scored_facts: list[tuple[int, Any]] = []
        for fact in self.semantic_memory.facts.values():
            haystack = f"{fact.subject} {fact.predicate} {fact.obj}".casefold()
            overlap = sum(1 for token in query_tokens if token in haystack)
            scored_facts.append((overlap, fact))
        scored_facts.sort(key=lambda item: (item[0], item[1].confidence), reverse=True)
        selected_facts = [fact for overlap, fact in scored_facts[:max_evidence_per_tick] if overlap > 0]

        evidence_records: list[Evidence] = []
        fact_groups: dict[tuple[str, str], list[Any]] = {}
        for fact in selected_facts:
            fact_groups.setdefault((fact.subject, fact.predicate), []).append(fact)
        for fact in selected_facts:
            peers = fact_groups[(fact.subject, fact.predicate)]
            has_conflict = any(peer.obj != fact.obj for peer in peers)
            strongest = max(peer.confidence for peer in peers)
            polarity = "contradict" if has_conflict and fact.confidence < strongest else "support"
            evidence = Evidence(
                source=f"semantic_memory:{fact.source}",
                content={
                    "subject": fact.subject,
                    "predicate": fact.predicate,
                    "obj": fact.obj,
                },
                confidence=max(0.0, min(1.0, float(fact.confidence))),
                polarity=polarity,
            )
            evidence_records.append(evidence)
        if evidence_records:
            self.workspace.add_evidence_many(evidence_records)

        hypothesis = HypothesisRecord(
            statement=question,
            goal="self_review",
            premises=[f"current uncertainty={uncertainty:.3f}"],
            predictions=[
                "relevant semantic evidence should reduce uncertainty"
                if evidence_records
                else "no relevant internal evidence is currently available"
            ],
            confidence=max(0.1, 1.0 - uncertainty),
            uncertainty=uncertainty,
        )
        for evidence in evidence_records:
            hypothesis.add_evidence(evidence)
        has_contradiction = any(item.polarity == "contradict" for item in evidence_records)
        if evidence_records:
            hypothesis.mark_tested(not has_contradiction)
        self.workspace.propose(hypothesis)
        self.workspace.appraise(
            AppraisalEvent(
                trigger="internal_reflection",
                appraisal="evidence_gathered" if evidence_records else "no_evidence",
                intensity=max(0.1, uncertainty),
                affected_dimensions={"curiosity": 0.03, "attention": 0.02},
            )
        )
        elapsed_ms = round((time_module.monotonic() - started_at) * 1000.0, 2)
        self.last_autonomous_tick = {
            "goal": goal_text,
            "question": question,
            "tick_index": self._tick_index,
            "evidence_budget": max_evidence_per_tick,
            "evidence_count": len(evidence_records),
            "evidence_ids": [item.evidence_id for item in evidence_records],
            "outcome": (
                "hypothesis_rejected"
                if has_contradiction
                else "hypothesis_supported"
                if evidence_records
                else "no_evidence"
            ),
            "hypothesis_status": hypothesis.status,
            "uncertainty": hypothesis.uncertainty,
            "workspace": self.workspace.summary(),
            "elapsed_ms": elapsed_ms,
            "quarantined_candidates": list(getattr(self.consolidator, "rejected_candidates", [])),
        }
        self.working_memory.store("last_autonomous_reflection", self.last_autonomous_tick)

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
            # Phase 12+: active autonomous evidence-gathering snapshot.
            "last_autonomous_tick": self.last_autonomous_tick,
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
