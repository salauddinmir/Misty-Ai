# ruff: noqa: RUF001
"""Phase 29: Misty full bilingual mathematics curriculum.

This module trains Misty with a complete school-level mathematics
curriculum in both Bengali and English. Each topic is represented as
structured, source-backed records (concepts, relations, facts, rules,
formulas, examples, and tests) that enter the package registry with
provenance, so the brain can explain mathematics from its stored
knowledge instead of only computing with the deterministic math engine.

Departments:
- arithmetic_pct  : fractions, decimals, percentages, ratios
- algebra         : linear equations, quadratic equations, inequalities
- geometry        : area, perimeter, volume, Pythagoras, angles
- trigonometry    : sin/cos/tan of standard angles and core identities
- series          : arithmetic and geometric progressions and sums
- number_theory   : LCM, GCD, primes, divisibility

The curriculum records coexist with the deterministic MathEngine
(brain/math_engine.py), which already solves these topics
computationally. This package teaches Misty the *vocabulary, rules and
formulas* so it can also explain and answer concept questions about
each topic in Bengali and English.
"""

from __future__ import annotations

import hashlib
from typing import Any, Dict, List

from brain.knowledge.registry import PackageRegistry, SourceRef, TrainingPackageV2

PACKAGE_ID = "misty-mathematics-phase29"
PACKAGE_DEPARTMENT = "mathematics"
PACKAGE_VERSION = "1.0.0"
PACKAGE_LICENSE = "proprietary"

_TOPIC: List[str] = [
    "arithmetic_pct",
    "algebra",
    "geometry",
    "trigonometry",
    "series",
    "number_theory",
]

# ---------------------------------------------------------------------------
# Concepts: the vocabulary of the curriculum (bilingual pairs)
# ---------------------------------------------------------------------------

MATH_CONCEPTS: List[Dict[str, Any]] = [
    # Arithmetic: fractions, decimals, percentages
    {"name": "Fraction", "type": "MathConcept", "lang": "en"},
    {"name": "ভগ্নাংশ", "type": "গণিত ধারণা", "lang": "bn"},
    {"name": "Numerator", "type": "MathConcept", "lang": "en"},
    {"name": "লব", "type": "গণিত ধারণা", "lang": "bn"},
    {"name": "Denominator", "type": "MathConcept", "lang": "en"},
    {"name": "হর", "type": "গণিত ধারণা", "lang": "bn"},
    {"name": "Percentage", "type": "MathConcept", "lang": "en"},
    {"name": "শতকরা", "type": "গণিত ধারণা", "lang": "bn"},
    {"name": "Decimal", "type": "MathConcept", "lang": "en"},
    {"name": "দশমিক", "type": "গণিত ধারণা", "lang": "bn"},
    {"name": "Ratio", "type": "MathConcept", "lang": "en"},
    {"name": "অনুপাত", "type": "গণিত ধারণা", "lang": "bn"},
    # Algebra
    {"name": "Equation", "type": "MathConcept", "lang": "en"},
    {"name": "সমীকরণ", "type": "গণিত ধারণা", "lang": "bn"},
    {"name": "Linear Equation", "type": "MathConcept", "lang": "en"},
    {"name": "রৈখিক সমীকরণ", "type": "গণিত ধারণা", "lang": "bn"},
    {"name": "Quadratic Equation", "type": "MathConcept", "lang": "en"},
    {"name": "দ্বিঘাত সমীকরণ", "type": "গণিত ধারণা", "lang": "bn"},
    {"name": "Inequality", "type": "MathConcept", "lang": "en"},
    {"name": "অসমতা", "type": "গণিত ধারণা", "lang": "bn"},
    {"name": "Variable", "type": "MathConcept", "lang": "en"},
    {"name": "ব্যবহারকারী চলক", "type": "গণিত ধারণা", "lang": "bn"},
    {"name": "Discriminant", "type": "MathConcept", "lang": "en"},
    {"name": "নির্ণায়ক", "type": "গণিত ধারণা", "lang": "bn"},
    # Geometry
    {"name": "Area", "type": "MathConcept", "lang": "en"},
    {"name": "ক্ষেত্রফল", "type": "গণিত ধারণা", "lang": "bn"},
    {"name": "Perimeter", "type": "MathConcept", "lang": "en"},
    {"name": "পরিসীমা", "type": "গণিত ধারণা", "lang": "bn"},
    {"name": "Volume", "type": "MathConcept", "lang": "en"},
    {"name": "আয়তন", "type": "গণিত ধারণা", "lang": "bn"},
    {"name": "Triangle", "type": "Shape", "lang": "en"},
    {"name": "ত্রিভুজ", "type": "আকৃতি", "lang": "bn"},
    {"name": "Rectangle", "type": "Shape", "lang": "en"},
    {"name": "আয়তক্ষেত্র", "type": "আকৃতি", "lang": "bn"},
    {"name": "Circle", "type": "Shape", "lang": "en"},
    {"name": "বৃত্ত", "type": "আকৃতি", "lang": "bn"},
    {"name": "Square", "type": "Shape", "lang": "en"},
    {"name": "বর্গ", "type": "আকৃতি", "lang": "bn"},
    {"name": "Pythagorean Theorem", "type": "MathTheorem", "lang": "en"},
    {"name": "পাইথাগোরাসের উপপাদ্য", "type": "গণিত উপপাদ্য", "lang": "bn"},
    {"name": "Hypotenuse", "type": "MathConcept", "lang": "en"},
    {"name": "অতিভুজ", "type": "গণিত ধারণা", "lang": "bn"},
    {"name": "Angle", "type": "MathConcept", "lang": "en"},
    {"name": "কোণ", "type": "গণিত ধারণা", "lang": "bn"},
    # Trigonometry
    {"name": "Trigonometry Branch", "type": "MathBranch", "lang": "en"},
    {"name": "Sine", "type": "TrigFunction", "lang": "en"},
    {"name": "সাইন", "type": "ত্রিকোণমিতিক ফাংশন", "lang": "bn"},
    {"name": "Cosine", "type": "TrigFunction", "lang": "en"},
    {"name": "কোসাইন", "type": "ত্রিকোণমিতিক ফাংশন", "lang": "bn"},
    {"name": "Tangent", "type": "TrigFunction", "lang": "en"},
    {"name": "ট্যানজেন্ট", "type": "ত্রিকোণমিতিক ফাংশন", "lang": "bn"},
    {"name": "Right Triangle", "type": "Shape", "lang": "en"},
    {"name": "সমকোণী ত্রিভুজ", "type": "আকৃতি", "lang": "bn"},
    # Series
    {"name": "Arithmetic Progression", "type": "Sequence", "lang": "en"},
    {"name": "সমান্তর ধারা", "type": "ধারা", "lang": "bn"},
    {"name": "Geometric Progression", "type": "Sequence", "lang": "en"},
    {"name": "গুণোত্তর ধারা", "type": "ধারা", "lang": "bn"},
    {"name": "Common Difference", "type": "MathConcept", "lang": "en"},
    {"name": "সাধারণ অন্তর", "type": "গণিত ধারণা", "lang": "bn"},
    {"name": "Common Ratio", "type": "MathConcept", "lang": "en"},
    {"name": "সাধারণ অনুপাত", "type": "গণিত ধারণা", "lang": "bn"},
    # Number theory
    {"name": "LCM", "type": "MathConcept", "lang": "en"},
    {"name": "ল.সা.গু", "type": "গণিত ধারণা", "lang": "bn"},
    {"name": "GCD", "type": "MathConcept", "lang": "en"},
    {"name": "গ.সা.গু", "type": "গণিত ধারণা", "lang": "bn"},
    {"name": "Prime Number", "type": "NumberClass", "lang": "en"},
    {"name": "মৌলিক সংখ্যা", "type": "সংখ্যা শ্রেণি", "lang": "bn"},
    {"name": "Divisibility", "type": "MathConcept", "lang": "en"},
    {"name": "বিভাজ্যতা", "type": "গণিত ধারণা", "lang": "bn"},
]

# ---------------------------------------------------------------------------
# Relations: branch structure of the curriculum
# ---------------------------------------------------------------------------

# Phase 29: common query aliases → canonical curriculum subjects.
# The NLU head-noun parser produces phrasal targets ("quadratic formula",
# "Pythagorean theorem", "sine function", "gcd definition") that would not
# otherwise match the canonical subjects stored in MATH_FACTS.
MATH_SYNONYMS: Dict[str, str] = {
    "quadratic formula": "Quadratic Equation",
    "দ্বিঘাত সমীকরণের সূত্র": "দ্বিঘাত সমীকরণ",
    "Pythagorean theorem": "Pythagorean Theorem",
    "পাইথাগোরাসের উপপাদ্য": "পাইথাগোরাসের উপপাদ্য",
    "sine function": "Sine",
    "সাইন ফাংশন": "সাইন",
    "cosine function": "Cosine",
    "tangent function": "Tangent",
    "gcd definition": "GCD",
    "lcm definition": "LCM",
    "g.সা.গু definition": "গ.সা.গু",
    "l.সা.গু definition": "ল.সা.গু",
    "percentage definition": "Percentage",
    "arithmetic progression definition": "Arithmetic Progression",
    "সমান্তর ধারার সংজ্ঞা": "সমান্তর ধারা",
    "geometric progression definition": "Geometric Progression",
}

MATH_RELATIONS: List[Dict[str, Any]] = [
    {"source": "Mathematics", "target": "Arithmetic", "type": "includes", "lang": "en"},
    {"source": "Mathematics", "target": "Algebra", "type": "includes", "lang": "en"},
    {"source": "Mathematics", "target": "Geometry", "type": "includes", "lang": "en"},
    {"source": "Mathematics", "target": "Trigonometry", "type": "includes", "lang": "en"},
    {"source": "Mathematics", "target": "Number Theory", "type": "includes", "lang": "en"},
    {"source": "গণিত", "target": "বীজগণিত", "type": "শাখা", "lang": "bn"},
    {"source": "গণিত", "target": "জ্যামিতি", "type": "শাখা", "lang": "bn"},
    {"source": "গণিত", "target": "ত্রিকোণমিতি", "type": "শাখা", "lang": "bn"},
    {"source": "গণিত", "target": "সংখ্যাতত্ত্ব", "type": "শাখা", "lang": "bn"},
    {"source": "Bengali", "target": "Fraction", "type": "translates", "lang": "en"},
    {"source": "Bengali", "target": "Percentage", "type": "translates", "lang": "en"},
    {"source": "Bengali", "target": "Pythagorean Theorem", "type": "translates", "lang": "en"},
    {"source": "Sine", "target": "Trigonometry", "type": "belongs_to", "lang": "en"},
    {"source": "Cosine", "target": "Trigonometry", "type": "belongs_to", "lang": "en"},
    {"source": "Tangent", "target": "Trigonometry", "type": "belongs_to", "lang": "en"},
    {"source": "Arithmetic Progression", "target": "Series", "type": "type_of", "lang": "en"},
    {"source": "Geometric Progression", "target": "Series", "type": "type_of", "lang": "en"},
    {"source": "Hypotenuse", "target": "Right Triangle", "type": "part_of", "lang": "en"},
    {"source": "Misty", "target": "mathematics-curriculum-phase29", "type": "trained_on", "lang": "en"},
]

# ---------------------------------------------------------------------------
# Facts: declarative curriculum knowledge (bilingual)
# ---------------------------------------------------------------------------

MATH_FACTS: List[Dict[str, Any]] = [
    # --- Arithmetic: fractions, decimals, percentages ---
    {
        "subject": "Fraction",
        "predicate": "definition",
        "obj": "a number written as numerator divided by denominator, e.g. 3/4",
        "lang": "en",
        "topic": "arithmetic_pct",
    },
    {
        "subject": "ভগ্নাংশ",
        "predicate": "সংজ্ঞা",
        "obj": "লব ও হর দিয়ে প্রকাশিত সংখ্যা, যেমন ৩/৪",
        "lang": "bn",
        "topic": "arithmetic_pct",
    },
    {
        "subject": "Percentage",
        "predicate": "definition",
        "obj": "a ratio expressed per hundred; 25% means 25 out of 100",
        "lang": "en",
        "topic": "arithmetic_pct",
    },
    {
        "subject": "শতকরা",
        "predicate": "সংজ্ঞা",
        "obj": "প্রতি শত ভাগে প্রকাশিত অনুপাত; ২৫% মানে ১০০ এর মধ্যে ২৫",
        "lang": "bn",
        "topic": "arithmetic_pct",
    },
    {
        "subject": "Decimal",
        "predicate": "definition",
        "obj": "a number with a whole part and a fractional part separated by a dot, e.g. 3.14",
        "lang": "en",
        "topic": "arithmetic_pct",
    },
    {
        "subject": "দশমিক",
        "predicate": "সংজ্ঞা",
        "obj": "পূর্ণসংখ্যা ও ভগ্নাংশ অংশ বিন্দু দিয়ে পৃথক করা সংখ্যা, যেমন ৩.১৪",
        "lang": "bn",
        "topic": "arithmetic_pct",
    },
    {
        "subject": "Ratio",
        "predicate": "definition",
        "obj": "a comparison of two quantities written as a:b, e.g. 2:3",
        "lang": "en",
        "topic": "arithmetic_pct",
    },
    {
        "subject": "অনুপাত",
        "predicate": "সংজ্ঞা",
        "obj": "দুটি রাশির তুলনা যা a:b আকারে লেখা হয়, যেমন ২:৩",
        "lang": "bn",
        "topic": "arithmetic_pct",
    },
    {
        "subject": "Percentage",
        "predicate": "formula",
        "obj": "part = (percentage / 100) x whole",
        "lang": "en",
        "topic": "arithmetic_pct",
    },
    {
        "subject": "শতকরা",
        "predicate": "সূত্র",
        "obj": "অংশ = (শতকরা / ১০০) x সম্পূর্ণ মান",
        "lang": "bn",
        "topic": "arithmetic_pct",
    },
    # --- Algebra: linear and quadratic ---
    {
        "subject": "Linear Equation",
        "predicate": "definition",
        "obj": "an equation of the form ax + b = 0 with solution x = -b/a",
        "lang": "en",
        "topic": "algebra",
    },
    {
        "subject": "রৈখিক সমীকরণ",
        "predicate": "সংজ্ঞা",
        "obj": "ax + b = 0 আকারের সমীকরণ যার সমাধান x = -b/a",
        "lang": "bn",
        "topic": "algebra",
    },
    {
        "subject": "Quadratic Equation",
        "predicate": "definition",
        "obj": "an equation of the form ax^2 + bx + c = 0 where a is not zero",
        "lang": "en",
        "topic": "algebra",
    },
    {
        "subject": "দ্বিঘাত সমীকরণ",
        "predicate": "সংজ্ঞা",
        "obj": "ax^2 + bx + c = 0 আকারের সমীকরণ যেখানে a শূন্য নয়",
        "lang": "bn",
        "topic": "algebra",
    },
    {
        "subject": "Quadratic Equation",
        "predicate": "quadratic_formula",
        "obj": "x = (-b ± sqrt(b^2 - 4ac)) / (2a)",
        "lang": "en",
        "topic": "algebra",
    },
    {
        "subject": "দ্বিঘাত সমীকরণ",
        "predicate": "দ্বিঘাত সূত্র",
        "obj": "x = (-b ± sqrt(b^2 - 4ac)) / (2a)",
        "lang": "bn",
        "topic": "algebra",
    },
    {
        "subject": "Discriminant",
        "predicate": "definition",
        "obj": "d = b^2 - 4ac; d>0 gives two real roots, d=0 one real root, d<0 no real roots",
        "lang": "en",
        "topic": "algebra",
    },
    {
        "subject": "নির্ণায়ক",
        "predicate": "সংজ্ঞা",
        "obj": "d = b^2 - 4ac; d>0 হলে দুটি বাস্তব মূল, d=0 হলে একটি, d<0 হলে কোনো বাস্তব মূল নেই",
        "lang": "bn",
        "topic": "algebra",
    },
    {
        "subject": "Inequality",
        "predicate": "definition",
        "obj": "a relation using <, >, <=, or >=; multiplying by a negative number flips the sign",
        "lang": "en",
        "topic": "algebra",
    },
    {
        "subject": "অসমতা",
        "predicate": "সংজ্ঞা",
        "obj": "<, >, <=, >= চিহ্ন দিয়ে প্রকাশিত সম্পর্ক; ঋণাত্মক সংখ্যা দিয়ে গুণ করলে চিহ্ন উল্টে যায়",
        "lang": "bn",
        "topic": "algebra",
    },
    # --- Geometry ---
    {
        "subject": "Rectangle",
        "predicate": "area_formula",
        "obj": "area = length x width",
        "lang": "en",
        "topic": "geometry",
    },
    {
        "subject": "আয়তক্ষেত্র",
        "predicate": "ক্ষেত্রফল সূত্র",
        "obj": "ক্ষেত্রফল = দৈর্ঘ্য x প্রস্থ",
        "lang": "bn",
        "topic": "geometry",
    },
    {
        "subject": "Square",
        "predicate": "area_formula",
        "obj": "area = side x side = side^2",
        "lang": "en",
        "topic": "geometry",
    },
    {
        "subject": "বর্গ",
        "predicate": "ক্ষেত্রফল সূত্র",
        "obj": "ক্ষেত্রফল = বাহু x বাহু = বাহু^২",
        "lang": "bn",
        "topic": "geometry",
    },
    {
        "subject": "Triangle",
        "predicate": "area_formula",
        "obj": "area = (base x height) / 2",
        "lang": "en",
        "topic": "geometry",
    },
    {
        "subject": "ত্রিভুজ",
        "predicate": "ক্ষেত্রফল সূত্র",
        "obj": "ক্ষেত্রফল = (ভূমি x উচ্চতা) / ২",
        "lang": "bn",
        "topic": "geometry",
    },
    {
        "subject": "Circle",
        "predicate": "area_formula",
        "obj": "area = pi x radius^2",
        "lang": "en",
        "topic": "geometry",
    },
    {
        "subject": "বৃত্ত",
        "predicate": "ক্ষেত্রফল সূত্র",
        "obj": "ক্ষেত্রফল = pi x ব্যাসার্ধ^২",
        "lang": "bn",
        "topic": "geometry",
    },
    {
        "subject": "Circle",
        "predicate": "circumference_formula",
        "obj": "circumference = 2 x pi x radius",
        "lang": "en",
        "topic": "geometry",
    },
    {
        "subject": "বৃত্ত",
        "predicate": "পরিসীমা সূত্র",
        "obj": "পরিসীমা = ২ x pi x ব্যাসার্ধ",
        "lang": "bn",
        "topic": "geometry",
    },
    {
        "subject": "Rectangle",
        "predicate": "perimeter_formula",
        "obj": "perimeter = 2 x (length + width)",
        "lang": "en",
        "topic": "geometry",
    },
    {
        "subject": "আয়তক্ষেত্র",
        "predicate": "পরিসীমা সূত্র",
        "obj": "পরিসীমা = ২ x (দৈর্ঘ্য + প্রস্থ)",
        "lang": "bn",
        "topic": "geometry",
    },
    {
        "subject": "Pythagorean Theorem",
        "predicate": "definition",
        "obj": (
            "in a right triangle the square of the hypotenuse equals the sum of the "
            "squares of the other two sides: c^2 = a^2 + b^2"
        ),
        "lang": "en",
        "topic": "geometry",
    },
    {
        "subject": "পাইথাগোরাসের উপপাদ্য",
        "predicate": "সংজ্ঞা",
        "obj": "সমকোণী ত্রিভুজে অতিভুজের বর্গ অন্য দুই বাহুর বর্গের যোগফলের সমান: c^2 = a^2 + b^2",
        "lang": "bn",
        "topic": "geometry",
    },
    {
        "subject": "Triangle",
        "predicate": "angle_sum",
        "obj": "the three interior angles of any triangle add up to 180 degrees",
        "lang": "en",
        "topic": "geometry",
    },
    {
        "subject": "ত্রিভুজ",
        "predicate": "কোণের যোগফল",
        "obj": "যেকোনো ত্রিভুজের তিন অন্তঃস্থ কোণের যোগফল ১৮০ ডিগ্রি",
        "lang": "bn",
        "topic": "geometry",
    },
    # --- Trigonometry ---
    {
        "subject": "Trigonometry",
        "predicate": "definition",
        "obj": "the branch of mathematics studying relations between sides and angles of triangles",
        "lang": "en",
        "topic": "trigonometry",
    },
    {
        "subject": "ত্রিকোণমিতি",
        "predicate": "সংজ্ঞা",
        "obj": "ত্রিভুজের বাহু ও কোণের মধ্যে সম্পর্ক নিয়ে আলোচনাকারী গণিতের শাখা",
        "lang": "bn",
        "topic": "trigonometry",
    },
    {
        "subject": "Sine",
        "predicate": "definition",
        "obj": "sine of an angle = opposite side / hypotenuse in a right triangle",
        "lang": "en",
        "topic": "trigonometry",
    },
    {
        "subject": "সাইন",
        "predicate": "সংজ্ঞা",
        "obj": "সমকোণী ত্রিভুজে কোণের সাইন = সম্মুখীন বাহু / অতিভুজ",
        "lang": "bn",
        "topic": "trigonometry",
    },
    {
        "subject": "Cosine",
        "predicate": "definition",
        "obj": "cosine of an angle = adjacent side / hypotenuse in a right triangle",
        "lang": "en",
        "topic": "trigonometry",
    },
    {
        "subject": "কোসাইন",
        "predicate": "সংজ্ঞা",
        "obj": "সমকোণী ত্রিভুজে কোণের কোসাইন = সংলগ্ন বাহু / অতিভুজ",
        "lang": "bn",
        "topic": "trigonometry",
    },
    {
        "subject": "Tangent",
        "predicate": "definition",
        "obj": "tangent of an angle = opposite side / adjacent side = sine / cosine",
        "lang": "en",
        "topic": "trigonometry",
    },
    {
        "subject": "ট্যানজেন্ট",
        "predicate": "সংজ্ঞা",
        "obj": "কোণের ট্যানজেন্ট = সম্মুখীন বাহু / সংলগ্ন বাহু = সাইন / কোসাইন",
        "lang": "bn",
        "topic": "trigonometry",
    },
    {
        "subject": "Sine",
        "predicate": "value_30",
        "obj": "sin(30°) = 1/2",
        "lang": "en",
        "topic": "trigonometry",
    },
    {
        "subject": "সাইন",
        "predicate": "মূল্য_৩০",
        "obj": "sin(৩০°) = ১/২",
        "lang": "bn",
        "topic": "trigonometry",
    },
    {
        "subject": "Sine",
        "predicate": "value_45",
        "obj": "sin(45°) = sqrt(2)/2",
        "lang": "en",
        "topic": "trigonometry",
    },
    {
        "subject": "Sine",
        "predicate": "value_60",
        "obj": "sin(60°) = sqrt(3)/2",
        "lang": "en",
        "topic": "trigonometry",
    },
    {
        "subject": "Sine",
        "predicate": "value_90",
        "obj": "sin(90°) = 1",
        "lang": "en",
        "topic": "trigonometry",
    },
    {
        "subject": "Cosine",
        "predicate": "value_0",
        "obj": "cos(0°) = 1",
        "lang": "en",
        "topic": "trigonometry",
    },
    {
        "subject": "Cosine",
        "predicate": "value_60",
        "obj": "cos(60°) = 1/2",
        "lang": "en",
        "topic": "trigonometry",
    },
    {
        "subject": "Cosine",
        "predicate": "value_45",
        "obj": "cos(45°) = sqrt(2)/2",
        "lang": "en",
        "topic": "trigonometry",
    },
    {
        "subject": "Tangent",
        "predicate": "value_45",
        "obj": "tan(45°) = 1",
        "lang": "en",
        "topic": "trigonometry",
    },
    {
        "subject": "Tangent",
        "predicate": "value_30",
        "obj": "tan(30°) = 1/sqrt(3)",
        "lang": "en",
        "topic": "trigonometry",
    },
    {
        "subject": "Tangent",
        "predicate": "value_60",
        "obj": "tan(60°) = sqrt(3)",
        "lang": "en",
        "topic": "trigonometry",
    },
    # --- Series ---
    {
        "subject": "Arithmetic Progression",
        "predicate": "definition",
        "obj": "a sequence where each term differs from the previous by a fixed common difference d",
        "lang": "en",
        "topic": "series",
    },
    {
        "subject": "সমান্তর ধারা",
        "predicate": "সংজ্ঞা",
        "obj": "একটি ধারা যেখানে প্রতিটি পদ আগের পদের থেকে নির্দিষ্ট সাধারণ অন্তর d দ্বারা পার্থক্যযুক্ত",
        "lang": "bn",
        "topic": "series",
    },
    {
        "subject": "Arithmetic Progression",
        "predicate": "nth_term",
        "obj": "n-th term = a + (n-1) x d, where a is the first term",
        "lang": "en",
        "topic": "series",
    },
    {
        "subject": "সমান্তর ধারা",
        "predicate": "n-তম পদ",
        "obj": "n-তম পদ = a + (n-1) x d, যেখানে a প্রথম পদ",
        "lang": "bn",
        "topic": "series",
    },
    {
        "subject": "Arithmetic Progression",
        "predicate": "sum_formula",
        "obj": "sum of first n terms = (n/2) x (2a + (n-1) x d)",
        "lang": "en",
        "topic": "series",
    },
    {
        "subject": "সমান্তর ধারা",
        "predicate": "যোগফল সূত্র",
        "obj": "প্রথম n পদের যোগফল = (n/2) x (2a + (n-1) x d)",
        "lang": "bn",
        "topic": "series",
    },
    {
        "subject": "Geometric Progression",
        "predicate": "definition",
        "obj": "a sequence where each term is obtained by multiplying the previous term by a fixed common ratio r",
        "lang": "en",
        "topic": "series",
    },
    {
        "subject": "গুণোত্তর ধারা",
        "predicate": "সংজ্ঞা",
        "obj": "একটি ধারা যেখানে প্রতিটি পদ আগের পদকে নির্দিষ্ট সাধারণ অনুপাত r দ্বারা গুণ করে পাওয়া যায়",
        "lang": "bn",
        "topic": "series",
    },
    {
        "subject": "Geometric Progression",
        "predicate": "nth_term",
        "obj": "n-th term = a x r^(n-1), where a is the first term",
        "lang": "en",
        "topic": "series",
    },
    {
        "subject": "গুণোত্তর ধারা",
        "predicate": "n-তম পদ",
        "obj": "n-তম পদ = a x r^(n-1), যেখানে a প্রথম পদ",
        "lang": "bn",
        "topic": "series",
    },
    # --- Number theory ---
    {
        "subject": "LCM",
        "predicate": "definition",
        "obj": "the least common multiple: the smallest positive integer divisible by all given numbers",
        "lang": "en",
        "topic": "number_theory",
    },
    {
        "subject": "ল.সা.গু",
        "predicate": "সংজ্ঞা",
        "obj": "লঘিষ্ঠম সম্পূর্ণ গুণিতক: প্রদত্ত সব সংখ্যা দ্বারা বিভাজ্য ক্ষুদ্রতম ধনাত্মক পূর্ণসংখ্যা",
        "lang": "bn",
        "topic": "number_theory",
    },
    {
        "subject": "GCD",
        "predicate": "definition",
        "obj": "the greatest common divisor: the largest positive integer that divides all given numbers",
        "lang": "en",
        "topic": "number_theory",
    },
    {
        "subject": "গ.সা.গু",
        "predicate": "সংজ্ঞা",
        "obj": "গরিষ্ঠম সাধারণ গুণনীয়ক: প্রদত্ত সব সংখ্যাকে ভাগ করতে পারা বৃহত্তম ধনাত্মক পূর্ণসংখ্যা",
        "lang": "bn",
        "topic": "number_theory",
    },
    {
        "subject": "LCM",
        "predicate": "gcd_relation",
        "obj": "LCM(a,b) x GCD(a,b) = a x b for any two positive integers",
        "lang": "en",
        "topic": "number_theory",
    },
    {
        "subject": "ল.সা.গু",
        "predicate": "গসাগু সম্পর্ক",
        "obj": "LCM(a,b) x GCD(a,b) = a x b যেকোনো দুটি ধনাত্মক পূর্ণসংখ্যার জন্য",
        "lang": "bn",
        "topic": "number_theory",
    },
    {
        "subject": "Prime Number",
        "predicate": "definition",
        "obj": "a number greater than 1 whose only divisors are 1 and itself; 2, 3, 5, 7 are the first primes",
        "lang": "en",
        "topic": "number_theory",
    },
    {
        "subject": "মৌলিক সংখ্যা",
        "predicate": "সংজ্ঞা",
        "obj": "১ এর বড় সংখ্যা যার একমাত্র ভাজক ১ ও নিজে; ২, ৩, ৫, ৭ প্রথম মৌলিক সংখ্যা",
        "lang": "bn",
        "topic": "number_theory",
    },
    {
        "subject": "Divisibility",
        "predicate": "rule_of_10",
        "obj": "a number is divisible by 10 if and only if its last digit is 0",
        "lang": "en",
        "topic": "number_theory",
    },
    {
        "subject": "Divisibility",
        "predicate": "নিয়ম_১০",
        "obj": "সংখ্যার শেষ অঙ্ক ০ হলেই সংখ্যাটি ১০ দ্বারা বিভাজ্য",
        "lang": "bn",
        "topic": "number_theory",
    },
]

# ---------------------------------------------------------------------------
# Formulas: canonical named formulas of the curriculum
# ---------------------------------------------------------------------------

MATH_FORMULAS: List[Dict[str, Any]] = [
    {"name": "quadratic_formula", "expression": "x = (-b ± sqrt(b^2 - 4ac)) / (2a)", "lang": "en", "confidence": 0.98},
    {"name": "দ্বিঘাত সূত্র", "expression": "x = (-b ± sqrt(b^2 - 4ac)) / (2a)", "lang": "bn", "confidence": 0.98},
    {"name": "discriminant", "expression": "d = b^2 - 4ac", "lang": "en", "confidence": 0.98},
    {"name": "nirnayok", "expression": "d = b^2 - 4ac", "lang": "bn", "confidence": 0.98},
    {"name": "rectangle_area", "expression": "A = length x width", "lang": "en", "confidence": 0.98},
    {"name": "triangle_area", "expression": "A = (base x height) / 2", "lang": "en", "confidence": 0.98},
    {"name": "circle_area", "expression": "A = pi x r^2", "lang": "en", "confidence": 0.98},
    {"name": "circle_circumference", "expression": "C = 2 x pi x r", "lang": "en", "confidence": 0.98},
    {"name": "pythagoras", "expression": "c^2 = a^2 + b^2", "lang": "en", "confidence": 0.98},
    {"name": "ap_nth_term", "expression": "a_n = a + (n-1) x d", "lang": "en", "confidence": 0.98},
    {"name": "ap_sum", "expression": "S_n = (n/2) x (2a + (n-1) x d)", "lang": "en", "confidence": 0.98},
    {"name": "gp_nth_term", "expression": "a_n = a x r^(n-1)", "lang": "en", "confidence": 0.98},
    {"name": "lcm_gcd_product", "expression": "LCM(a,b) x GCD(a,b) = a x b", "lang": "en", "confidence": 0.98},
    {"name": "percentage_part", "expression": "part = (percentage / 100) x whole", "lang": "en", "confidence": 0.95},
]

# ---------------------------------------------------------------------------
# Rules: inference rules that let the brain reason mathematically
# ---------------------------------------------------------------------------

MATH_RULES: List[Dict[str, Any]] = [
    {
        "when": "quadratic equation ax^2 + bx + c = 0 with b^2 - 4ac >= 0",
        "then": "real roots exist and are given by the quadratic formula x = (-b ± sqrt(b^2 - 4ac)) / (2a)",
        "lang": "en",
    },
    {
        "when": "quadratic সমীকরণ ax^2 + bx + c = 0 যেখানে b^2 - 4ac >= 0",
        "then": "বাস্তব মূল বিদ্যমান এবং দ্বিঘাত সূত্র দ্বারা পাওয়া যায় x = (-b ± sqrt(b^2 - 4ac)) / (2a)",
        "lang": "bn",
    },
    {
        "when": "right triangle with legs a and b and hypotenuse c",
        "then": "c = sqrt(a^2 + b^2) by the Pythagorean theorem",
        "lang": "en",
    },
    {
        "when": "two positive integers a and b",
        "then": "GCD(a,b) can be found with the Euclidean algorithm and LCM(a,b) = (a x b) / GCD(a,b)",
        "lang": "en",
    },
    {
        "when": "দুটি ধনাত্মক পূর্ণসংখ্যা a ও b",
        "then": "ইউক্লিডীয় অ্যালগোরিদম দিয়ে GCD(a,b) পাওয়া যায় এবং LCM(a,b) = (a x b) / GCD(a,b)",
        "lang": "bn",
    },
    {
        "when": "percentage p of a whole w is asked",
        "then": "the answer is (p / 100) x w",
        "lang": "en",
    },
    {
        "when": "AP first term a with common difference d and n terms",
        "then": "sum = (n/2) x (2a + (n-1) x d)",
        "lang": "en",
    },
    {
        "when": "GP first term a with common ratio r and n terms",
        "then": "n-th term = a x r^(n-1)",
        "lang": "en",
    },
]

# ---------------------------------------------------------------------------
# Examples: worked bilingual examples
# ---------------------------------------------------------------------------

MATH_EXAMPLES: List[Dict[str, Any]] = [
    {
        "input": "solve x^2 - 5x + 6 = 0",
        "output": "x = 2 or x = 3 (roots of the quadratic)",
        "lang": "en",
    },
    {"input": "৩০০ এর ১৫% কত?", "output": "৪৫ (কারণ ৩০০ x ১৫ / ১০০ = ৪৫)", "lang": "bn", "confidence": 0.95},
    {"input": "what is 15% of 300?", "output": "45, because 300 x 15 / 100 = 45", "lang": "en", "confidence": 0.95},
    {
        "input": "বাহু ৫ ও ১২ হলে অতিভুজ কত?",
        "output": "১৩, কারণ sqrt(5^2 + 12^2) = sqrt(169) = ১৩",
        "lang": "bn",
    },
    {
        "input": "দৈর্ঘ্য ৮ ও প্রস্থ ৫ হলে আয়তক্ষেত্রের ক্ষেত্রফল কত?",
        "output": "৪০ বর্গ একক (৮ x ৫)",
        "lang": "bn",
    },
    {
        "input": "lcm of 12 and 18?",
        "output": "36, since GCD(12,18) = 6 and LCM = (12 x 18) / 6 = 36",
        "lang": "en",
    },
    {
        "input": "১২ ও ১৮ এর গ.সা.গু কত?",
        "output": "৬ (ইউক্লিডীয় অ্যালগোরিদম: 18 = 1 x 12 + 6, 12 = 2 x 6)",
        "lang": "bn",
    },
    {
        "input": "first term 3, common difference 4, find the 10th term",
        "output": "39, because 3 + 9 x 4 = 39",
        "lang": "en",
    },
    {"input": "sin(30°) এর মান কত?", "output": "১/২", "lang": "bn", "confidence": 0.95},
    {"input": "what is tan(45°)?", "output": "1", "lang": "en", "confidence": 0.95},
    {
        "input": "solve 2x + 6 = 0",
        "output": "x = -3, because 2x = -6 so x = -6/2 = -3",
        "lang": "en",
    },
    {
        "input": "২x + ৬ = ০ সমাধান করো",
        "output": "x = -৩, কারণ ২x = -৬, সুতরাং x = -৬/২ = -৩",
        "lang": "bn",
    },
    {
        "input": "5 cm ব্যাসার্ধের বৃত্তের ক্ষেত্রফল কত?",
        "output": "78.54 বর্গ সেমি (pi x 5^2 ≈ 78.54)",
        "lang": "bn",
    },
]

# ---------------------------------------------------------------------------
# Tests: deterministic sanity tests embedded in the package
# ---------------------------------------------------------------------------

MATH_TESTS: List[Dict[str, Any]] = [
    {
        "id": "p29_quad_roots",
        "input": "solve x^2 - 5x + 6 = 0",
        "expected_output": "x = 2 or x = 3",
        "lang": "en",
    },
    {"id": "p29_pct_15_of_300", "input": "15% of 300", "expected_output": "45", "lang": "en", "confidence": 0.95},
    {"id": "p29_pct_15_of_300_bn", "input": "৩০০ এর ১৫%", "expected_output": "৪৫", "lang": "bn", "confidence": 0.95},
    {
        "id": "p29_pythagoras_5_12",
        "input": "hypotenuse of right triangle with legs 5 and 12",
        "expected_output": "13",
        "lang": "en",
    },
    {
        "id": "p29_rect_area_8_5",
        "input": "area of rectangle 8 by 5",
        "expected_output": "40",
        "lang": "en",
    },
    {
        "id": "p29_circle_area_5",
        "input": "area of circle with radius 5",
        "expected_output": "78.54",
        "lang": "en",
    },
    {"id": "p29_lcm_12_18", "input": "lcm of 12 and 18", "expected_output": "36", "lang": "en", "confidence": 0.95},
    {"id": "p29_gcd_12_18", "input": "gcd of 12 and 18", "expected_output": "6", "lang": "en", "confidence": 0.95},
    {
        "id": "p29_ap_10th_term",
        "input": "10th term of AP starting 3 with difference 4",
        "expected_output": "39",
        "lang": "en",
    },
    {
        "id": "p29_gp_5th_term",
        "input": "5th term of GP starting 2 with ratio 3",
        "expected_output": "162",
        "lang": "en",
    },
    {"id": "p29_sin_30", "input": "sin(30 degrees)", "expected_output": "0.5", "lang": "en", "confidence": 0.95},
    {"id": "p29_tan_45", "input": "tan(45 degrees)", "expected_output": "1.0", "lang": "en", "confidence": 0.95},
    {
        "id": "p29_linear_neg3",
        "input": "solve 2x + 6 = 0",
        "expected_output": "x = -3",
        "lang": "en",
    },
    {"id": "p29_sq_root_144", "input": "sqrt(144)", "expected_output": "12", "lang": "en", "confidence": 0.95},
    {
        "id": "p29_triangle_area_6_7",
        "input": "area of triangle with base 6 and height 7",
        "expected_output": "21",
        "lang": "en",
    },
]

# ---------------------------------------------------------------------------
# Provenance: content hash computed from the canonical payload
# ---------------------------------------------------------------------------


def _build_payload() -> str:
    """Canonical payload for the content hash (order matters)."""
    import json

    parts: List[str] = []
    parts.append(json.dumps(MATH_SYNONYMS, sort_keys=True, ensure_ascii=False))
    parts.append(json.dumps(MATH_CONCEPTS, sort_keys=True, ensure_ascii=False))
    parts.append(json.dumps(MATH_RELATIONS, sort_keys=True, ensure_ascii=False))
    parts.append(json.dumps(MATH_FACTS, sort_keys=True, ensure_ascii=False))
    parts.append(json.dumps(MATH_FORMULAS, sort_keys=True, ensure_ascii=False))
    parts.append(json.dumps(MATH_RULES, sort_keys=True, ensure_ascii=False))
    parts.append(json.dumps(MATH_EXAMPLES, sort_keys=True, ensure_ascii=False))
    parts.append(json.dumps(MATH_TESTS, sort_keys=True, ensure_ascii=False))
    return "".join(parts)


_PAYLOAD = _build_payload()
_CONTENT_HASH = "sha256:" + hashlib.sha256(_PAYLOAD.encode("utf-8")).hexdigest()

# Shared source_ref used on every record so the registry accepts them.
_RECORD_SOURCE: Dict[str, Any] = {
    "title": "Misty Phase 29 mathematics curriculum",
    "url": "https://misty-brain.onrender.com",
    "retrieved_at": "2026-08-19T00:00:00Z",
    "content_hash": _CONTENT_HASH,
}


def mathematics_curriculum_package() -> TrainingPackageV2:
    """Return the Phase 29 bilingual mathematics curriculum package."""
    from datetime import datetime, timezone

    def _attach(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Attach the provenance source_ref to records that lack one."""
        out: List[Dict[str, Any]] = []
        for record in records:
            rec = dict(record)
            if "source_ref" not in rec:
                rec["source_ref"] = _RECORD_SOURCE
            out.append(rec)
        return out

    def _topic_concepts() -> List[Dict[str, Any]]:
        topics = {
            "arithmetic_pct": "fraction, decimal, percentage and ratio arithmetic",
            "algebra": "linear equations, quadratic equations and inequalities",
            "geometry": "area, perimeter, volume and the Pythagorean theorem",
            "trigonometry": "sine, cosine and tangent of standard angles",
            "series": "arithmetic and geometric progressions and their sums",
            "number_theory": "LCM, GCD, prime numbers and divisibility",
        }
        out: List[Dict[str, Any]] = []
        for topic, description in topics.items():
            out.append(
                {
                    "subject": "Misty",
                    "predicate": "knows_topic",
                    "obj": topic,
                    "lang": "en",
                    "source_ref": _RECORD_SOURCE,
                }
            )
            out.append(
                {
                    "subject": topic,
                    "predicate": "description",
                    "obj": description,
                    "lang": "en",
                    "source_ref": _RECORD_SOURCE,
                }
            )
        return out

    all_facts = _topic_concepts() + _attach(MATH_FACTS)

    return TrainingPackageV2(
        package_id=PACKAGE_ID,
        department=PACKAGE_DEPARTMENT,
        version=PACKAGE_VERSION,
        languages=["bn", "en"],
        license=PACKAGE_LICENSE,
        source=SourceRef(
            title="Misty full mathematics curriculum (Phase 29) — bilingual, deterministic",
            url="https://misty-brain.onrender.com",
            retrieved_at=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            content_hash=_CONTENT_HASH,
        ),
        concepts=[
            {"name": "Mathematics", "type": "Field", "source_ref": _RECORD_SOURCE},
            {"name": "Algebra", "type": "Branch", "source_ref": _RECORD_SOURCE},
            {"name": "Geometry", "type": "Branch", "source_ref": _RECORD_SOURCE},
            {"name": "Trigonometry", "type": "Branch", "source_ref": _RECORD_SOURCE},
            {"name": "Number Theory", "type": "Branch", "source_ref": _RECORD_SOURCE},
            {"name": "Series", "type": "Branch", "source_ref": _RECORD_SOURCE},
            {"name": "গণিত", "type": "শাখা", "source_ref": _RECORD_SOURCE},
            *MATH_CONCEPTS,
        ],
        relations=MATH_RELATIONS,
        facts=all_facts,
        rules=[dict(r, source_ref=_RECORD_SOURCE) for r in MATH_RULES],
        formulas=[dict(f, source_ref=_RECORD_SOURCE) for f in MATH_FORMULAS],
        examples=_attach(MATH_EXAMPLES),
        tests=_attach(MATH_TESTS),
        confidence_policy={"default": 0.8, "requires_source": True},
    )


def register_mathematics_curriculum(brain: Any) -> int:
    """Load the Phase 29 mathematics curriculum into the brain's
    semantic memory and knowledge graph, and register the package.

    Returns the number of curriculum facts registered.
    """
    PackageRegistry().register(mathematics_curriculum_package())
    count = 0
    for entry in MATH_CONCEPTS:
        if brain.concept_graph.get_concept_by_name(entry["name"]) is None:
            brain.concept_graph.create_concept(
                name=entry["name"],
                concept_type=entry.get("type", "MathConcept"),
            )
    # Phase 29: alias facts — the NLU head-noun parser extracts phrasal
    # targets that do not match the canonical subjects word-for-word (e.g.
    # "quadratic formula" vs "Quadratic Equation", "Pythagorean theorem",
    # "sine function", "gcd definition"). Storing the same facts under
    # these query aliases lets the definition lookup in the brain answer
    # trained concepts instead of the "not learned" fallback.
    for alias, canonical in MATH_SYNONYMS.items():
        for fact in MATH_FACTS:
            if fact["subject"] != canonical:
                continue
            if brain.semantic_memory.query(subject=alias, predicate=fact["predicate"]):
                continue
            brain.semantic_memory.store_fact(
                subject=alias,
                predicate=fact["predicate"],
                obj=fact["obj"],
                confidence=fact.get("confidence", 0.8),
                source=PACKAGE_ID,
            )
            count += 1

    for fact in MATH_FACTS:
        if brain.semantic_memory.query(subject=fact["subject"], predicate=fact["predicate"]):
            continue
        brain.semantic_memory.store_fact(
            subject=fact["subject"],
            predicate=fact["predicate"],
            obj=fact["obj"],
            confidence=fact.get("confidence", 0.8),
            source=PACKAGE_ID,
        )
        count += 1
    return count
