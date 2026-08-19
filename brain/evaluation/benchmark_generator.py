"""Automated benchmark generation from curriculum manifests.

Curriculum units declare expected observable behavior (fragment coverage and
prompt templates). This module generates deterministic BilingualCase objects
from those declarations so every training department gets a runnable,
inspectable acceptance suite without hand-written duplication.

The generator only uses manifest-declared data; it never synthesizes answers
that the curriculum does not cover.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Tuple

from brain.evaluation.bilingual import BenchmarkCase, default_bilingual_cases


@dataclass(frozen=True)
class UnitCaseSpec:
    """Manifest-declared coverage requirement for one curriculum unit."""

    unit: str
    department: str
    fragments: Tuple[str, ...]
    minimum_confidence: float
    required_claims: Tuple[str, ...] = ()
    prompt_template: str = ""


UNIT_CASE_SPECS: Dict[str, Tuple[UnitCaseSpec, ...]] = {
    "language": (
        UnitCaseSpec(
            unit="bengali-digit-and-number-parsing",
            department="language",
            fragments=("সংখ্যা",),
            minimum_confidence=0.4,
            prompt_template="৫ এবং ৩ যোগ করো",
        ),
        UnitCaseSpec(
            unit="intent-and-entity-extraction",
            department="language",
            fragments=("Misty",),
            minimum_confidence=0.7,
            required_claims=("workspace_evidence",),
            prompt_template="মিস্টি কে?",
        ),
        UnitCaseSpec(
            unit="code-switching-and-terminology",
            department="language",
            fragments=("Misty",),
            minimum_confidence=0.6,
            prompt_template="Who are you? তুমি কি Bengali বলতে পারো?",
        ),
        UnitCaseSpec(
            unit="grounded-bilingual-rendering",
            department="language",
            fragments=("Misty",),
            minimum_confidence=0.6,
            prompt_template="You are a digital brain. Tell me about yourself in Bengali.",
        ),
    ),
    "mathematics": (
        UnitCaseSpec(
            unit="arithmetic-and-number-theory",
            department="mathematics",
            fragments=("9",),
            minimum_confidence=0.6,
            required_claims=("deterministic_math_engine",),
            prompt_template="What is 7 + 2?",
        ),
        UnitCaseSpec(
            unit="fractions-ratios-and-percentages",
            department="mathematics",
            fragments=("50",),
            minimum_confidence=0.5,
            prompt_template="100 এর 50% কত?",
        ),
        UnitCaseSpec(
            unit="algebra-and-equations",
            department="mathematics",
            fragments=("x", "5"),
            minimum_confidence=0.4,
            prompt_template="Solve x + 3 = 8",
        ),
        UnitCaseSpec(
            unit="geometry-and-trigonometry",
            department="mathematics",
            fragments=("geometry",),
            minimum_confidence=0.3,
            prompt_template="What is the area formula of a circle?",
        ),
        UnitCaseSpec(
            unit="sequences-combinatorics-and-probability",
            department="mathematics",
            fragments=("probability",),
            minimum_confidence=0.3,
            prompt_template="Define probability.",
        ),
        UnitCaseSpec(
            unit="discrete-mathematics-and-logic",
            department="mathematics",
            fragments=("logic",),
            minimum_confidence=0.3,
            prompt_template="What is mathematical logic?",
        ),
    ),
    "physics": (
        UnitCaseSpec(
            unit="measurement-units-and-dimensions",
            department="physics",
            fragments=("meter",),
            minimum_confidence=0.4,
            prompt_template="What is the SI unit of length?",
        ),
        UnitCaseSpec(
            unit="vectors-and-kinematics",
            department="physics",
            fragments=("velocity",),
            minimum_confidence=0.4,
            prompt_template="Define velocity.",
        ),
        UnitCaseSpec(
            unit="newtonian-mechanics",
            department="physics",
            fragments=("force",),
            minimum_confidence=0.4,
            prompt_template="State Newton's second law.",
        ),
        UnitCaseSpec(
            unit="energy-momentum-and-gravitation",
            department="physics",
            fragments=("energy",),
            minimum_confidence=0.4,
            prompt_template="Define kinetic energy.",
        ),
        UnitCaseSpec(
            unit="fluids-thermodynamics-and-waves",
            department="physics",
            fragments=("wave",),
            minimum_confidence=0.3,
            prompt_template="What is a mechanical wave?",
        ),
        UnitCaseSpec(
            unit="optics-and-electromagnetism",
            department="physics",
            fragments=("light",),
            minimum_confidence=0.3,
            prompt_template="What is reflection of light?",
        ),
    ),
    "literature": (
        UnitCaseSpec(
            unit="periods-and-literary-movements",
            department="literature",
            fragments=("Bengali",),
            minimum_confidence=0.3,
            prompt_template="What is Bengali literature?",
        ),
        UnitCaseSpec(
            unit="genres-and-literary-devices",
            department="literature",
            fragments=("poem",),
            minimum_confidence=0.3,
            prompt_template="Define a poem as a literary genre.",
        ),
        UnitCaseSpec(
            unit="author-work-relations",
            department="literature",
            fragments=("Rabindranath",),
            minimum_confidence=0.4,
            prompt_template="Who wrote Gitanjali?",
        ),
        UnitCaseSpec(
            unit="grounded-summary",
            department="literature",
            fragments=("Rabindranath",),
            minimum_confidence=0.4,
            required_claims=("workspace_evidence",),
            prompt_template="Summarize Rabindranath Tagore's contribution with evidence.",
        ),
    ),
    "reasoning": (
        UnitCaseSpec(
            unit="deduction",
            department="reasoning",
            fragments=("deduction",),
            minimum_confidence=0.3,
            prompt_template="What is deductive reasoning?",
        ),
        UnitCaseSpec(
            unit="induction",
            department="reasoning",
            fragments=("induction",),
            minimum_confidence=0.3,
            prompt_template="What is inductive reasoning?",
        ),
    ),
    "commonsense": (
        UnitCaseSpec(
            unit="physical-intuition",
            department="commonsense",
            fragments=("commonsense",),
            minimum_confidence=0.2,
            prompt_template="What is commonsense reasoning?",
        ),
    ),
    "memory": (
        UnitCaseSpec(
            unit="consolidation",
            department="memory",
            fragments=("memory",),
            minimum_confidence=0.3,
            prompt_template="What is memory consolidation?",
        ),
    ),
    "perception": (
        UnitCaseSpec(
            unit="attention",
            department="perception",
            fragments=("attention",),
            minimum_confidence=0.3,
            prompt_template="What is attention in perception?",
        ),
    ),
    "emotion": (
        UnitCaseSpec(
            unit="appraisal",
            department="emotion",
            fragments=("emotion",),
            minimum_confidence=0.3,
            prompt_template="What is emotion appraisal?",
        ),
    ),
    "self_model": (
        UnitCaseSpec(
            unit="identity-stability",
            department="self_model",
            fragments=("Misty",),
            minimum_confidence=0.7,
            required_claims=("workspace_evidence",),
            prompt_template="Who created you and what are your capabilities?",
        ),
        UnitCaseSpec(
            unit="uncertainty-awareness",
            department="self_model",
            fragments=("Misty",),
            minimum_confidence=0.5,
            prompt_template="When should you express uncertainty?",
        ),
        UnitCaseSpec(
            unit="planning",
            department="self_model",
            fragments=("plan",),
            minimum_confidence=0.3,
            prompt_template="What is planning in cognitive agents?",
        ),
    ),
}


def language_prompt_for_unit(unit: str, language: str, spec: UnitCaseSpec) -> str:
    """Choose a language variant of the manifest prompt."""
    if not spec.prompt_template:
        return f"Explain {unit.replace('-', ' ')} in {language}."
    return spec.prompt_template


def cases_from_specs(
    specs: Dict[str, Tuple[UnitCaseSpec, ...]],
    languages: Tuple[str, ...] = ("bn", "en"),
    prefix: str = "curriculum",
) -> List[BenchmarkCase]:
    """Generate deterministic bilingual cases from unit case specs."""
    cases: List[BenchmarkCase] = []
    for department, department_specs in sorted(specs.items()):
        for spec in department_specs:
            for language in languages:
                case_id = f"{prefix}.{department}.{spec.unit}.{language}"
                prompt = language_prompt_for_unit(spec.unit, language, spec)
                cases.append(
                    BenchmarkCase(
                        case_id=case_id,
                        language=language,
                        prompt=prompt,
                        expected_fragments=spec.fragments,
                        minimum_confidence=spec.minimum_confidence,
                        required_claims=spec.required_claims,
                    )
                )
    return cases


def generated_benchmark_cases() -> List[BenchmarkCase]:
    """Default generated suite combining all curriculum unit specs."""
    return cases_from_specs(UNIT_CASE_SPECS)


def curriculum_cases(department: str, languages: Tuple[str, ...] = ("bn", "en")) -> List[BenchmarkCase]:
    """Generated cases scoped to one department, or empty for unmapped departments."""
    specs = UNIT_CASE_SPECS.get(department, ())
    return cases_from_specs({department: specs}, languages=languages)


def all_acceptance_cases() -> List[BenchmarkCase]:
    """Full suite: default identity/engine cases plus all generated curriculum cases."""
    return list(default_bilingual_cases()) + generated_benchmark_cases()


def unit_coverage_map() -> Dict[str, Dict[str, Any]]:
    """Inspectable mapping of department -> units -> generated case count."""
    mapping: Dict[str, Dict[str, Any]] = {}
    for department, specs in sorted(UNIT_CASE_SPECS.items()):
        mapping[department] = {
            "units": tuple(spec.unit for spec in specs),
            "generated_cases": len(specs) * 2,  # bn and en
            "total_specs": len(specs),
        }
    return mapping
