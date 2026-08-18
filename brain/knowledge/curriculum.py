"""Department curriculum manifests for MISTY's structured training program."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List


@dataclass(frozen=True)
class CurriculumModule:
    department: str
    title: str
    languages: tuple[str, ...]
    prerequisites: tuple[str, ...]
    units: tuple[str, ...]
    package_ids: tuple[str, ...]
    benchmark_ids: tuple[str, ...]
    acceptance: Dict[str, float]


LANGUAGE_CURRICULUM = CurriculumModule(
    department="language",
    title="Bengali-English compositional language",
    languages=("bn", "en"),
    prerequisites=("identity.v1", "grounding.v1"),
    units=(
        "unicode-and-script-normalization",
        "bengali-digit-and-number-parsing",
        "intent-and-entity-extraction",
        "code-switching-and-terminology",
        "dialogue-state-and-coreference",
        "grounded-bilingual-rendering",
    ),
    package_ids=("language.bengali.v1", "language.english.v1"),
    benchmark_ids=("lang.intent.bn-en.v1", "lang.grounding.bn-en.v1"),
    acceptance={"intent_exact_match": 0.90, "formula_language_invariance": 0.95, "unsupported_claim_rate_max": 0.01},
)

MATHEMATICS_CURRICULUM = CurriculumModule(
    department="mathematics",
    title="Deterministic mathematics and proof traces",
    languages=("bn", "en"),
    prerequisites=("language.bengali.v1", "math.arithmetic.v1"),
    units=(
        "arithmetic-and-number-theory",
        "fractions-ratios-and-percentages",
        "algebra-and-equations",
        "geometry-and-trigonometry",
        "sequences-combinatorics-and-probability",
        "statistics-and-data",
        "calculus-and-linear-algebra",
        "discrete-mathematics-and-logic",
    ),
    package_ids=("mathematics.core.v1", "mathematics.algebra.v1"),
    benchmark_ids=("math.exact.bn-en.v1", "math.steps.v1"),
    acceptance={"exact_answer": 0.95, "invalid_expression_rejection": 1.0, "step_reproducibility": 0.95},
)

PHYSICS_CURRICULUM = CurriculumModule(
    department="physics",
    title="Unit-aware physics reasoning",
    languages=("bn", "en"),
    prerequisites=("mathematics.core.v1", "physics.measurement.v1"),
    units=(
        "measurement-units-and-dimensions",
        "vectors-and-kinematics",
        "newtonian-mechanics",
        "energy-momentum-and-gravitation",
        "fluids-thermodynamics-and-waves",
        "optics-and-electromagnetism",
        "relativity-and-quantum-foundations",
        "atomic-nuclear-and-astrophysics",
    ),
    package_ids=("physics.core.v1", "physics.mechanics.v1"),
    benchmark_ids=("physics.units.v1", "physics.formulas.bn-en.v1"),
    acceptance={"formula_selection": 0.90, "unit_consistency": 0.98, "incomplete_data_detection": 0.95},
)

LITERATURE_CURRICULUM = CurriculumModule(
    department="literature",
    title="Bengali literature metadata and grounded analysis",
    languages=("bn", "en"),
    prerequisites=("language.bengali.v1", "identity.v1"),
    units=(
        "periods-and-literary-movements",
        "genres-and-literary-devices",
        "author-work-relations",
        "chronology-and-cultural-context",
        "grounded-summary",
        "copyright-safe-analysis",
    ),
    package_ids=("literature.bengali.v1",),
    benchmark_ids=("literature.metadata.bn-en.v1", "literature.grounded-summary.v1"),
    acceptance={"metadata_exactness": 0.98, "author_work_relation": 0.98, "fabricated_quotation_rate_max": 0.0},
)


CURRICULA: Dict[str, CurriculumModule] = {
    curriculum.department: curriculum
    for curriculum in (
        LANGUAGE_CURRICULUM,
        MATHEMATICS_CURRICULUM,
        PHYSICS_CURRICULUM,
        LITERATURE_CURRICULUM,
    )
}


def get_curriculum(department: str) -> CurriculumModule:
    """Return a curriculum manifest or raise a clear error for unknown departments."""
    try:
        return CURRICULA[department]
    except KeyError as exc:
        raise ValueError(f"unknown curriculum department: {department}") from exc


def list_curricula() -> List[CurriculumModule]:
    """Return curriculum manifests in deterministic department order."""
    return [CURRICULA[key] for key in sorted(CURRICULA)]
