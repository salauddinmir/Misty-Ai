"""
Main Brain Class.

The central orchestrator that initializes all subsystems and
processes input through the cognitive cycle. This is the primary
entry point for the cognitive system.
"""

import copy
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
from brain.dialogue.driver import ConversationDriver
from brain.emotion import tone as tone_module
from brain.emotion.state import EmotionalState
from brain.emotion.tone import ToneMapper
from brain.goals.manager import GoalManager
from brain.graph.activation import SpreadingActivation
from brain.graph.concepts import ConceptGraph
from brain.graph.hebbian import HebbianLearner
from brain.knowledge.commonsense import (
    register_commonsense_layer,
    register_conversation_corpus,
)
from brain.knowledge.inference import InferenceSynthesizer
from brain.knowledge.personality import ResponseVariator
from brain.knowledge.training_culture import register_culture_curriculum
from brain.knowledge.training_literature import register_literature_curriculum
from brain.knowledge.training_mathematics import register_mathematics_curriculum
from brain.knowledge.training_physics import register_physics_curriculum
from brain.knowledge.web_learning import WebSearchLearner
from brain.learning.consolidation import MemoryConsolidator
from brain.learning.curiosity import CuriosityExplorer
from brain.learning.induction import EvidenceGatedInducer
from brain.learning.post_learning_loop import PostLearningAssessor, attach_to_learner
from brain.learning.reinforcement import ReinforcementLearner
from brain.learning.reward import RewardSignal
from brain.learning.self_assessment import GapAssessor
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
        # Assessment clones must not learn from benchmark prompts or trigger
        # process-wide persistence hooks installed by the API runtime.
        self._assessment_mode: bool = False

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
        # Phase 33: autonomous self-assessment — the brain evaluates its own
        # knowledge against benchmark cases, produces an inspectable gap list,
        # and exposes it via the state snapshot (``knowledge_gaps``).
        self.gap_assessor = GapAssessor(self)
        # Phase 36: deterministic web-learning ingestion bound to this brain
        # so learning batches (and the /api/training/web_learn route) share
        # the same semantic memory, quarantine, and safety gate.
        self.web_learner = WebSearchLearner(self)
        # Phase 37 — post-learning self-assessment loop.
        self.post_learning_assessor = PostLearningAssessor(self, gap_assessor=self.gap_assessor)
        attach_to_learner(self.web_learner, self.post_learning_assessor)
        self._learning_quarantine: List[Dict[str, Any]] = []

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

        # Phase 24: personality voice and response variation — reply
        # templates are drawn from a per-intent bilingual pool so two
        # consecutive identical inputs cannot produce identical replies.
        self.variator = ResponseVariator()

        # Phase 25: conversation driver — keeps the exchange alive with
        # empathy, interest expansion, and off-track steering questions.
        self.conversation_driver = ConversationDriver()

        # Phase 26: emotion-driven tone mapping — the internal emotional
        # state now changes HOW the brain replies (register, length hint,
        # safe humor, calm responses to anger).
        self.tone_mapper = ToneMapper()

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

    def enable_assessment_mode(self) -> None:
        """Disable learning and persistence side effects for an evaluator clone.

        API startup currently installs an instance-level procedural store hook
        and a process-wide ``Procedure.reinforce`` hook.  Evaluation clones may
        inherit the former through ``deepcopy`` and always observe the latter,
        so assessment mode removes the instance hook and cognitive phases check
        this flag before invoking any reinforcement or long-term learning.
        """
        self._assessment_mode = True
        self.consolidator.persistence_sink = None
        # A live API brain may have an instance monkey-patch that closes over
        # its database.  Removing a copied override restores the normal class
        # method on the isolated evaluator.
        self.procedural_memory.__dict__.pop("store", None)

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
        register_conversation_corpus(self)
        # Phase 29: load the full bilingual mathematics curriculum —
        # algebra, geometry, trigonometry, percentages/series and
        # number theory — into the registry, concepts and facts.
        register_mathematics_curriculum(self)
        # Phase 30: load the full bilingual physics curriculum — mechanics,
        # energy, gravitation, electricity, waves and thermal concepts.
        register_physics_curriculum(self)
        # Phase 31: load the bilingual Bengali literature curriculum —
        # Tagore, Nazrul, Jibanananda Das and the literary renaissance.
        register_literature_curriculum(self)
        # Phase 32: load the bilingual social-cultural curriculum —
        # Bangladesh and India state, festivals, geography and world basics.
        register_culture_curriculum(self)

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
        reason_result = run_phase(
            self._phase_reason,
            interpret_result.data.get("parse_result"),
            recall_result.data,
            associate_result.data,
        )

        # Phase 6: PLAN
        plan_result = run_phase(
            self._phase_plan,
            interpret_result.data.get("parse_result"),
            reason_result.data,
        )

        # Phase 7: ACT
        act_result = run_phase(
            self._phase_act,
            interpret_result.data.get("parse_result"),
            recall_result.data,
            associate_result.data,
            reason_result.data,
            plan_result.data,
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

        # Phase 25: let the conversation driver decide whether this reply
        # should end with a follow-up of its own. The driver respects
        # cooldown (never two driver questions back-to-back) and closure
        # (never a question after "বাই"/"goodbye").
        intent_value = interpret_result.data.get("intent", "unknown") if interpret_result is not None else "unknown"
        driver_plan = self._driver_plan(text_input, response, intent_value, act_result.data.get("confidence", 0.5))
        # Phase 28: the rest of this post-processing (tone, grounding,
        # turn-recording) still runs on closure turns, but the farewell
        # line must never be decorated with a tone opener or a joke.
        _closure_turn = driver_plan.kind == "closure"
        if driver_plan.kind == "closure":
            # Phase 27/28: farewells replace the reply for closure turns
            # (parser-flagged "বাই" / "goodbye" or driver-detected goodbye)
            # so the brain never responds to a farewell with a question
            # about the user's health.
            if driver_plan.question:
                response = driver_plan.question
        elif driver_plan.needs_followup and driver_plan.question and response:
            response = f"{response} {driver_plan.question}"

        # Phase 26: emotion-driven tone — apply the style opener and safe
        # joke from the current emotional state and the user's affect.
        # Skipped on closure turns so 'বাই।' / 'goodbye' produce a clean
        # farewell line.
        if _closure_turn:
            tone_plan = None
        else:
            tone_plan = self.tone_mapper.plan_tone(self.emotion, text_input, response)
        if tone_plan is not None:
            if tone_plan.joke:
                response = f"{response} {tone_plan.joke}"
            if tone_plan.opener and response and not response.startswith(tone_plan.opener):
                response = f"{tone_plan.opener} {response}"
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
        # Keep the interpreted intent accessible to API consumers
        # (intent_value already set earlier for the conversation driver).
        used_evidence_ids = tuple(act_result.data.get("used_evidence_ids", []))
        used_evidence = [item for item in self.workspace.evidence if item.evidence_id in used_evidence_ids]
        grounded_utterance = self.language_grounder.ground(
            response,
            raw_input=text_input,
            intent=intent_value,
            confidence=float(act_result.data.get("confidence", 0.5)),
            evidence_count=len(used_evidence),
            hypothesis_count=len(self.workspace.hypotheses),
            strategy="causal_plan_execution",
            grounding_source=str(act_result.data.get("grounding_source", "fallback")),
            evidence_sources=tuple(item.source for item in used_evidence),
            evidence_ids=tuple(item.evidence_id for item in used_evidence),
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

    # Subjects that refer to the brain itself in identity questions —
    # normalised to "Misty" before the identity lookup runs.
    _SELF_SUBJECTS = frozenset(
        {
            "তুমি",
            "তোমাকে",
            "আপনি",
            "আপনাকে",
            "মিস্টি",
            "মিস্টিকে",
            "you",
        }
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
                # Phase 28: a QUERY_WHO always carries an explicit subject
                # ("MistLook কে তৈরি করেছ?"). When the subject is a real
                # named entity and the parser left the target empty, the
                # subject IS the answer target — inheriting an unrelated
                # prior topic ("creator") would be wrong, so prefer the
                # subject over prior-topic inheritance in that case.
                _subject = parse_result.query.get("subject", "")
                if parse_result.intent is IntentType.QUERY_WHO and _subject and _subject not in self._SELF_SUBJECTS:
                    parse_result.query["target"] = _subject
                    parse_result.entities["coreference_target"] = _subject
                elif not target or target in self._PRONOUN_TOKENS:
                    # Phase 23: use a previous-turn topic, not a token from the
                    # current input (current-turn salient entities
                    # would just echo the bare word like "কারণ" back at
                    # the user).
                    prior_topic = self._prior_topic(
                        exclude=_current_token_set(parse_result.raw_text),
                        parse_result=parse_result,
                    )
                    if prior_topic:
                        parse_result.query["target"] = prior_topic
                        parse_result.entities["coreference_target"] = prior_topic
        # Phase 23: bare follow-up questions ("সেটা কী?", "কারণ কী?", "আর বলো")
        # inherit the last conversation topic so the thread stays alive.
        self._resolve_bare_followup(parse_result)
        # Phase 28: anchor the dialogue topic to the query's resolved target
        # so follow-up turns ("Why?", "কারণ কী?") inherit a meaningful
        # topic instead of the raw scraped sentence words ("the", "আকাশের").
        # Phase 28: anchor the topic to a target the USER explicitly asked
        # about. Inherited / resolved targets ("কারণ", "কাজ", "color") are
        # follow-up words and must never overwrite a real topic anchor
        # ("আকাশের রঙ", "sky") that later follow-ups like "Why?" need.
        _qtarget = parse_result.query.get("target", "")
        _coref = parse_result.entities.get("coreference_target", "")
        if parse_result.intent in (IntentType.QUERY_WHO, IntentType.QUERY_WHAT) and _qtarget and not _coref:
            self.dialogue_context.topic = _qtarget
        if not parse_result.entities and parse_result.intent in (
            IntentType.STATEMENT,
            IntentType.UNKNOWN,
            IntentType.CONTINUATION,
            IntentType.CORRECTION,
            IntentType.TEACH,
        ):
            resolved = resolve_entities(parse_result.raw_text, self.dialogue_context.get_salient_entities())
            if resolved:
                parse_result.entities["resolved_entities"] = resolved

    # Phase 23: bare follow-up resolution constants.
    _BARE_FOLLOWUP_PATTERN = re.compile(
        r"(সেট|এট|ওট|এগুল|ওগুল)\b|^(কারণ|কারণট|কী কারণ|কেনো|তারপর|"
        r"তারপরে|আর|আরব|আরে|আরে বল|আর বল|আরে বলে|আরব বল|আরে বলে|"
        r"আরে জনাও|জনাও|বলে দাও)\b"
    )
    _BARE_FOLLOWUP_PATTERNS = (
        re.compile(r"^কারণ|কারণ ক|কী কারণ|কারণটা|কেন|কেনো|(?i:\bwhy\b)"),
        re.compile(r"^কারণ|কারণ ক|কী কারণ|কারণটা"),
        re.compile(r"^আর|আর বল|আরো বল|আরব বল|বলে দাও|জানাও|আর জানাও"),
    )
    # Phase 23: how many recent turns to look back at for context phrases.
    _CONTEXT_WINDOW: int = 4
    # Phase 23: discourse tokens that must never be treated as a topic.
    _DISCOURSE_TOKENS = frozenset(
        {
            "আর",
            "আরো",
            "আরব",
            "কারণ",
            "কারণে",
            "কারণটা",
            "কারণটি",
            "এখন",
            "তখন",
            "পরে",
            "আগে",
            "তাই",
            "এটাই",
            "বেশ",
            "আচ্ছা",
            # Explicit-teaching trigger words must never be picked as the
            # conversation topic ("মনে রাখো: X হলো Y" → topic = X). These
            # also appear in DialogueContext's extraction ban list.
            "মনে",
            "রাখো",
            "রাখুন",
            "রাখা",
            "জানি",
            "জানাও",
            "শেখো",
            "শেখাও",
            "শেখে",
            "বলো",
            "বলুন",
            "বলে",
            "বলা",
        }
    )

    # Phase 28: interrogative heads that must never seed a topic —
    # "What is gravity?" must anchor "gravity", not "What".
    _INTERROGATIVE_TOKENS = frozenset(
        (
            "what",
            "who",
            "how",
            "why",
            "where",
            "when",
            "which",
            "কি",
            "কী",
            "কেন",
            "কেনো",
            "কিসে",
            "কিসের",
            "কিভাবে",
            "কিভাবে",
            "কোথায়",
            "কখন",
            "কোন",
            "কোনটা",
        )
    )

    # Phase 28: salient stop tokens that must never make a good topic
    # ("Remember that a drone is ..." -> topic "drone", not "Remember").
    _SALIENT_STOP_TOKENS = frozenset(
        (
            "a",
            "an",
            "the",
            "is",
            "are",
            "was",
            "were",
            "be",
            "been",
            "being",
            "am",
            "do",
            "does",
            "did",
            "of",
            "in",
            "on",
            "at",
            "to",
            "for",
            "with",
            "from",
            "about",
            "it",
            "that",
            "this",
            "remember",
            "keep",
            "note",
            "learn",
            "মনে",
            "রাখো",
            "রাখুন",
            "এটা",
            "সেটা",
            "ওটা",
            "এটি",
            "সেটি",
            "আছে",
            "আছো",
            "হয়",
            "থেকে",
            "দিয়ে",
        )
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
                # Phase 28: reason follow-ups ("কারণ কি?", "Why?")
                # inherit the why-relation so the answer is composed
                # from reason facts instead of a casual-chat reply.
                if pattern is self._BARE_FOLLOWUP_PATTERNS[1]:
                    parse_result.query["relation"] = "why"
                    parse_result.query["type"] = "why"
                    if parse_result.intent is IntentType.CONVERSATION:
                        # Bare reason words parsed as casual chat are
                        # promoted to structured why-queries.
                        parse_result.intent = IntentType.QUERY_WHAT
                return

    def _prior_topic(
        self,
        exclude: set | None = None,
        parse_result: ParseResult | None = None,
    ) -> str | None:
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
        # Phase 28: prefer entities the brain actively marked salient in
        # the prior turns (taught subjects, queried entities) over a raw
        # word-scrape, so "মনে রাখো: সেতু হলো ...||সেট কী?" inherits
        # the taught subject "সেতু" instead of the sentence tail "রাস্তা".
        # Phase 28: salient entities scraped from the CURRENT turn (it is
        # already in history by the time topic resolution runs) must not
        # seed the topic — filter them out so "এর কাজ কি?" does not inherit
        # the word "কাজ" from its own input.
        # Phase 28: salient entities scraped from the CURRENT turn (it is
        # already in history by the time topic resolution runs) must not
        # seed the topic — BUT only when the current turn is a bare or
        # pronominal follow-up. If the user explicitly names an entity
        # ("MistLook কে তৈরি করেছে?"), the parser already carries that
        # target and the salient list must NOT be filtered by the
        # current-turn words, otherwise the named entity gets removed
        # while a bare predicate word ("creator") survives the filter.
        _cur_words = set()
        if parse_result is not None:
            _target = parse_result.query.get("target", "")
            _has_own_entity = bool(_target) or bool(
                parse_result.entities.get("coreference_target", ""),
            )
            if not _has_own_entity and parse_result.raw_text:
                _cur_norm = re.sub(r"[^\w\u0980-\u09ff]", " ", parse_result.raw_text or "").strip()
                _cur_words = {w.lower() for w in _cur_norm.split() if w and len(w) > 2}
        salient_lower = {e.lower() for e in self.dialogue_context.salient_entities if e.lower() not in _cur_words}
        first_valid = None
        salient_match = None
        # reversed() starts with the MOST RECENT prior turn — that position
        # is where salient entities may outrank the raw scrape.
        for _pos, turn in enumerate(reversed(prior_texts)):
            if not prior_texts:
                break
            norm = re.sub(r"[^\w\u0980-\u09ff]", " ", turn or "").strip()
            words = [w for w in norm.split() if w and len(w) > 2]
            # Phase 28: scan from the most recent word first so a bare
            # follow-up ("Why?", "আর বলো") inherits the LAST thing the
            # user actually said, not the first.
            for word in reversed(words):
                base = self._normalize_bengali_word(word)
                if base in self._DISCOURSE_TOKENS or base in exclude:
                    continue
                # Phase 28: interrogative heads ("What is gravity?") must
                # never seed the topic — checked case-insensitively.
                if base in self._PRONOUN_TOKENS or base in self._INTERROGATIVE_TOKENS:
                    continue
                if base.lower() in self._INTERROGATIVE_TOKENS:
                    continue
                # Phase 28: salient stop words (articles, copulas, BN
                # particles, discourse verbs like "remember") never make
                # good topics.
                if base in self._SALIENT_STOP_TOKENS or base.lower() in self._SALIENT_STOP_TOKENS:
                    continue
                if first_valid is None:
                    first_valid = base
                # Salient entities the brain actively tracked outrank the
                # generic scrape, but only when they appeared in the MOST
                # RECENT prior turn — a salient entity from an older turn
                # must not outrank a word the user just said ("color of
                # the sky" || "Why?" -> topic "sky", not "color").
                # Phase 28: salient entities the brain actively tracked
                # outrank the generic scrape, but only when they appeared
                # in the MOST RECENT prior turn AND the entity is a real
                # knowledge-base entry — a bare predicate word scraped as
                # salient ("creator" in "MistLook-এর creator") must never
                # outrank the actual entity ("MistLook") that carries
                # stored facts.
                if _pos == 0 and base.lower() in salient_lower and self._entity_has_knowledge(base):
                    salient_match = base
        if salient_match:
            return salient_match
        return first_valid

    def _entity_has_knowledge(self, name: str) -> bool:
        """True if the named entity has stored facts anywhere in the brain.

        Used by topic resolution so that scraped salient words that are
        actually predicates or filler ("creator", "reason") do not seed the
        dialogue topic when a real entity with knowledge exists."""
        if (
            self.concept_graph.get_concept_by_name(name)
            or self.semantic_memory.query(subject=name, predicate="is_a")
            or self.semantic_memory.query(subject=name, predicate="color")
            or self.semantic_memory.query(subject=name, predicate="use")
            or self.semantic_memory.query(subject=name, predicate="capability")
            or self.semantic_memory.query(subject=name, predicate="creator_of")
            or self.semantic_memory.query(obj=name)
            or self.semantic_memory.query(subject=name, predicate="relation")
        ):
            return True
        return False

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
        # Farewell turns are answered by a proper goodbye instead of the
        # generic conversational reply below; the driver's closure plan
        # (process(), Phase 25) then installs the full farewell line.
        if parse_result.entities.get("closure"):
            return ("", 0.9)
        # Phase 28: safe-humor requests get a joke as the actual reply
        # instead of an unknown fallback with a tacked-on joke.
        if self.tone_mapper._user_humor(parse_result.raw_text):
            is_bn = any("\u0980" <= ch <= "\u09ff" for ch in parse_result.raw_text)
            pool = tone_module.HUMOR_JOKES["bn" if is_bn else "en"]
            keyed = [j for j in pool if ("রসিকতা" if is_bn else "joke") in j]
            # Deterministic per-text rotation among keyword-anchored jokes.
            joke = keyed[int(hash(parse_result.raw_text) % len(keyed))] if keyed else pool[0]
            opener = "একটি ছোট্ট রসিকতা শোনাই — " if is_bn else "Here is a small joke for you — "
            return f"{opener}{joke}", 0.7
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
                response = f"আপনি ঠিক আছেন! {anchor} আমি এটি একটু সহজ করে বলছি — দেখুন কোনো অংশ আবার বুঝিয়ে বলতে পারি?"
            else:
                response = (
                    "আপনি ঠিক আছেন! আমি একটু সহজ করে বলছি: আমি একটি ডিজিটাল "
                    "ব্রেন — আমি আপনার আগের কথার উপর ভিত্তি করে কাছে, চিন্তা করি এব "
                    "আমার সংরক্ষিত জ্ঞান থেকে উত্তর তৈরি করি। কোনো অংশটি আবার "
                    "বুঝিয়ে বলি?"
                )
            return response, 0.75
        if re.search(r"কি ব্যাপার|কী ব্যাপার", text):
            response = f"কোনো ব্যাপার নয়! আমি ভালো আছি এবং আপনার কথা শুনছি। {self_model_text} বলুন, কী নিয়ে কথা হবে?"
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
            response = f"Nothing special — just processing and learning! {self_model_text} What shall we talk about?"
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
        # Phase 24: pick a varied friendly reply so casual turns do not
        # echo the same "আমি আপনার কথাটি শুনলাম। ..." sentence.
        friendly = self.variator.pick("conversation", text)
        response = f"{friendly} {self_model_text}" if friendly else (f"আমি আপনার কথাটি শুনলাম। {self_model_text}")
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
                    "কি",
                    "কী",
                    "কিছু",
                    "আমি",
                    "তুমি",
                    "আপনি",
                    "এটা",
                    "সেটা",
                    "ওটা",
                    "আছ",
                    "আছো",
                    "করছ",
                }:
                    continue
                salient = self.dialogue_context.get_salient_entities()
                salient = [e for e in salient if e not in self._DISCOURSE_TOKENS]
                if salient and candidate.lower() == salient[0].lower():
                    return f"আপনি আগে {candidate} নিয়ে কথা বলছিলেন — "
                if salient:
                    continue
            salient = [e for e in self.dialogue_context.get_salient_entities() if e not in self._DISCOURSE_TOKENS]
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

    # Phase 25: conversation driver plan — decide the follow-up shape for
    # this turn before the response is finalized in `process()`.
    def _is_generic_unknown_reply(self, response: str) -> bool:
        """Phase 27: True when the response is one of the generic
        unknown-input fallbacks from the personality pool or the
        hard-coded unknown handler — those are safe to replace with a
        contextually better reply (e.g. a farewell for closure inputs).
        """
        generic_markers = (
            "working memory",
            "learning opportunity",
            "parse করতে পারিনি",
            "বুঝতে শিখিনি",
            "বিশ্লেষণ করতে পারছি না",
            "could not resolve the intent",
            "could not parse its intent",
            "I heard you, but",
        )
        return response and any(marker and marker in response for marker in generic_markers)

    def _driver_plan(self, user_text: str, response: str, intent: str, confidence: float) -> Any:
        """Build the conversation-driver plan for this turn.

        Topic knowledge depth (is_a facts about the topic, unexplored
        neighbors) decides between a continuation nudge and an
        interest-expansion question; empathy shapes reply to expressed
        user states; closure greetings suppress follow-ups entirely.
        """
        exclude = _current_token_set(user_text)
        topic = self._prior_topic(exclude=exclude) or self.dialogue_context.topic
        topic_facts = 0
        if topic:
            facts = self.semantic_memory.query(subject=topic, predicate="is_a")
            topic_facts = len(facts) if facts else 0
        has_related = False
        if topic:
            concept = self.concept_graph.get_concept_by_name(topic)
            if concept:
                related = self.concept_graph.find_related(concept.concept_id, direction="outgoing")
                has_related = bool(related)

        return self.conversation_driver.plan_followup(
            user_text=user_text,
            response=response,
            intent=intent,
            confidence=float(confidence),
            topic=topic,
            topic_facts=topic_facts,
            has_related=has_related,
        )

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

    def _normalize_what_target_for_recall(self, parse_result: ParseResult) -> None:
        """Resolve deterministic WHAT target variants before evidence retrieval.

        The compatibility ACT handler historically normalized compounds,
        inflections, and inherited topics after RECALL. Doing the same bounded
        normalization here lets REASON rank the facts that ACT can consume and
        preserves their provenance through the causal pipeline.
        """
        if parse_result.intent != IntentType.QUERY_WHAT:
            return

        target_name = parse_result.query.get("target", "")
        relation = parse_result.query.get("relation", "")
        target_tokens = {token.casefold() for token in re.findall(r"[A-Za-z\u0980-\u09ff]+", target_name)}
        if relation in {"", "is_a"}:
            attribute_predicates = {
                "color": {"color", "colour", "রঙ"},
                "use": {"use", "uses", "ব্যবহার", "কাজ"},
                "capability": {"capability", "ক্ষমতা"},
            }
            for predicate, markers in attribute_predicates.items():
                if target_tokens & markers:
                    relation = predicate
                    parse_result.query["relation"] = predicate
                    break
        if not target_name or relation in {"use", "capability", "why", "how"}:
            inherited = self.dialogue_context.topic
            if not inherited:
                inherited = self._prior_topic(
                    exclude=_current_token_set(parse_result.raw_text) | self._INTERROGATIVE_TOKENS,
                    parse_result=parse_result,
                )
            if inherited:
                target_name = inherited

        if not target_name:
            return

        if " " in target_name:
            stop_words = (
                self._SALIENT_STOP_TOKENS
                | self._INTERROGATIVE_TOKENS
                | {
                    "of",
                    "the",
                    "a",
                    "an",
                    "in",
                    "on",
                    "at",
                    "with",
                    "from",
                }
            )
            is_bengali = any("\u0980" <= char <= "\u09ff" for char in target_name)
            candidates = target_name.split() if is_bengali else list(reversed(target_name.split()))
            if not self._definition_or_concept(target_name):
                target_name = next(
                    (
                        word
                        for word in candidates
                        if word.casefold() not in stop_words and self._definition_or_concept(word)
                    ),
                    next((word for word in candidates if word.casefold() not in stop_words), target_name),
                )

        if not target_name.isascii() and " " not in target_name:
            base = self._normalize_bengali_word(target_name)
            if base != target_name and self._definition_or_concept(base):
                target_name = base
        elif target_name.endswith("s") and len(target_name) > 3 and not self._definition_or_concept(target_name):
            if target_name.endswith("ies") and len(target_name) > 4:
                singular = target_name[:-3] + "y"
            elif target_name.endswith("es") and len(target_name) > 4:
                singular = target_name[:-2]
            else:
                singular = target_name[:-1]
            if self._definition_or_concept(singular):
                target_name = singular

        parse_result.query["target"] = target_name

    def _phase_recall(self, parse_result: ParseResult | None) -> CycleResult:
        """RECALL phase: retrieve memories and broadcast their provenance."""
        self.state.current_phase = "recall"
        recalled: Dict[str, Any] = {"evidence_ids": []}

        if not parse_result:
            return CycleResult(phase=CognitivePhase.RECALL, data=recalled, success=True)

        self._normalize_what_target_for_recall(parse_result)
        target_name = parse_result.query.get("target", "")
        relation = parse_result.query.get("relation", "")
        if target_name:
            target_concept = self.concept_graph.get_concept_by_name(target_name)
            if target_concept:
                self.recall_scorer.record_recall(target_concept.concept_id)
                recalled["recall_scores"] = self.recall_scorer.score(
                    target_concept.concept_id,
                    emotional_valence=self._current_valence(),
                )

        facts = []
        if parse_result.intent == IntentType.QUERY_WHO and target_name:
            facts = self.semantic_memory.query(predicate=relation or None, obj=target_name)
        elif parse_result.intent == IntentType.QUERY_WHAT and target_name:
            facts = self.semantic_memory.query(subject=target_name)
            predicate_groups = {
                "is_a": {"is_a", "definition", "সংজ্ঞা", "সূত্র", "formula"},
                "color": {"color"},
                "use": {"use", "is_a"},
                "capability": {"capability", "use", "is_a"},
                "why": {"why_reason", "day_color_reason", "color", "is_a"},
                "how": {"why_reason", "day_color_reason", "color", "use", "is_a"},
            }
            relevant_predicates = predicate_groups.get(relation)
            if relevant_predicates:
                facts = [fact for fact in facts if fact.predicate in relevant_predicates]

        if facts:
            semantic_facts = []
            for fact in facts:
                record = {
                    "subject": fact.subject,
                    "predicate": fact.predicate,
                    "obj": fact.obj,
                    "source": fact.source,
                    "confidence": float(fact.confidence),
                }
                evidence = Evidence(
                    source=fact.source or "semantic_memory",
                    content={"kind": "semantic_fact", **record},
                    confidence=float(fact.confidence),
                )
                self.workspace.broadcast_evidence(evidence)
                record["evidence_id"] = evidence.evidence_id
                recalled["evidence_ids"].append(evidence.evidence_id)
                semantic_facts.append(record)
            recalled["semantic_facts"] = semantic_facts

        if target_name:
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

            target_concept = self.concept_graph.get_concept_by_name(target_name)
            if target_concept:
                direction = "incoming" if parse_result.intent == IntentType.QUERY_WHO else "both"
                graph_relations = self.concept_graph.get_relations(target_concept.concept_id, direction=direction)
                if parse_result.intent == IntentType.QUERY_WHO and relation:
                    graph_relations = [item for item in graph_relations if item.get("relation_type") == relation]
                if graph_relations:
                    recalled_relations = []
                    for relation_record in graph_relations:
                        record = {**relation_record, "evidence_source": "knowledge_graph"}
                        evidence = Evidence(
                            source="knowledge_graph",
                            content={"kind": "graph_relation", **record},
                            confidence=float(record.get("confidence", 1.0)),
                        )
                        self.workspace.broadcast_evidence(evidence)
                        record["evidence_id"] = evidence.evidence_id
                        recalled["evidence_ids"].append(evidence.evidence_id)
                        recalled_relations.append(record)
                    recalled["graph_relations"] = recalled_relations

        return CycleResult(phase=CognitivePhase.RECALL, data=recalled, success=True)

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
                    # concepts that fired together this cycle. Assessment
                    # clones perform retrieval only and must not learn from
                    # benchmark prompts.
                    if not self._assessment_mode:
                        hebbian_updates = self.hebbian.update(self.concept_graph, list(activated.keys()))
                        if hebbian_updates:
                            self.working_memory.store("hebbian_updates", hebbian_updates)
        # Phase 4: Hebbian bookkeeping (also covers the neural path).
        if not self._assessment_mode:
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

    def _phase_reason(
        self,
        parse_result: ParseResult | None,
        recall_data: Dict[str, Any] | None = None,
        associate_data: Dict[str, Any] | None = None,
    ) -> CycleResult:
        """REASON phase: derive answer candidates from recalled evidence."""
        self.state.current_phase = "reason"
        recall_data = recall_data or {}
        associate_data = associate_data or {}
        derived: List[Dict[str, Any]] = []
        answer_candidates: List[Dict[str, Any]] = []

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

            target_name = parse_result.query.get("target", "")
            relation = parse_result.query.get("relation", "")
            subject = parse_result.query.get("subject", "")
            self_names = {"misty", "মিস্টি", "মিস্টিকে"}
            self_references = {str(item).casefold() for item in self._SELF_SUBJECTS} | self_names
            protected_identity_query = (
                parse_result.intent == IntentType.QUERY_WHO
                and relation in {"creator_of", "made_by"}
                and (str(target_name).casefold() in self_names or str(subject).casefold() in self_references)
            )
            if protected_identity_query:
                response, confidence = self._act_query_self(parse_result)
                identity_evidence = Evidence(
                    source="protected_self_model",
                    content={
                        "kind": "protected_identity",
                        "subject": "Misty",
                        "predicate": "made_by",
                        "obj": "Pixline Incorporate / Salauddin Mir",
                    },
                    confidence=confidence,
                )
                self.workspace.broadcast_evidence(identity_evidence)
                answer_candidates.append(
                    {
                        "answer": response,
                        "response": response,
                        "source": "protected_self_model",
                        "predicate": "made_by",
                        "confidence": confidence,
                        "evidence_ids": [identity_evidence.evidence_id],
                        "trust_priority": 100,
                    }
                )

            for fact in recall_data.get("semantic_facts", []):
                if parse_result.intent == IntentType.QUERY_WHO:
                    answer = str(fact.get("subject", "")).strip()
                    response = answer
                elif parse_result.intent == IntentType.QUERY_WHAT:
                    answer = str(fact.get("obj", "")).strip()
                    response = (
                        f"{target_name} is {answer}." if target_name.isascii() else f"{target_name} হলো {answer}।"
                    )
                else:
                    continue
                if answer:
                    answer_candidates.append(
                        {
                            "answer": answer,
                            "response": response,
                            "source": fact.get("source", "semantic_memory"),
                            "predicate": fact.get("predicate"),
                            "confidence": float(fact.get("confidence", 0.5)),
                            "evidence_ids": [fact["evidence_id"]] if fact.get("evidence_id") else [],
                        }
                    )

            for relation_record in recall_data.get("graph_relations", []):
                if parse_result.intent == IntentType.QUERY_WHAT:
                    relevant_graph_predicates = {
                        "is_a": {"is_a"},
                        "color": {"color"},
                        "use": {"use", "uses"},
                        "capability": {"capability", "use", "uses"},
                        "why": {"why_reason", "day_color_reason", "color"},
                        "how": {"why_reason", "day_color_reason", "use", "uses"},
                    }.get(relation)
                    if (
                        relevant_graph_predicates is not None
                        and relation_record.get("relation_type") not in relevant_graph_predicates
                    ):
                        continue
                if parse_result.intent == IntentType.QUERY_WHO:
                    answer_id = relation_record.get("source")
                elif relation_record.get("source"):
                    target_concept = self.concept_graph.get_concept_by_name(target_name)
                    answer_id = (
                        relation_record.get("target")
                        if target_concept and relation_record.get("source") == target_concept.concept_id
                        else relation_record.get("source")
                    )
                else:
                    answer_id = None
                answer_concept = self.concept_graph.get_concept(answer_id) if answer_id else None
                if answer_concept:
                    response = answer_concept.name
                    if parse_result.intent == IntentType.QUERY_WHAT:
                        response = (
                            f"{target_name} is related to {answer_concept.name}."
                            if target_name.isascii()
                            else f"{target_name} {answer_concept.name}-এর সাথে সম্পর্কিত।"
                        )
                    answer_candidates.append(
                        {
                            "answer": answer_concept.name,
                            "response": response,
                            "source": "knowledge_graph",
                            "predicate": relation_record.get("relation_type"),
                            "confidence": float(relation_record.get("confidence", 0.5)),
                            "evidence_ids": [relation_record["evidence_id"]]
                            if relation_record.get("evidence_id")
                            else [],
                        }
                    )

            composition_relations = {"use", "capability", "why", "how"}
            semantic_facts = recall_data.get("semantic_facts", [])
            if parse_result.intent == IntentType.QUERY_WHAT and relation in composition_relations and semantic_facts:
                details = list(dict.fromkeys(str(fact.get("obj", "")).strip() for fact in semantic_facts))
                details = [detail for detail in details if detail]
                evidence_ids = list(
                    dict.fromkeys(str(fact.get("evidence_id")) for fact in semantic_facts if fact.get("evidence_id"))
                )
                if details and evidence_ids:
                    joined_details = ", ".join(details[:4])
                    is_bengali = any("\u0980" <= char <= "\u09ff" for char in parse_result.raw_text)
                    response = (
                        f"{target_name} সম্পর্কে সংরক্ষিত তথ্য: {joined_details}।"
                        if is_bengali
                        else f"From my stored knowledge about {target_name}: {joined_details}."
                    )
                    answer_candidates.append(
                        {
                            "answer": joined_details,
                            "response": response,
                            "source": "semantic_composition",
                            "predicate": relation,
                            "confidence": min(float(fact.get("confidence", 0.5)) for fact in semantic_facts),
                            "evidence_ids": evidence_ids,
                            "trust_priority": 10,
                        }
                    )

        context = parse_result.raw_text if parse_result else ""
        if context and hasattr(self, "procedural_memory") and self.procedural_memory.size > 0:
            procedure = self.procedural_memory.get_strongest(context)
            if procedure:
                # Evaluation must never invoke the process-wide reinforcement
                # persistence hook installed by the API lifespan.
                if not self._assessment_mode:
                    procedure.reinforce(success=True, amount=0.05)
                procedure_evidence = Evidence(
                    source="procedural_memory",
                    content={
                        "kind": "procedure",
                        "procedure_id": procedure.procedure_id,
                        "name": procedure.name,
                        "action": procedure.action,
                    },
                    confidence=procedure.strength,
                )
                self.workspace.broadcast_evidence(procedure_evidence)
                derived.append(
                    {
                        "procedure": procedure.name,
                        "action": procedure.action,
                        "strength": procedure.strength,
                        "evidence_id": procedure_evidence.evidence_id,
                    }
                )

        # Rank before deduplicating so duplicate answers retain the
        # strongest evidence rather than whichever store happened to be
        # iterated first.
        answer_candidates.sort(
            key=lambda item: (
                int(item.get("trust_priority", 0)),
                float(item.get("confidence", 0.0)),
            ),
            reverse=True,
        )
        ranked_candidates: List[Dict[str, Any]] = []
        seen_answers: set[str] = set()
        for candidate in answer_candidates:
            answer_key = str(candidate.get("answer", "")).strip().casefold()
            if not answer_key or answer_key in seen_answers:
                continue
            seen_answers.add(answer_key)
            ranked_candidates.append(candidate)
        derived.extend(ranked_candidates)
        if parse_result and ranked_candidates and parse_result.intent in {IntentType.QUERY_WHO, IntentType.QUERY_WHAT}:
            selected = ranked_candidates[0]
            self.state.add_thought(
                "inference_synthesis",
                [
                    f"REASON selected predicate {selected.get('predicate') or 'unknown'} using ranked evidence.",
                    f"PLAN received {len(selected.get('evidence_ids', []))} supporting evidence item(s).",
                ],
            )
        return CycleResult(
            phase=CognitivePhase.REASON,
            data={
                "derived": derived,
                "answer_candidates": ranked_candidates,
                "selected_answer": ranked_candidates[0] if ranked_candidates else None,
                "recall_evidence_ids": list(recall_data.get("evidence_ids", [])),
                "association_count": len(associate_data.get("activation_map", {})),
            },
            success=True,
        )

    def _phase_plan(
        self,
        parse_result: ParseResult | None,
        reason_data: Dict[str, Any] | None = None,
    ) -> CycleResult:
        """PLAN phase: select an executable action using reasoning output."""
        self.state.current_phase = "plan"
        reason_data = reason_data or {}
        if not parse_result:
            return CycleResult(
                phase=CognitivePhase.PLAN,
                data={"plan": "request_clarification", "executable": False, "reason": "missing_parse_result"},
                success=False,
            )
        intent = parse_result.intent.value
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

        plan_by_intent = {
            IntentType.NAME_DECLARATION: "store_identity",
            IntentType.RELATION_DECLARATION: "store_relation",
            IntentType.QUERY_WHO: "answer_query",
            IntentType.QUERY_WHAT: "answer_query",
            IntentType.GREETING: "greet_back",
            IntentType.CONVERSATION: "converse_friendly",
            IntentType.MATH: "solve_mathematics",
            IntentType.PHYSICS: "solve_physics",
            IntentType.TEACH: "absorb_knowledge",
            IntentType.STATEMENT: "absorb_knowledge",
            IntentType.CORRECTION: "absorb_knowledge",
            IntentType.CONTINUATION: "continue_topic",
            IntentType.CAPABILITY_QUERY: "describe_capabilities",
            IntentType.RECOGNITION_QUERY: "recall_identity",
        }
        plan = plan_by_intent.get(parse_result.intent, "request_clarification")
        executable = plan in set(plan_by_intent.values()) | {"request_clarification"}
        return CycleResult(
            phase=CognitivePhase.PLAN,
            data={
                "plan": plan,
                "active_goal": goal.goal_id,
                "expected_intent": intent,
                "executable": executable,
                "selected_answer": reason_data.get("selected_answer"),
                "reason_evidence_ids": list(reason_data.get("recall_evidence_ids", [])),
            },
            success=executable,
        )

    def _phase_act(
        self,
        parse_result: ParseResult | None,
        recall_data: Dict[str, Any],
        associate_data: Dict[str, Any],
        reason_data: Dict[str, Any],
        plan_data: Dict[str, Any],
    ) -> CycleResult:
        """ACT phase: validate and execute the selected causal plan."""
        self.state.current_phase = "act"

        if not parse_result:
            return CycleResult(
                phase=CognitivePhase.ACT,
                data={
                    "response": "Please clarify what you would like me to do.",
                    "confidence": 0.3,
                    "grounding_source": "fallback",
                    "plan": plan_data.get("plan"),
                    "used_evidence_ids": [],
                },
                success=False,
            )

        plan = str(plan_data.get("plan", ""))
        allowed_intents = {
            "store_identity": {IntentType.NAME_DECLARATION},
            "store_relation": {IntentType.RELATION_DECLARATION},
            "answer_query": {IntentType.QUERY_WHO, IntentType.QUERY_WHAT},
            "absorb_knowledge": {IntentType.TEACH, IntentType.STATEMENT, IntentType.CORRECTION},
            "continue_topic": {IntentType.CONTINUATION},
            "describe_capabilities": {IntentType.CAPABILITY_QUERY},
            "recall_identity": {IntentType.RECOGNITION_QUERY},
            "converse_friendly": {IntentType.CONVERSATION},
            "greet_back": {IntentType.GREETING},
            "solve_mathematics": {IntentType.MATH},
            "solve_physics": {IntentType.PHYSICS},
            "request_clarification": {parse_result.intent},
        }
        plan_matches_intent = parse_result.intent in allowed_intents.get(plan, set())
        expected_intent = plan_data.get("expected_intent")
        if (
            not plan_data.get("executable", False)
            or not plan_matches_intent
            or (expected_intent and expected_intent != parse_result.intent.value)
        ):
            is_bengali = any("\u0980" <= char <= "\u09ff" for char in parse_result.raw_text)
            response = (
                "নির্বাচিত পরিকল্পনাটি এই অনুরোধের জন্য নিরাপদে কার্যকর করা যাচ্ছে না। অনুগ্রহ করে অনুরোধটি স্পষ্ট করুন।"
                if is_bengali
                else "The selected plan is not executable for this request. Please clarify what you want me to do."
            )
            return CycleResult(
                phase=CognitivePhase.ACT,
                data={
                    "response": response,
                    "confidence": 0.25,
                    "grounding_source": "fallback",
                    "plan": plan,
                    "used_evidence_ids": [],
                    "rejection_reason": "plan_intent_mismatch_or_not_executable",
                },
                success=False,
            )

        response = ""
        confidence = 0.5
        grounding_source = "direct_knowledge"
        used_evidence_ids: List[str] = []
        selected_answer = plan_data.get("selected_answer") or reason_data.get("selected_answer")
        selected_response = ""
        selected_evidence_ids: List[str] = []
        selected_supported = False
        if selected_answer:
            selected_response = str(selected_answer.get("response") or selected_answer.get("answer") or "").strip()
            selected_evidence_ids = list(selected_answer.get("evidence_ids", []))
            selected_supported = bool(selected_response and selected_evidence_ids)

        used_selected_answer = False
        if plan == "store_identity":
            response, confidence = self._run_learning_action(self._act_name_declaration, parse_result)
        elif plan == "store_relation":
            response, confidence = self._run_learning_action(self._act_relation_declaration, parse_result)
        elif (
            plan == "answer_query"
            and parse_result.intent in {IntentType.QUERY_WHO, IntentType.QUERY_WHAT}
            and selected_supported
        ):
            # For supported factual queries the ranked REASON decision is
            # authoritative. ACT must not independently re-query insertion-
            # ordered stores and silently execute a different answer.
            response = selected_response
            confidence = float(selected_answer.get("confidence", 0.5))
            used_evidence_ids = selected_evidence_ids
            grounding_source = "reason_derived_evidence"
            used_selected_answer = True
        elif plan == "answer_query" and parse_result.intent == IntentType.QUERY_WHO:
            response, confidence = self._act_query(parse_result, recall_data)
        elif plan == "answer_query" and parse_result.intent == IntentType.QUERY_WHAT:
            # Normalized/aliased targets that could not participate in RECALL
            # still use the compatibility handler; consumed facts are turned
            # into explicit evidence below.
            response, confidence = self._act_query_what(parse_result, recall_data)
        elif plan == "absorb_knowledge" and parse_result.intent == IntentType.STATEMENT:
            response, confidence = self._run_learning_action(self._act_statement, parse_result)
        elif plan == "absorb_knowledge" and parse_result.intent == IntentType.TEACH:
            response, confidence = self._run_learning_action(self._act_teach, parse_result)
        elif plan == "absorb_knowledge" and parse_result.intent == IntentType.CORRECTION:
            response, confidence = self._run_learning_action(self._act_correction, parse_result)
        elif plan == "continue_topic":
            response, confidence = self._act_continuation(parse_result)
        elif plan == "describe_capabilities":
            response, confidence = self._act_capability(parse_result)
        elif plan == "recall_identity":
            response, confidence = self._act_recognition(parse_result)
        elif plan == "converse_friendly":
            response, confidence = self._act_conversation(parse_result)
            grounding_source = "fallback"
        elif plan == "greet_back":
            response, confidence = self._act_greeting(parse_result)
            grounding_source = "fallback"
        elif plan == "solve_mathematics":
            response, confidence = self._act_math(parse_result)
        elif plan == "solve_physics":
            response, confidence = self._act_physics(parse_result)
        elif selected_supported:
            response = selected_response
            confidence = float(selected_answer.get("confidence", 0.5))
            used_evidence_ids = selected_evidence_ids
            grounding_source = "reason_derived_evidence"
        else:
            response, confidence = self._act_unknown(parse_result)
            grounding_source = "fallback"

        # A compatibility WHAT handler records the exact semantic facts it
        # rendered. When target normalization or alias resolution happened
        # after RECALL, broadcast those consumed facts now so a fact-backed
        # response can never claim direct knowledge without evidence lineage.
        if plan == "answer_query" and parse_result.intent == IntentType.QUERY_WHAT and not used_selected_answer:
            used_fact_keys = set(getattr(self, "_last_query_what_fact_keys", []))
            supporting_records = [
                fact
                for fact in recall_data.get("semantic_facts", [])
                if (str(fact.get("subject", "")), str(fact.get("predicate", "")), str(fact.get("obj", "")))
                in used_fact_keys
            ]
            recalled_keys = {
                (str(fact.get("subject", "")), str(fact.get("predicate", "")), str(fact.get("obj", "")))
                for fact in supporting_records
            }
            for fact in self.semantic_memory.facts.values():
                fact_key = (fact.subject, fact.predicate, fact.obj)
                if fact_key not in used_fact_keys or fact_key in recalled_keys:
                    continue
                evidence = Evidence(
                    source=fact.source or "semantic_memory",
                    content={
                        "kind": "semantic_fact",
                        "subject": fact.subject,
                        "predicate": fact.predicate,
                        "obj": fact.obj,
                        "source": fact.source,
                        "confidence": float(fact.confidence),
                    },
                    confidence=float(fact.confidence),
                )
                self.workspace.broadcast_evidence(evidence)
                supporting_records.append(
                    {
                        "subject": fact.subject,
                        "predicate": fact.predicate,
                        "obj": fact.obj,
                        "source": fact.source,
                        "confidence": float(fact.confidence),
                        "evidence_id": evidence.evidence_id,
                    }
                )

            if supporting_records:
                for fact in supporting_records:
                    evidence_id = fact.get("evidence_id")
                    if evidence_id and evidence_id not in used_evidence_ids:
                        used_evidence_ids.append(evidence_id)
                confidence = min(
                    confidence,
                    *(float(fact.get("confidence", confidence)) for fact in supporting_records),
                )
                grounding_source = "reason_derived_evidence"
            elif selected_answer:
                # A specialized answer with no consumed semantic facts must
                # not advertise more certainty than conflicting ranked data.
                confidence = min(confidence, float(selected_answer.get("confidence", confidence)))

        # Any remaining query fallback with ranked evidence is conservatively
        # bounded by that evidence rather than a handler's hard-coded score.
        if plan == "answer_query" and selected_answer and grounding_source == "direct_knowledge":
            confidence = min(confidence, float(selected_answer.get("confidence", confidence)))

        if confidence <= 0.35 and not used_evidence_ids and grounding_source == "direct_knowledge":
            grounding_source = "fallback"

        curiosity_question = self._curiosity_prompt(self.state.active_concepts)
        if curiosity_question:
            response = (response + " " + curiosity_question) if response else curiosity_question

        return CycleResult(
            phase=CognitivePhase.ACT,
            data={
                "response": response,
                "confidence": confidence,
                "plan": plan,
                "grounding_source": grounding_source,
                "used_evidence_ids": used_evidence_ids,
                "association_count": len(associate_data.get("activation_map", {})),
            },
            success=confidence > 0.5,
        )

    def _run_learning_action(self, handler: Any, parse_result: ParseResult) -> tuple:
        """Execute a learning-shaped ACT handler without retaining assessment writes."""
        if not self._assessment_mode:
            return handler(parse_result)
        snapshots = {
            "name": self.name,
            "user_name": self.user_name,
            "semantic_memory": copy.deepcopy(self.semantic_memory),
            "concept_graph": copy.deepcopy(self.concept_graph),
            "episodic_memory": copy.deepcopy(self.episodic_memory),
            "procedural_memory": copy.deepcopy(self.procedural_memory),
            "learning_quarantine": copy.deepcopy(self._learning_quarantine),
        }
        try:
            return handler(parse_result)
        finally:
            self.name = snapshots["name"]
            self.user_name = snapshots["user_name"]
            self.semantic_memory = snapshots["semantic_memory"]
            self.concept_graph = snapshots["concept_graph"]
            self.episodic_memory = snapshots["episodic_memory"]
            self.procedural_memory = snapshots["procedural_memory"]
            self._learning_quarantine = snapshots["learning_quarantine"]
            self.procedural_memory.__dict__.pop("store", None)

    def _act_greeting(self, parse_result: ParseResult) -> tuple:
        """Phase 24: friendly greeting with a varied personality voice.

        Uses the bilingual greeting pool so repeated greetings do not
        echo the same sentence, while keeping MISTY's stable identity
        (Smart Artificial Brain by Pixline Incorporate).
        """
        name_part = f", {self.user_name}" if self.user_name else ""
        text = parse_result.raw_text or ""
        response = self.variator.pick("greeting", text, placeholders={"name": name_part})
        if not response:
            is_bengali = any("\u0980" <= char <= "\u09ff" for char in text)
            if is_bengali:
                response = (
                    f"হ্যালো{name_part}! আমি Misty - Smart Artificial Brain, "
                    f"Pixline Incorporate-এর তৈরি। কীভাবে সাহায্য করতে পারি?"
                )
            else:
                response = (
                    f"Hello{name_part}! I am Misty - a Smart Artificial Brain built "
                    f"by Pixline Incorporate. How may I help?"
                )
        return response, 0.9

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

        # Phase 28: pronoun subjects in identity questions ("তুমি", "you"...)
        # refer to Misty herself — normalize BEFORE anything else reads the
        # subject, so both "Who created you?" and "তুমি কে তৈরি করেছ?" work.
        if parse_result.intent == IntentType.QUERY_WHO:
            subject = parse_result.query.get("subject", "")
            if subject in self._SELF_SUBJECTS:
                parse_result.query["subject"] = "Misty"
        # Identity shortcuts: if asked about MISTY herself (explicit name,
        # or a who-query with a self-subject), answer from self-knowledge
        # before the generic graph/semantic lookup so the answer always
        # reflects the trained identity.
        _query_subject = parse_result.query.get("subject", "")
        if target_name.lower() == "misty" or (
            parse_result.intent == IntentType.QUERY_WHO
            and _query_subject.lower() == "misty"
            and relation == "creator_of"
        ):
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
        # Phase 24: pick a varied personality template per language so
        # consecutive unknown inputs do not echo the same canned phrase.
        response = self.variator.pick("unknown", raw)
        if not response:
            is_bengali = any("\u0980" <= char <= "\u09ff" for char in raw)
            response = (
                (
                    "আমি আপনার কথাটি বুঝতে চেষ্টা করেছি, কিন্তু এই বাক্যের intent এখনো "
                    'নির্ভুলভাবে parse করতে পারিনি। আপনি চাইলে "মনে রাখো: ...", "X হলো Y", '
                    '"আমার নাম X", অথবা নির্দিষ্ট math/physics format ব্যবহার করে শেখাতে পারেন। '
                    "আমি এই অজানা input-টি learning opportunity হিসেবে working memory-তে রেখেছি।"
                )
                if is_bengali
                else (
                    "I heard you, but I could not resolve the intent yet. You can teach me with "
                    '"remember that ...", "X is Y", or ask a supported mathematics or physics question. '
                    "I have retained this unknown input as a learning opportunity."
                )
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
        is_bn = any("\u0980" <= ch <= "\u09ff" for ch in parse_result.raw_text or "")
        if relation in ("creator_of", "made_by"):
            if is_bn:
                return (
                    "আমি Misty - Smart Artificial Brain। আমাকে তৈরি করেছে "
                    "Pixline Incorporate, যার Founder হলেন Salauddin Mir (Netvai নামে পরিচিত)। "
                    "আমি হলো ভারতের প্রথম Smart AI Brain যেটি কোনো LLM-এর উপর নির্ভরশীল নয়।"
                ), 0.95
            return (
                "I am Misty - a Smart Artificial Brain created by Pixline Incorporate, "
                "whose Founder is Salauddin Mir (known as Netvai). I am India's first "
                "Smart AI Brain that does not depend on any LLM."
            ), 0.95
        # Default: full self-introduction
        if is_bn:
            return (
                "আমি Misty - Smart Artificial Brain। আমি Pixline Incorporate-এর তৈরি "
                "একটি কৃত্রিম কগনিটিভ সিস্টেম — ভারতের প্রথম Smart AI Brain যেটি "
                "কোনো LLM dependency ছাড়াই কাজ করে। আমার তৈরিকারী হলেন "
                "Salauddin Mir, যিনি Netvai নামে পরিচিত। আমি স্পাইকিং নিউরাল নেটওয়ার্ক "
                "ও নলেজ গ্রাফ ব্যবহার করি এবং বাংলা ও ইংরেজি দুই ভাষায় কথা বলতে পারি।"
            ), 0.95
        return (
            "I am Misty - a Smart Artificial Brain. I am an artificial cognitive "
            "system built by Pixline Incorporate — India's first Smart AI Brain that "
            "works without any LLM dependency. My creator is Salauddin Mir, who is "
            "known as Netvai. I use spiking neural networks and a knowledge graph, "
            "and I can converse in both Bengali and English."
        ), 0.95

    def _definition_or_concept(self, name: str):
        """Phase 29: lookup predicates that carry definition knowledge.

        Curriculum packages (e.g. the mathematics curriculum) store
        explanations under predicates such as ``definition``, ``সংজ্ঞা``,
        ``formula`` and ``সূত্র``, not just ``is_a``. This helper bundles
        the lookup so definition-style facts participate in head-noun
        resolution and existence checks, preventing the generic
        "I have not learned X yet" fallback for trained concepts.
        """
        for _pred in (
            "is_a",
            "definition",
            # Phase 29 curriculum definition predicates:
            "সংজ্ঞা",
            "\u09b8\u09c2\u09a4\u09b0",
            "formula",
            # Phase 28 topic-inheritance relational predicates:
            "color",
            "use",
            "capability",
            "why_reason",
            "day_color_reason",
        ):
            _found = self.semantic_memory.query(subject=name, predicate=_pred)
            if _found:
                return _found
        return self.concept_graph.get_concept_by_name(name)

    def _act_query_what(self, parse_result: ParseResult, recall_data: Dict[str, Any]) -> tuple:
        """Handle definition (is_a / means) queries like "মিস্টি মানে কী?".
        Looks up is_a facts in the knowledge graph and semantic memory,
        and falls back to a humble "still learning" answer that mentions
        the asked-about entity so the user can teach it.
        """
        self._last_query_what_fact_keys: List[tuple[str, str, str]] = []
        target_name = parse_result.query.get("target", "")
        relation = parse_result.query.get("relation", "")
        # Phase 28: relational follow-ups ("এর কাজ কি?", "What can that
        # do?", "কারণ কি?", "How does that work?") inherit the previous
        # topic instead of dying on an empty target.
        if not target_name or relation in {"use", "capability", "why", "how"}:
            # Phase 28: prefer the anchored conversation topic (set from the
            # previous query target / taught subject) over raw salient-word
            # scraping, so "Why?" after "What is the color of the sky?"
            # inherits the topic anchor ("color of the sky" -> "sky")
            # instead of the stray salient word "color".
            inherited = self.dialogue_context.topic
            if not inherited:
                inherited = self._prior_topic(
                    exclude=_current_token_set(parse_result.raw_text) | self._INTERROGATIVE_TOKENS,
                    parse_result=parse_result,
                )
            if inherited:
                target_name = inherited
                parse_result.query["target"] = inherited
        if not target_name:
            return self._act_unknown(parse_result)
        # Phase 28: compound targets like "color of the sky" or the
        # Bengali possessive "আকাশের রঙ" reduce to the entity the
        # knowledge base actually stores ("sky" / "আকাশ") instead of the
        # attribute word ("color" / "রঙ") that no facts exist for.
        if " " in target_name:
            _stop = (
                self._SALIENT_STOP_TOKENS
                | self._INTERROGATIVE_TOKENS
                | {
                    "of",
                    "the",
                    "a",
                    "an",
                    "in",
                    "on",
                    "at",
                    "with",
                    "from",
                }
            )
            # English: head noun is the LAST content word ("color of the
            # sky" -> "sky"). Bengali possessives put the entity FIRST
            # ("আকাশের রঙ" -> "আকাশ"). Pick whichever candidate carries
            # stored facts; fall back to the grammar-based head noun.
            _is_bn_target = any("\u0980" <= ch <= "\u09ff" for ch in target_name)
            _word_order = target_name.split() if _is_bn_target else list(reversed(target_name.split()))
            _head = None
            # Phase 32: the FULL compound target (e.g. "বাংলাদেশের রাজধনী"
            # / "capital of india") may itself be a stored subject with
            # direct definition facts — prefer that over reducing the
            # phrase to a single word, so "What is Bangladesh's capital?"
            # resolves to the capital itself (Dhaka) rather than the
            # country's own definition.
            if self._definition_or_concept(target_name):
                _head = target_name
            else:
                _orig = target_name
                for _w in _word_order:
                    if _w.lower() in _stop:
                        continue
                    _kb = self._definition_or_concept(_w)
                    if _kb:
                        _head = _w
                        break
                if _head is None:
                    _head = next(
                        (w for w in _word_order if w.lower() not in _stop),
                        _orig,
                    )
            target_name = _head
            parse_result.query["target"] = _head

        # Phase 28: English plural stripping so "robots" resolves to
        # the singular knowledge-graph entry.
        def _singular(name: str) -> str:
            if name and name.isascii() and name.endswith("s") and len(name) > 3:
                if name.endswith("ies") and len(name) > 4:
                    return name[:-3] + "y"
                if name.endswith("es") and len(name) > 4:
                    return name[:-2]
                return name[:-1]
            return name

        # Phase 28: Bengali inflection normalization for single-word
        # targets — "আকাশের" resolves to the base "আকাশ" that the
        # knowledge base actually stores (genitive/possessive suffixes).
        if not target_name.isascii() and " " not in target_name:
            _base = self._normalize_bengali_word(target_name)
            if _base != target_name:
                _bhas = self._definition_or_concept(_base)
                if _bhas:
                    target_name = _base
                    parse_result.query["target"] = _base
        if target_name.isascii():
            _sing = _singular(target_name)
            _has = self._definition_or_concept(target_name)
            if not _has and _sing != target_name:
                _shas = self._definition_or_concept(_sing)
                if _shas:
                    target_name = _sing
                    parse_result.query["target"] = _sing
        # Phase 28: fall back to the parser's English is_a extraction
        # ("X is a Y") before giving up, so fresh teaching turns feed
        # immediate answers.
        _en = self.nlu._en_is_a_pattern.search(parse_result.raw_text or "")
        if _en and _en.group(1).lower() == target_name.lower():
            return (f"{target_name} is {_en.group(2).strip()}. I just learned that from what you told me."), 0.7

        # Phase 28: relational answers (use / capability / why / how) are
        # composed from stored facts (is_a, use, color, reason) instead of
        # the generic 'not learned' fallback, so the reply always carries
        # real knowledge about the anchored topic.
        if relation in {"use", "capability", "how", "why"}:
            facts = (
                self.semantic_memory.query(subject=target_name, predicate="is_a")
                + self.semantic_memory.query(subject=target_name, predicate="use")
                + self.semantic_memory.query(subject=target_name, predicate="color")
                + self.semantic_memory.query(subject=target_name, predicate="day_color_reason")
                + self.semantic_memory.query(subject=target_name, predicate="why_reason")
            )
            if facts:
                self._last_query_what_fact_keys = [(fact.subject, fact.predicate, fact.obj) for fact in facts[:3]]
                is_bn = any("\u0980" <= ch <= "\u09ff" for ch in parse_result.raw_text or "")
                detail_parts = [f.obj for f in facts[:3]]
                detail = ", ".join(detail_parts)
                # The reason fact (আকাশের day_color_reason) explains WHY;
                # use/capability facts explain WHAT it does.
                if relation == "why":
                    if is_bn:
                        return (
                            f"আমার সংরক্ষিত তথ্য অনুসারে {target_name} সম্পর্কে আমার জানা: "
                            f"{detail}। কারণটি এই তথ্যের ভিত্তিতেই ডেরাইভ করা হয়েছে।"
                        ), 0.75
                    return (
                        f"From my stored knowledge about {target_name}: {detail}. "
                        f"That is the reason I can derive from my facts."
                    ), 0.75
                if is_bn:
                    return (
                        f"আমার সংরক্ষিত তথ্য অনুসারে {target_name} হলো {detail}। এই তথ্য থেকেই এর কাজ ও ক্ষমতা নির্ণয় করা হয়।"
                    ), 0.75
                return (
                    f"From my stored knowledge, {target_name} is {detail}. "
                    f"Its function and capability follow from that knowledge."
                ), 0.75

        facts = (
            self.semantic_memory.query(subject=target_name, predicate="is_a")
            + self.semantic_memory.query(subject=target_name, predicate="definition")
            + self.semantic_memory.query(subject=target_name, predicate="সংজ্ঞা")
            + self.semantic_memory.query(subject=target_name, predicate="সূত্র")
            + self.semantic_memory.query(subject=target_name, predicate="formula")
        )
        if facts:
            self._last_query_what_fact_keys = [(fact.subject, fact.predicate, fact.obj) for fact in facts[:3]]
            is_bn = any("\u0980" <= ch <= "\u09ff" for ch in parse_result.raw_text or "")
            definitions = [fact.obj for fact in facts]
            if is_bn:
                return f"{target_name} হলো {', '.join(definitions[:3])}।", 0.9
            return (f"From my stored knowledge, {target_name} is {', '.join(definitions[:3])}."), 0.9

        # Phase 29: subject alias expansion — curriculum packages store
        # facts under canonical names (e.g. "Quadratic Equation") that do
        # not match the parsed target literally (e.g. "quadratic formula",
        # "Pythagorean theorem"). When the exact lookup finds nothing,
        # scan definition-style facts whose subject contains a content
        # word from the target so trained concepts still surface instead
        # of the generic "not learned" fallback.
        if not facts and len(target_name) > 3:
            _alias_facts: list = []
            _alias_seen: set = set()
            _target_words = set(re.findall(r"[A-Za-z\u0980-\u09ff]+", target_name.lower()))
            _target_words -= {w for w in _target_words if w in self._SALIENT_STOP_TOKENS or len(w) <= 2}
            for _word in _target_words:
                for _subject in self.semantic_memory.query(subject=_word):
                    if _subject.subject in _alias_seen:
                        continue
                    _matches = _target_words & set(
                        w
                        for w in re.findall(r"[A-Za-z\u0980-\u09ff]+", _subject.subject.lower())
                        if len(w) > 2 and w not in self._SALIENT_STOP_TOKENS
                    )
                    if _matches and _subject.predicate in (
                        "is_a",
                        "definition",
                        "সংজ্ঞা",
                        "\u09b8\u09c2\u09a4\u09b0",
                        "formula",
                    ):
                        _alias_seen.add(_subject.subject)
                        _alias_facts.append(_subject)
            if _alias_facts:
                facts = _alias_facts
        if facts:
            self._last_query_what_fact_keys = [(fact.subject, fact.predicate, fact.obj) for fact in facts[:3]]
            is_bn = any("\u0980" <= ch <= "\u09ff" for ch in parse_result.raw_text or "")
            definitions = [fact.obj for fact in facts]
            if is_bn:
                return f"{target_name} হলো {', '.join(definitions[:3])}।", 0.9
            return (f"From my stored knowledge, {target_name} is {', '.join(definitions[:3])}."), 0.9
        concept = self.concept_graph.get_concept_by_name(target_name)
        if concept and concept.concept_type and concept.concept_type != "Entity":
            is_bn = any("\u0980" <= ch <= "\u09ff" for ch in parse_result.raw_text or "")
            if is_bn:
                return f"{target_name} হলো {concept.concept_type}।", 0.8
            return f"{target_name} is a {concept.concept_type}.", 0.8

        recalled = recall_data.get("semantic_facts", [])
        for fact in recalled:
            if fact.get("subject") == target_name and fact.get("predicate") == "is_a":
                self._last_query_what_fact_keys = [
                    (str(fact.get("subject", "")), str(fact.get("predicate", "")), str(fact.get("obj", "")))
                ]
                return f"{target_name} হলো {fact.get('obj', '')}।", 0.85

        # Phase 18: derive an answer from commonsense / stored knowledge
        # before falling back to "আমি এখনো X সম্পর্কে জানি না".
        synthesis = self.inference_synthesizer.synthesize(parse_result.raw_text or target_name, self)
        if synthesis is not None:
            self.state.add_thought("inference_synthesis", synthesis.steps)
            is_bn = any("\u0980" <= ch <= "\u09ff" for ch in parse_result.raw_text or "")
            if is_bn:
                return (
                    f"{target_name} সম্পর্কে আমি এইতুক জানি: {synthesis.answer}",
                    synthesis.confidence,
                )
            return (
                f"This much I know about {target_name}: {synthesis.answer}",
                synthesis.confidence,
            )

        self.emotion.update_from_outcome(success=False)
        # Phase 24: varied humble fallback so repeated "X কী?" queries
        # do not echo the same "আমি এখনো X সম্পর্কে জানি না" sentence.
        fallback = self.variator.pick("query_what_unknown", target_name, placeholders={"subject": target_name})
        if not fallback:
            fallback = f'আমি এখনো {target_name} সম্পর্কে জানি না। আপনি বলতে পারেন: "{target_name} হলো X" — তাহলে আমি মনে রাখব।'
        return fallback, 0.3

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
        synthesis = self.inference_synthesizer.synthesize(parse_result.raw_text or "", self)
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
        # Phase 24: varied acknowledgment so repeated statements do not
        # echo the same generic robot reply.
        ack = self.variator.pick("statement", parse_result.raw_text or "")
        if not ack:
            ack = (
                f"আমি আপনার কথাটি শুনলাম{context_part}, কিন্তু এখনো "
                "এটি সম্পূর্ণ বুঝতে শিখিনি। আপনি চাইলে শেখাতে পারেন: "
                '"মনে রাখো ..." বা "X হলো Y" ফরম্যাটে।'
            )
        return ack, 0.5

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
            # Phase 28: English teaching turns ("Remember that a drone is a
            # flying robot") are parsed with the same is_a logic so the
            # taught subject becomes the follow-up topic.
            if not facts:
                for pattern in self.nlu._en_is_a_pattern.finditer(taught):
                    subject, obj = pattern.group(1).strip(), pattern.group(2).strip()
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
                # Phase 28: the taught subject becomes the dialogue topic so
                # capability/use follow-ups ("What can that do?") anchor to
                # what was just taught, not to generic sentence words.
                self.dialogue_context.topic = subject
                # Phase 24: varied learning acknowledgment.
                ack = self.variator.pick("teach", raw, placeholders={"fact": f"{subject} হলো {obj}"})
                if not ack:
                    ack = f"মনে রাখা হয়েছে: {subject} হলো {obj}।"
                return ack, 0.9

        self.episodic_memory.store(
            content={"type": "taught_statement", "text": raw},
            emotional_valence=0.6,
            importance=0.7,
        )
        # Phase 24: varied acknowledgment when no structured fact was
        # extracted from the taught sentence.
        ack = self.variator.pick("teach", raw, placeholders={"fact": raw})
        if not ack:
            ack = f"আমি মনে রাখলাম: {raw}"
        return ack, 0.7

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
            # Phase 24: varied correction acknowledgment.
            ack = self.variator.pick(
                "correction",
                parse_result.raw_text or "",
                placeholders={"target": correction_target},
            )
            if not ack:
                ack = f"ধন্যবাদ সংশোধনের জন্য। আপনি ঠিক বলছেন — {correction_target}। আমি এটা মনে রাখলাম।"
            return ack, 0.8
        # Phase 24: varied clarification request.
        clarify = self.variator.pick("correction", parse_result.raw_text or "")
        if not clarify:
            clarify = "আমি বুঝতে পেরেছি আপনি সংশোধন করছেন, কিন্তু কী সংশোধন করতে চাইছেন সেটা স্পষ্ট করে বলুন।"
        return clarify, 0.5

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
        # Discourse tokens, interrogatives and reply-filler words are never
        # valid topics — they must not seed the expansion answer.
        salient = [
            e
            for e in salient
            if e not in self._DISCOURSE_TOKENS
            and e.lower()
            not in {
                "what",
                "who",
                "how",
                "why",
                "great",
                "question",
                "topic",
                "hello",
                "hi",
                "okay",
                "alright",
                "fine",
                "thanks",
            }
        ]
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
            # Phase 24: varied continuation phrasing around the topic detail.
            variant = self.variator.pick(
                "continuation",
                parse_result.raw_text or "",
                placeholders={"topic": topic, "detail": detail},
            )
            if not variant:
                variant = (
                    f"আমি {topic} নিয়ে বলছি — {topic} হলো {detail}। এর বেশি জানতে চাইলে বলুন 'আমি {topic}-এর তথ্য দাও'।"
                )
            return variant, 0.8

        topic_concept = self.concept_graph.get_concept_by_name(topic)
        related = []
        if topic_concept:
            related = self.concept_graph.find_related(topic_concept.concept_id, direction="outgoing")
        if related:
            names = [concept.name for concept in related[:3]]
            return f"{topic} নিয়ে আমার জ্ঞান: সম্পর্কিত ধারণা — {', '.join(names)}।", 0.7

        # Phase 23: try knowledge-inference synthesis on the topic before
        # admitting ignorance, so follow-ups can still extract reasoning.
        synthesis = self.inference_synthesizer.synthesize(f"{topic} কী?", self)
        if synthesis is not None:
            self.state.add_thought("inference_synthesis", synthesis.steps)
            detail = synthesis.answer[3:].strip() if synthesis.answer.startswith("আমি ") else synthesis.answer
            return (
                f"{topic} সম্পর্কে আমি এতটুকু জানি: {detail}",
                synthesis.confidence,
            )
        # Phase 24: varied honest-fallback phrasing instead of a fixed
        # "{topic} নিয়ে আমি এখনো বেশি কিছু জানি না..." sentence.
        honest = self.variator.pick(
            "continuation",
            parse_result.raw_text or "",
            placeholders={"topic": topic, "detail": ""},
        )
        if not honest:
            honest = f"{topic} নিয়ে আমি এখনো বেশি কিছু জানি না। আপনি কি আমাকে আরো শেখাবেন?"
        return honest, 0.5

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
        if self._assessment_mode:
            return CycleResult(
                phase=CognitivePhase.LEARN,
                data={"assessment_mode": True, "learning_skipped": True},
                success=True,
            )

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
        if self._assessment_mode:
            return CycleResult(
                phase=CognitivePhase.CONSOLIDATE,
                data={"assessment_mode": True, "consolidation_skipped": True},
                success=True,
            )

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
            # Phase 33: autonomous self-assessment — knowledge gaps from
            # the last GapAssessor evaluation, visible via /api/brain/state.
            "knowledge_gaps": self.gap_assessor.gap_dicts(),
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
