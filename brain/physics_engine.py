"""LLM-independent deterministic Physics reasoning for MISTY.

This first module covers safe, explicit formulas for units, kinematics,
Newtonian mechanics, work, energy, power, momentum, and gravitation. It does
not guess unsupported problems; it returns a bounded explanation instead.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import ClassVar


@dataclass(frozen=True)
class PhysicsResult:
    answer: str
    exact: str
    category: str
    steps: tuple[str, ...] = ()
    confidence: float = 0.96


class PhysicsEngine:
    """Deterministic introductory Physics solver with Bengali terminology."""

    _markers: ClassVar[tuple[str, ...]] = (
        "physics",
        "velocity",
        "speed",
        "distance",
        "time",
        "acceleration",
        "বেগ",
        "দ্রুতি",
        "দূরত্ব",
        "সময়",
        "সময়",
        "ত্বরণ",
        "force",
        "বল",
        "mass",
        "ভর",
        "work",
        "কাজ",
        "energy",
        "শক্তি",
        "power",
        "ক্ষমতা",
        "momentum",
        "ভরবেগ",
        "gravity",
        "মহাকর্ষ",
        "g =",
        "newton",
    )

    @classmethod
    def _has_marker(cls, text: str, marker: str) -> bool:
        """Match a physics term as a token, not as a substring."""
        if marker == "g =":
            return marker in text
        escaped = re.escape(marker)
        return re.search(rf"(?<![\w\u0980-\u09FF]){escaped}(?![\w\u0980-\u09FF])", text) is not None

    def solve(self, text: str) -> PhysicsResult | None:
        lowered = text.lower().strip()
        if not any(self._has_marker(lowered, marker) for marker in self._markers):
            return None
        numbers = [float(value) for value in re.findall(r"-?\d+(?:\.\d+)?", lowered)]
        if not numbers:
            return PhysicsResult(
                "এই Physics প্রশ্নের জন্য সংখ্যাগত মান দিন। উদাহরণ: velocity = distance / time, distance 100 m, time 20 s",
                "missing_values",
                "physics_help",
                confidence=0.45,
            )

        if (
            any(self._has_marker(lowered, marker) for marker in ("velocity", "বেগ", "speed", "দ্রুতি"))
            and len(numbers) >= 2
        ):
            distance, duration = numbers[:2]
            if duration == 0:
                return PhysicsResult("সময় শূন্য হলে বেগ নির্ণয় করা যায় না।", "undefined", "kinematics", confidence=0.7)
            value = distance / duration
            return PhysicsResult(
                f"velocity = {value:g} m/s",
                f"v = {value:g} m/s",
                "kinematics",
                ("v = distance / time", f"v = {distance:g} / {duration:g}", f"v = {value:g} m/s"),
            )

        if any(self._has_marker(lowered, marker) for marker in ("force", "বল", "newton")) and len(numbers) >= 2:
            mass, acceleration = numbers[:2]
            value = mass * acceleration
            return PhysicsResult(
                f"force = {value:g} N",
                f"F = {value:g} N",
                "mechanics",
                ("F = m x a", f"F = {mass:g} x {acceleration:g}", f"F = {value:g} N"),
            )

        if any(self._has_marker(lowered, marker) for marker in ("work", "কাজ")) and len(numbers) >= 2:
            force, displacement = numbers[:2]
            value = force * displacement
            return PhysicsResult(
                f"work = {value:g} J",
                f"W = {value:g} J",
                "energy",
                ("W = F x s", f"W = {force:g} x {displacement:g}", f"W = {value:g} J"),
            )

        if any(self._has_marker(lowered, marker) for marker in ("kinetic", "গতিশক্তি")) and len(numbers) >= 2:
            mass, velocity = numbers[:2]
            value = 0.5 * mass * velocity**2
            return PhysicsResult(
                f"kinetic energy = {value:g} J",
                f"K = {value:g} J",
                "energy",
                ("K = ½mv²", f"K = ½ x {mass:g} x {velocity:g}²", f"K = {value:g} J"),
            )

        if any(self._has_marker(lowered, marker) for marker in ("momentum", "ভরবেগ")) and len(numbers) >= 2:
            mass, velocity = numbers[:2]
            value = mass * velocity
            return PhysicsResult(
                f"momentum = {value:g} kg·m/s",
                f"p = {value:g} kg·m/s",
                "mechanics",
                ("p = m x v", f"p = {mass:g} x {velocity:g}", f"p = {value:g} kg·m/s"),
            )

        if (
            any(self._has_marker(lowered, marker) for marker in ("potential", "বিভবশক্তি", "gravitational"))
            and len(numbers) >= 2
        ):
            mass, height = numbers[:2]
            g = numbers[2] if len(numbers) >= 3 else 9.8
            value = mass * g * height
            return PhysicsResult(
                f"gravitational potential energy = {value:g} J",
                f"U = {value:g} J",
                "gravitation",
                ("U = mgh", f"U = {mass:g} x {g:g} x {height:g}", f"U = {value:g} J"),
            )

        return PhysicsResult(
            "এই Physics format-এর জন্য এখনো নির্দিষ্ট solver নেই। বর্তমানে velocity, force, work, "
            "kinetic energy, momentum ও gravitational potential energy সমর্থিত।",
            "unsupported",
            "physics_help",
            confidence=0.4,
        )


PHYSICS_ENGINE = PhysicsEngine()

PHYSICS_CONCEPTS = [
    {"name": name, "type": "Physics"}
    for name in (
        "Physics",
        "Measurement",
        "Units",
        "Vectors",
        "Kinematics",
        "Newtonian Mechanics",
        "Force",
        "Work",
        "Energy",
        "Power",
        "Momentum",
        "Gravitation",
        "Fluids",
        "Thermodynamics",
        "Waves",
        "Sound",
        "Optics",
        "Electromagnetism",
        "Relativity",
        "Quantum Physics",
        "Astrophysics",
    )
]

PHYSICS_RELATIONS = [
    {"source": "Physics", "target": item["name"], "type": "includes"}
    for item in PHYSICS_CONCEPTS
    if item["name"] != "Physics"
]

PHYSICS_FACTS = [
    {"subject": "Physics", "predicate": "studies", "obj": "matter, energy, motion, forces, space, and time"},
    {"subject": "Kinematics", "predicate": "uses", "obj": "distance, displacement, speed, velocity, and acceleration"},
    {"subject": "Newtonian Mechanics", "predicate": "uses", "obj": "F = ma and laws of motion"},
    {"subject": "Work", "predicate": "formula", "obj": "W = F x s"},
    {"subject": "Kinetic Energy", "predicate": "formula", "obj": "K = ½mv²"},
    {"subject": "Momentum", "predicate": "formula", "obj": "p = mv"},
    {
        "subject": "Gravitational Potential Energy",
        "predicate": "formula",
        "obj": "U = mgh near Earth's surface",
    },
    {
        "subject": "Misty",
        "predicate": "has_capability",
        "obj": "deterministic introductory Physics reasoning without an LLM",
    },
]


def physics_package() -> tuple[list[dict[str, str]], list[dict[str, str]], list[dict[str, str]]]:
    return PHYSICS_CONCEPTS, PHYSICS_RELATIONS, PHYSICS_FACTS


__all__ = ["PHYSICS_ENGINE", "PhysicsEngine", "PhysicsResult", "physics_package"]
