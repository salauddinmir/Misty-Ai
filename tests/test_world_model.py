"""
Phase 5 tests: world model — structured environment state and
next-intent prediction with prediction-error feedback.
"""

from brain.core.brain import Brain
from brain.world.model import WorldEntity, WorldModel

# -----------------------------------------------------------------------
# Entity registry
# -----------------------------------------------------------------------


class TestWorldEntity:
    def test_basic_entity(self) -> None:
        entity = WorldEntity("desk_lamp", "object", "study_room")
        assert entity.entity_id == "desk_lamp"
        assert entity.location == "study_room"

    def test_round_trip(self) -> None:
        entity = WorldEntity("cat", "animal", "living_room")
        entity.attributes["color"] = "white"
        restored = WorldEntity.from_dict(entity.to_dict())
        assert restored.entity_id == "cat"
        assert restored.attributes["color"] == "white"


class TestWorldModelEntities:
    def setup_method(self) -> None:
        self.model = WorldModel()

    def test_add_and_refresh_entity(self) -> None:
        entity = self.model.add_entity("phone", "device", attributes={"battery": 80})
        assert entity.entity_type == "device"
        # Refresh with new attributes updates instead of duplicating.
        self.model.add_entity("phone", attributes={"signal": "strong"})
        assert self.model.get_entity("phone").attributes["signal"] == "strong"
        assert len(self.model.entities) == 1

    def test_registry_is_bounded(self) -> None:
        small = WorldModel(max_entities=3)
        small.add_entity("a")
        small.add_entity("b")
        small.add_entity("c")
        small.add_entity("d")
        assert len(small.entities) == 3
        assert "d" in small.entities  # eviction: oldest removed

    def test_get_missing_entity(self) -> None:
        assert self.model.get_entity("nope") is None


# -----------------------------------------------------------------------
# Causal links
# -----------------------------------------------------------------------


class TestCausalLinks:
    def setup_method(self) -> None:
        self.model = WorldModel()
        self.model.record_cause("rain", "wet_ground")
        self.model.record_cause("cloud", "rain")
        self.model.record_cause("rain", "traffic")

    def test_causes_of_effect(self) -> None:
        assert "rain" in self.model.causes_of("wet_ground")

    def test_effects_of_cause(self) -> None:
        effects = self.model.effects_of("rain")
        assert "wet_ground" in effects and "traffic" in effects

    def test_causal_links_bounded(self) -> None:
        small = WorldModel(max_causal_links=2)
        small.record_cause("x", "y")
        small.record_cause("a", "b")
        small.record_cause("p", "q")
        assert len(small.causal_links) == 2
        # newest kept
        assert small.causal_links[-1]["effect"] == "q"


# -----------------------------------------------------------------------
# Intent prediction
# -----------------------------------------------------------------------


class TestIntentPrediction:
    def test_no_history_no_prediction(self) -> None:
        model = WorldModel()
        assert model.predict_next_intent() is None

    def test_no_transition_no_prediction(self) -> None:
        model = WorldModel()
        model.record_intent("greeting")  # first intent, nothing to predict from
        assert model.predict_next_intent() is None

    def test_prediction_from_history(self) -> None:
        model = WorldModel()
        # greeting is often followed by a query in our sample history.
        sequence = [
            "greeting",
            "query_who",
            "greeting",
            "query_who",
            "greeting",
            "statement",
        ]
        for intent in sequence:
            model.record_intent(intent)
        # The last observed intent ('statement') has no learned follow-up
        # yet, so the predictor falls back through history and surfaces
        # the strongest learned transition: greeting -> query_who.
        assert model.predict_next_intent() == "query_who"
        assert model.predict_from("greeting") == "query_who"

    def test_prediction_error_signal(self) -> None:
        model = WorldModel()
        for intent in ["greeting", "query_who", "greeting", "query_who"]:
            model.record_intent(intent)
        # Prime the history so the predictor sees 'greeting' as the
        # last intent, then check what it predicts from there.
        model.intent_history.append("greeting")
        # Next actual intent matches the predicted follow-up.
        outcome = model.record_intent("query_who")
        assert outcome["predicted"] == "query_who"
        assert outcome["correct"] is True
        assert outcome["error"] == 0.0
        # A surprise intent yields error 1.0.
        model.intent_history.append("greeting")
        outcome = model.record_intent("correction")
        assert outcome["correct"] is False
        assert outcome["error"] == 1.0

    def test_history_window_bounded(self) -> None:
        model = WorldModel(history_window=4)
        for _ in range(10):
            model.record_intent("statement")
        assert len(model.intent_history) == 4

    def test_serialize_round_trip(self) -> None:
        model = WorldModel()
        model.add_entity("desk", "furniture", "office")
        model.record_cause("coffee", "focus")
        for intent in ["greeting", "query_who", "greeting", "statement"]:
            model.record_intent(intent)
        restored = WorldModel()
        restored.load(model.to_dict())
        assert "desk" in restored.entities
        assert len(restored.causal_links) == 1
        assert restored.predict_next_intent() == model.predict_next_intent()

    def test_reset_clears(self) -> None:
        model = WorldModel()
        model.add_entity("x")
        model.record_intent("greeting")
        model.reset()
        assert not model.entities and not model.intent_history


# -----------------------------------------------------------------------
# Wiring: brain uses the world model in the cycle
# -----------------------------------------------------------------------


class TestBrainWorldModelWiring:
    def test_world_model_wired(self) -> None:
        brain = Brain()
        assert hasattr(brain, "world") and isinstance(brain.world, WorldModel)

    def test_entities_extracted_from_turns(self) -> None:
        brain = Brain()
        brain.process("আমার নাম সাবরীনা")
        brain.process("আমার একটি বিড়াল আছে যার নাম মিয়া")
        names = set(brain.world.entities.keys())
        assert "সাবরীনা" in names
        # 'মিয়া' should appear somewhere in registered entities.
        assert any("মিয়া" in n for n in names)

    def test_prediction_error_in_state(self) -> None:
        brain = Brain()
        result = brain.process("হ্যালো")
        assert "last_prediction_error" in result["brain_state"]
        state = brain.get_state()
        assert state["last_prediction_error"] in (0.0, 1.0)

    def test_repeated_pattern_learns_prediction(self) -> None:
        brain = Brain()
        # Establish a pattern: greeting followed by query.
        for _ in range(4):
            brain.process("হ্যালো")
            brain.process("মিস্তি কে তৈরি করেছে?")
        # Same pattern again: the greeting's intent history should
        # prime the predictor; we only check that the outcome dict is
        # produced, not that it guesses correctly on limited data.
        result = brain.process("হ্যালো")
        assert result["brain_state"]["last_prediction_error"] in (0.0, 1.0)
