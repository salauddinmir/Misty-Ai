"""Phase 30 tests: full bilingual physics curriculum.

Covers:
- package validation and registry registration
- the deterministic PhysicsEngine solving every PHYSICS_TEST case
- physics-engine topic support added in Phase 30 (Bengali digit input,
  free-fall distance, series/parallel resistance, Ohm's law current,
  electrical/mechanical power, wave speed)
- the brain answering curriculum concept questions in both languages
- regression safety: engine answers stay deterministic across calls
"""

from __future__ import annotations

import re

import pytest

from brain.core.brain import Brain
from brain.knowledge.registry import PackageRegistry, validate_package
from brain.knowledge.training_physics import (
    PHYSICS_CONCEPTS,
    PHYSICS_EXAMPLES,
    PHYSICS_FACTS,
    PHYSICS_FORMULAS,
    PHYSICS_RELATIONS,
    PHYSICS_RULES,
    PHYSICS_SYNONYMS,
    PHYSICS_TESTS,
    physics_curriculum_package,
    register_physics_curriculum,
)
from brain.physics_engine import PHYSICS_ENGINE

_BN_TO_EN = str.maketrans("০১২৩৪৫৬৭৮৯", "0123456789")

# Phase 30 bilingual probe phrases — kept as module constants to stay
# within the 120-character line limit.
_BN_FALL_3 = (
    "\u09e9 \u09b8\u09c7\u0995\u09c7\u09a8\u09cd\u09a1\u09c7 \u09ae\u09c1\u0995\u09cd\u09a4\u09aa\u09a4\u09a8\u09c7 "
    "\u09aa\u09a1\u09bc\u09be \u09a6\u09c2\u09b0\u09a4\u09cd\u09a4\u09cd\u09ac"
)
_BN_OHM_12_4 = (
    "\u09e7\u09e8 \u09ad\u09cb\u09b2\u09cd\u099f \u0993 \u09ea \u0993\u09b9\u09ae\u09c7 "
    "\u09a4\u09a1\u09bc\u09bf\u09a4\u09cd \u09aa\u09cd\u09b0\u09ac\u09be\u09b9"
)
_BN_SERIES_6_3 = (
    "\u09ec \u0993\u09b9\u09ae \u0993 \u09e9 \u0993\u09b9\u09ae "
    "\u09b8\u09ae\u09ac\u09be\u09af\u09bc\u09c7 \u09ae\u09cb\u099f \u09b0\u09cb\u09a7"
)
_BN_PARALLEL_6_3 = (
    "\u09ec \u0993\u09b9\u09ae \u0993 \u09e9 \u0993\u09b9\u09ae "
    "\u09b8\u09ae\u09be\u09a8\u09cd\u09a4\u09b0\u09be\u09b2\u09c7 \u09ae\u09cb\u099f \u09b0\u09cb\u09a7"
)
_BN_WAVE_50_4 = (
    "\u09eb\u09e6 \u09b9\u09be\u09b0\u09cd\u099c \u0995\u09ae\u09cd\u09aa\u09be\u0999\u09cd\u0995 "
    "\u0993 \u09ea \u09ae\u09bf \u09a4\u09b0\u0999\u09cd\u0997\u09c7\u09b0 \u09ac\u09c7\u0997"
)


def _unify_digits(text: str) -> str:
    return text.translate(_BN_TO_EN)


def _new_brain() -> Brain:
    return Brain(use_neural_sim=False)


def _engine_answer(text: str) -> str:
    result = PHYSICS_ENGINE.solve(text)
    assert result is not None, f"engine returned None for {text!r}"
    assert result.exact not in (None, "unsupported", "missing_values", "undefined"), (
        f"engine error for {text!r}: {result.answer}"
    )
    return str(result.exact)


# ---------------------------------------------------------------------------
# Package validation and registry
# ---------------------------------------------------------------------------


class TestPhysicsPackage:
    def test_package_validates(self):
        package = physics_curriculum_package()
        assert validate_package(package) is package

    def test_package_identity(self):
        package = physics_curriculum_package()
        assert package.package_id == "misty-physics-phase30"
        assert package.department == "physics"
        assert {"bn", "en"}.issubset(set(package.languages))
        source = package.source
        assert str(getattr(source, "content_hash", "")).startswith("sha256:")

    def test_package_registers(self):
        registry = PackageRegistry()
        registry.register(physics_curriculum_package())
        registered = registry.get("misty-physics-phase30")
        assert registered is not None
        assert registered.version == "1.0.0"
        departments = {package.department for package in registry.list()}
        assert "physics" in departments

    def test_curriculum_records_non_empty(self):
        assert len(PHYSICS_CONCEPTS) >= 20
        assert len(PHYSICS_RELATIONS) >= 10
        assert len(PHYSICS_FACTS) >= 30
        assert len(PHYSICS_FORMULAS) >= 5
        assert len(PHYSICS_RULES) >= 5
        assert len(PHYSICS_EXAMPLES) >= 5
        assert len(PHYSICS_TESTS) >= 10
        assert len(PHYSICS_SYNONYMS) >= 10

    def test_bilingual_pairs(self):
        english = {record["name"] for record in PHYSICS_CONCEPTS if record["lang"] == "en"}
        bengali = {record["name"] for record in PHYSICS_CONCEPTS if record["lang"] == "bn"}
        assert len(english) >= 15
        assert len(bengali) >= 15

    def test_topics_covered(self):
        topics = {record.get("topic") for record in PHYSICS_FACTS if record.get("topic")}
        for topic in ("kinematics", "forces", "energy", "waves_sound", "electricity", "optics"):
            assert topic in topics, f"missing topic {topic}"

    def test_register_into_brain(self):
        # Brain.__init__ already loads the Phase 30 physics curriculum,
        # so a fresh brain carries the facts; re-registering is idempotent and
        # returns 0 new records, which is expected (no duplicates).
        brain = _new_brain()
        fresh_registered = register_physics_curriculum(brain)
        assert fresh_registered == 0
        # Concepts entered the graph.
        assert brain.concept_graph.get_concept_by_name("Newton's Second Law") is not None
        _ohm_bn = "\u0993\u09b9\u09ae\u09c7\u09b0 \u09b8\u09c2\u09a4\u09cd\u09b0"
        assert brain.concept_graph.get_concept_by_name(_ohm_bn) is not None
        # Facts entered semantic memory.
        assert brain.semantic_memory.query(subject="Force", predicate="definition")
        assert brain.semantic_memory.query(subject="বল", predicate="সংজ্ঞা")


# ---------------------------------------------------------------------------
# Engine: every PHYSICS_TEST case must compute deterministically
# ---------------------------------------------------------------------------


class TestPhysicsEnginePhysicsTests:
    @pytest.mark.parametrize("case", PHYSICS_TESTS, ids=[case["id"] for case in PHYSICS_TESTS])
    def test_physics_test_case(self, case: dict):
        result = PHYSICS_ENGINE.solve(case["input"])
        assert result is not None, f"engine returned None for {case['input']!r}"
        assert result.exact not in (None, "unsupported", "missing_values", "undefined"), (
            f"engine error for {case['input']!r}: {result.answer}"
        )
        expected = case["expected_output"]
        # Normalized numeric tolerance: the engine formats answers like
        # "I = 3 A" or "R = 9 ohm"; the expected numeric tokens (with minor
        # decimal rounding differences) must appear.
        actual = _unify_digits(str(result.exact))
        expected_norm = _unify_digits(str(expected))
        if expected_norm in actual:
            return
        expected_numbers = re.findall(r"\d+(?:\.\d+)?", expected_norm)
        actual_numbers = re.findall(r"\d+(?:\.\d+)?", actual)
        matched = 0
        for expect_num in expected_numbers:
            for act_num in actual_numbers:
                try:
                    if abs(float(act_num) - float(expect_num)) < 0.01:
                        matched += 1
                        break
                except ValueError:
                    pass
        assert matched == len(expected_numbers), f"expected {expected!r} numeric values not in {result.exact!r}"

    def test_determinism(self):
        first = _engine_answer("velocity of 200 m in 10 s")
        for _ in range(5):
            assert _engine_answer("velocity of 200 m in 10 s") == first


# ---------------------------------------------------------------------------
# Engine: Phase 30 feature additions
# ---------------------------------------------------------------------------


class TestPhysicsEnginePhase30Features:
    def test_velocity_english(self):
        assert "20" in _engine_answer("velocity of 200 m in 10 s")

    def test_velocity_bengali(self):
        assert "20" in _unify_digits(_engine_answer("২০০ মিটার ১০ সেকেন্ডে অতিক্রমের বেগ"))

    def test_force_english(self):
        assert "10" in _engine_answer("force of mass 5 kg acceleration 2 m/s^2")

    def test_kinetic_energy(self):
        assert "9" in _engine_answer("kinetic energy of mass 2 kg at 3 m/s")

    def test_work(self):
        assert "40" in _engine_answer("work done by force 10 N over 4 m")

    def test_potential_energy(self):
        assert "196" in _engine_answer("potential energy of 2 kg at height 10 m")

    def test_momentum(self):
        assert "6" in _engine_answer("momentum of mass 2 kg at 3 m/s")

    def test_free_fall(self):
        assert "122.5" in _engine_answer("distance fallen freely in 5 seconds")

    def test_free_fall_bengali(self):
        result = PHYSICS_ENGINE.solve(_BN_FALL_3)
        assert result is not None and "44.1" in _unify_digits(str(result.exact))

    def test_ohm_current(self):
        assert "3" in _engine_answer("current with voltage 12 V and resistance 4 ohm")

    def test_ohm_bengali(self):
        assert "3" in _unify_digits(_engine_answer(_BN_OHM_12_4))

    def test_series_resistance(self):
        assert "9" in _engine_answer("total resistance of 6 ohm and 3 ohm in series")

    def test_series_bengali(self):
        assert "9" in _unify_digits(_engine_answer(_BN_SERIES_6_3))

    def test_parallel_resistance(self):
        assert "2" in _engine_answer("total resistance of 6 ohm and 3 ohm in parallel")

    def test_parallel_bengali(self):
        assert "2" in _unify_digits(_engine_answer(_BN_PARALLEL_6_3))

    def test_power_voltage_current(self):
        assert "60" in _engine_answer("power for 12 V and 5 A")

    def test_power_work_time(self):
        assert "20" in _engine_answer("power for 100 J of work in 5 s")

    def test_wave_speed(self):
        assert "200" in _engine_answer("speed of wave with frequency 50 Hz and wavelength 4 m")

    def test_wave_bengali(self):
        assert "200" in _unify_digits(_engine_answer(_BN_WAVE_50_4))

    def test_wave_not_velocity(self):
        # A wave question must never be parsed as plain velocity (f x λ,
        assert "200" in _unify_digits(_engine_answer(_BN_WAVE_50_4))
        assert "12.5" not in _engine_answer("speed of wave with frequency 50 Hz and wavelength 4 m")

    def test_free_fall_not_undefined(self):
        # 3 s free fall must never hit the unsupported fallback.
        result = PHYSICS_ENGINE.solve("free fall distance in 3 s")
        assert result is not None and result.exact not in ("unsupported", "missing_values", "undefined")


# ---------------------------------------------------------------------------
# Brain: concept questions answered from stored curriculum knowledge
# ---------------------------------------------------------------------------


class TestBrainPhysicsConceptQuestions:
    @pytest.fixture(autouse=True)
    def _brain(self):
        self.brain = _new_brain()
        register_physics_curriculum(self.brain)

    def _answer(self, text: str) -> str:
        return str(self.brain.process(text).get("response", ""))

    # --- Kinematics vocabulary ---

    def test_velocity_definition_english(self):
        answer = self._answer("velocity definition?")
        lowered = answer.lower()
        assert "not learned" not in lowered and "শিখিনি" not in lowered
        assert "velocity" in lowered or "m/s" in answer or "displacement" in lowered

    def test_velocity_definition_bengali(self):
        answer = self._answer("বেগের সংজ্ঞা কী?")
        lowered = answer.lower()
        assert "not learned" not in lowered and "শিখিনি" not in lowered
        assert "বেগ" in lowered or "m/s" in answer or "সরণ" in lowered

    def test_acceleration_definition(self):
        answer = self._answer("acceleration definition?")
        lowered = answer.lower()
        assert "not learned" not in lowered and "শিখিনি" not in lowered
        assert "acceleration" in lowered or "m/s" in answer

    def test_free_fall_definition(self):
        answer = self._answer("what is free fall?")
        lowered = answer.lower()
        assert "not learned" not in lowered and "শিখিনি" not in lowered
        assert "free fall" in lowered or "gravit" in lowered or "9.8" in answer or "mukt" in lowered

    # --- Mechanics vocabulary ---

    def test_newton_second_law(self):
        answer = self._answer("newton's second law definition?")
        lowered = answer.lower()
        assert "not learned" not in lowered and "শিখিনি" not in lowered
        assert "second law" in lowered or "f = ma" in lowered.replace(" ", "") or "force" in lowered

    def test_newton_second_law_bengali(self):
        answer = self._answer("নিউটনের দ্বিতীয় সূত্র কী?")
        lowered = answer.lower()
        assert "not learned" not in lowered and "শিখিনি" not in lowered
        assert "দ্বিতীয়" in lowered or "f = ma" in answer.replace(" ", "") or "বল" in lowered

    def test_inertia_definition(self):
        answer = self._answer("what is inertia?")
        lowered = answer.lower()
        assert "not learned" not in lowered and "শিখিনি" not in lowered
        assert "inertia" in lowered or "জড়তা" in lowered or "rest" in lowered or "motion" in lowered

    def test_weight_definition(self):
        answer = self._answer("weight definition?")
        lowered = answer.lower()
        assert "not learned" not in lowered and "শিখিনি" not in lowered
        assert "weight" in lowered or "gravit" in lowered or "mg" in answer or "ওজন" in lowered

    # --- Energy vocabulary ---

    def test_kinetic_energy_definition(self):
        answer = self._answer("kinetic energy definition?")
        lowered = answer.lower()
        assert "not learned" not in lowered and "শিখিনি" not in lowered
        assert "kinetic" in lowered or "1/2" in answer or "½" in answer or "mv" in answer

    def test_kinetic_energy_bengali(self):
        answer = self._answer("গতিশক্তির সংজ্ঞা কী?")
        lowered = answer.lower()
        assert "not learned" not in lowered and "শিখিনি" not in lowered
        assert "গতিশক্তি" in lowered or "½" in answer or "mv" in answer or "kinetic" in lowered

    def test_potential_energy_definition(self):
        answer = self._answer("potential energy definition?")
        lowered = answer.lower()
        assert "not learned" not in lowered and "শিখিনি" not in lowered
        assert "potential" in lowered or "mgh" in answer

    def test_work_definition(self):
        answer = self._answer("work definition?")
        lowered = answer.lower()
        assert "not learned" not in lowered and "শিখিনি" not in lowered
        assert "work" in lowered or "f x s" in answer.replace(" ", "") or "কাজ" in lowered

    def test_power_definition(self):
        answer = self._answer("power definition?")
        lowered = answer.lower()
        assert "not learned" not in lowered and "শিখিনি" not in lowered
        assert "power" in lowered or "watt" in lowered or "w / t" in answer or "ক্ষমতা" in lowered

    # --- Waves vocabulary ---

    def test_wave_definition_english(self):
        answer = self._answer("what is a wave?")
        lowered = answer.lower()
        assert "not learned" not in lowered and "শিখিনি" not in lowered
        assert "wave" in lowered or "তরঙ্গ" in lowered or "disturbance" in lowered or "energy" in lowered

    def test_frequency_definition(self):
        answer = self._answer("frequency definition?")
        lowered = answer.lower()
        assert "not learned" not in lowered and "শিখিনি" not in lowered
        assert "frequency" in lowered or "hertz" in lowered or "hz" in lowered or "কম্পাঙ্ক" in lowered

    # --- Electricity vocabulary ---

    def test_ohms_law_definition(self):
        answer = self._answer("ohm's law definition?")
        lowered = answer.lower()
        assert "not learned" not in lowered and "শিখিনি" not in lowered
        assert "ohm" in lowered or "i = v / r" in answer.replace(" ", "") or "voltage" in lowered

    def test_ohms_law_bengali(self):
        answer = self._answer("ওহমের সূত্র কী?")
        lowered = answer.lower()
        assert "not learned" not in lowered and "শিখিনি" not in lowered
        assert "ওহম" in lowered or "i = v/r" in answer.replace(" ", "") or "রোধ" in lowered

    def test_series_vs_parallel(self):
        answer = self._answer("series and parallel circuit difference?")
        lowered = answer.lower()
        # Brain should not admit ignorance about circuits.
        assert "not learned" not in lowered and "শিখিনি" not in lowered

    # --- Optics vocabulary ---

    def test_reflection_definition(self):
        answer = self._answer("reflection definition?")
        lowered = answer.lower()
        assert "not learned" not in lowered and "শিখিনি" not in lowered
        assert "reflection" in lowered or "light" in lowered or "প্রতিফলন" in lowered

    def test_refraction_definition(self):
        answer = self._answer("refraction definition?")
        lowered = answer.lower()
        assert "not learned" not in lowered and "শিখিনি" not in lowered
        assert "refraction" in lowered or "প্রতিসরণ" in lowered or "bend" in lowered

    def test_focal_length_definition(self):
        answer = self._answer("focal length definition?")
        lowered = answer.lower()
        assert "not learned" not in lowered and "শিখিনি" not in lowered
        assert "focal" in lowered or "lens" in lowered or "ফোকাস" in lowered

    # --- Engine-backed answers via the physics engine through the brain ---

    def test_brain_computes_velocity(self):
        answer = self._answer("velocity of 200 m in 10 s")
        assert "20" in answer

    def test_brain_computes_ohm(self):
        answer = self._answer("current with voltage 12 V and resistance 4 ohm")
        assert "3" in answer

    def test_brain_computes_wave(self):
        answer = self._answer("speed of wave with frequency 50 Hz and wavelength 4 m")
        assert "200" in answer
