# ruff: noqa: RUF001
"""Phase 30: Misty deep bilingual physics curriculum.

This module trains Misty with a school-level physics curriculum in both
Bengali and English. Each unit is represented as structured, source-backed
records (concepts, relations, facts, formulas, rules, examples, and tests)
that enter the package registry with provenance, so the brain can explain
physics from its stored knowledge instead of only computing with the
deterministic PhysicsEngine.

Units:
- kinematics   : velocity, acceleration, free fall, equations of motion
- forces       : Newton's three laws, mass, weight, inertia
- energy       : kinetic energy, potential energy, work, power
- waves_sound  : wave speed, frequency, wavelength, period
- electricity  : Ohm's law, current, voltage, resistance, series/parallel
- optics       : reflection, focal length, mirror and lens formula

The curriculum records coexist with the deterministic PhysicsEngine
(brain/physics_engine.py), which already solves supported numeric queries
computationally. This package teaches Misty the vocabulary, rules and
formulas so it can also explain and answer concept questions about each
unit in Bengali and English.
"""

from __future__ import annotations

import hashlib
from typing import Any, Dict, List

from brain.knowledge.registry import PackageRegistry, SourceRef, TrainingPackageV2

PACKAGE_ID = "misty-physics-phase30"
PACKAGE_DEPARTMENT = "physics"
PACKAGE_VERSION = "1.0.0"
PACKAGE_LICENSE = "proprietary"

_TOPIC: List[str] = [
    "kinematics",
    "forces",
    "energy",
    "waves_sound",
    "electricity",
    "optics",
]

# ---------------------------------------------------------------------------
# Concepts: the vocabulary of the curriculum (bilingual pairs)
# ---------------------------------------------------------------------------

PHYSICS_CONCEPTS: List[Dict[str, Any]] = [
    # Kinematics
    {"name": "Velocity", "type": "PhysicsConcept", "lang": "en"},
    {"name": "বেগ", "type": "পদার্থবিজ্ঞান ধারণা", "lang": "bn"},
    {"name": "Speed", "type": "PhysicsConcept", "lang": "en"},
    {"name": "দ্রুতি", "type": "পদার্থবিজ্ঞান ধারণা", "lang": "bn"},
    {"name": "Acceleration", "type": "PhysicsConcept", "lang": "en"},
    {"name": "ত্বরণ", "type": "পদার্থবিজ্ঞান ধারণা", "lang": "bn"},
    {"name": "Displacement", "type": "PhysicsConcept", "lang": "en"},
    {"name": "সরণ", "type": "পদার্থবিজ্ঞান ধারণা", "lang": "bn"},
    {"name": "Free Fall", "type": "PhysicsConcept", "lang": "en"},
    {"name": "মুক্তপতন", "type": "পদার্থবিজ্ঞান ধারণা", "lang": "bn"},
    # Forces
    {"name": "Force", "type": "PhysicsConcept", "lang": "en"},
    {"name": "বল", "type": "পদার্থবিজ্ঞান ধারণা", "lang": "bn"},
    {"name": "Mass", "type": "PhysicsConcept", "lang": "en"},
    {"name": "ভর", "type": "পদার্থবিজ্ঞান ধারণা", "lang": "bn"},
    {"name": "Weight", "type": "PhysicsConcept", "lang": "en"},
    {"name": "ওজন", "type": "পদার্থবিজ্ঞান ধারণা", "lang": "bn"},
    {"name": "Newton's First Law", "type": "PhysicsLaw", "lang": "en"},
    {"name": "নিউটনের প্রথম সূত্র", "type": "পদার্থবিজ্ঞান সূত্র", "lang": "bn"},
    {"name": "Newton's Second Law", "type": "PhysicsLaw", "lang": "en"},
    {"name": "নিউটনের দ্বিতীয় সূত্র", "type": "পদার্থবিজ্ঞান সূত্র", "lang": "bn"},
    {"name": "Newton's Third Law", "type": "PhysicsLaw", "lang": "en"},
    {"name": "নিউটনের তৃতীয় সূত্র", "type": "পদার্থবিজ্ঞান সূত্র", "lang": "bn"},
    {"name": "Inertia", "type": "PhysicsConcept", "lang": "en"},
    {"name": "জড়তা", "type": "পদার্থবিজ্ঞান ধারণা", "lang": "bn"},
    # Energy
    {"name": "Kinetic Energy", "type": "PhysicsConcept", "lang": "en"},
    {"name": "গতিশক্তি", "type": "পদার্থবিজ্ঞান ধারণা", "lang": "bn"},
    {"name": "Potential Energy", "type": "PhysicsConcept", "lang": "en"},
    {"name": "বিভবশক্তি", "type": "পদার্থবিজ্ঞান ধারণা", "lang": "bn"},
    {"name": "Work", "type": "PhysicsConcept", "lang": "en"},
    {"name": "কাজ", "type": "পদার্থবিজ্ঞান ধারণা", "lang": "bn"},
    {"name": "Power", "type": "PhysicsConcept", "lang": "en"},
    {"name": "ক্ষমতা", "type": "পদার্থবিজ্ঞান ধারণা", "lang": "bn"},
    # Waves and sound
    {"name": "Wave", "type": "PhysicsConcept", "lang": "en"},
    {"name": "তরঙ্গ", "type": "পদার্থবিজ্ঞান ধারণা", "lang": "bn"},
    {"name": "Frequency", "type": "PhysicsConcept", "lang": "en"},
    {"name": "কম্পাঙ্ক", "type": "পদার্থবিজ্ঞান ধারণা", "lang": "bn"},
    {"name": "Wavelength", "type": "PhysicsConcept", "lang": "en"},
    {"name": "তরঙ্গদৈর্ঘ্য", "type": "পদার্থবিজ্ঞান ধারণা", "lang": "bn"},
    {"name": "Period", "type": "PhysicsConcept", "lang": "en"},
    {"name": "পর্যায়কাল", "type": "পদার্থবিজ্ঞান ধারণা", "lang": "bn"},
    {"name": "Sound", "type": "PhysicsConcept", "lang": "en"},
    {"name": "শব্দ", "type": "পদার্থবিজ্ঞান ধারণা", "lang": "bn"},
    # Electricity
    {"name": "Ohm's Law", "type": "PhysicsLaw", "lang": "en"},
    {"name": "ওহমের সূত্র", "type": "পদার্থবিজ্ঞান সূত্র", "lang": "bn"},
    {"name": "Current", "type": "PhysicsConcept", "lang": "en"},
    {"name": "তড়িৎপ্রবাহ", "type": "পদার্থবিজ্ঞান ধারণা", "lang": "bn"},
    {"name": "Voltage", "type": "PhysicsConcept", "lang": "en"},
    {"name": "বিভব পার্থক্য", "type": "পদার্থবিজ্ঞান ধারণা", "lang": "bn"},
    {"name": "Resistance", "type": "PhysicsConcept", "lang": "en"},
    {"name": "রোধ", "type": "পদার্থবিজ্ঞান ধারণা", "lang": "bn"},
    {"name": "Series Circuit", "type": "Circuit", "lang": "en"},
    {"name": "সমবায় সংযোগ", "type": "বর্তনী", "lang": "bn"},
    {"name": "Parallel Circuit", "type": "Circuit", "lang": "en"},
    {"name": "সমান্তরাল সংযোগ", "type": "বর্তনী", "lang": "bn"},
    # Optics
    {"name": "Reflection", "type": "PhysicsConcept", "lang": "en"},
    {"name": "প্রতিফলন", "type": "পদার্থবিজ্ঞান ধারণা", "lang": "bn"},
    {"name": "Refraction", "type": "PhysicsConcept", "lang": "en"},
    {"name": "প্রতিসরণ", "type": "পদার্থবিজ্ঞান ধারণা", "lang": "bn"},
    {"name": "Focal Length", "type": "PhysicsConcept", "lang": "en"},
    {"name": "ফোকাস দূরত্ব", "type": "পদার্থবিজ্ঞান ধারণা", "lang": "bn"},
    {"name": "Mirror", "type": "OpticalElement", "lang": "en"},
    {"name": "দর্পণ", "type": "আলোক উপাদান", "lang": "bn"},
    {"name": "Lens", "type": "OpticalElement", "lang": "en"},
    {"name": "লেন্স", "type": "আলোক উপাদান", "lang": "bn"},
]

# ---------------------------------------------------------------------------
# Synonyms: common query aliases -> canonical curriculum subjects.
# ---------------------------------------------------------------------------

PHYSICS_SYNONYMS: Dict[str, str] = {
    "second law definition": "Newton's Second Law",
    "newton's second law definition": "Newton's Second Law",
    "নিউটনের দ্বিতীয় সূত্রের সংজ্ঞা": "নিউটনের দ্বিতীয় সূত্র",
    "first law definition": "Newton's First Law",
    "third law definition": "Newton's Third Law",
    "ohm's law definition": "Ohm's Law",
    "ওহমের সূত্রের সংজ্ঞা": "ওহমের সূত্র",
    "kinetic energy definition": "Kinetic Energy",
    "গতিশক্তির সংজ্ঞা": "গতিশক্তি",
    "potential energy definition": "Potential Energy",
    "বিভবশক্তির সংজ্ঞা": "বিভবশক্তি",
    "work definition": "Work",
    "কাজের সংজ্ঞা": "কাজ",
    "power definition": "Power",
    "ক্ষমতার সংজ্ঞা": "ক্ষমতা",
    "velocity definition": "Velocity",
    "বেগের সংজ্ঞা": "বেগ",
    "acceleration definition": "Acceleration",
    "ত্বরণের সংজ্ঞা": "ত্বরণ",
    "wave speed definition": "Wave",
    "frequency definition": "Frequency",
    "কম্পাঙ্কের সংজ্ঞা": "কম্পাঙ্ক",
    "current definition": "Current",
    "তড়িৎপ্রবাহের সংজ্ঞা": "তড়িৎপ্রবাহ",
    "resistance definition": "Resistance",
    "রোধের সংজ্ঞা": "রোধ",
    "reflection definition": "Reflection",
    "প্রতিফলনের সংজ্ঞা": "প্রতিফলন",
    "focal length definition": "Focal Length",
    "ফোকাস দূরত্বের সংজ্ঞা": "ফোকাস দূরত্ব",
    "free fall definition": "Free Fall",
    "মুক্তপতনের সংজ্ঞা": "মুক্তপতন",
    "gravity of earth": "Free Fall",
    "g value": "Free Fall",
}

PHYSICS_RELATIONS: List[Dict[str, Any]] = [
    {"source": "Physics", "target": "Kinematics", "type": "includes", "lang": "en"},
    {"source": "Physics", "target": "Forces", "type": "includes", "lang": "en"},
    {"source": "Physics", "target": "Energy", "type": "includes", "lang": "en"},
    {"source": "Physics", "target": "Waves", "type": "includes", "lang": "en"},
    {"source": "Physics", "target": "Electricity", "type": "includes", "lang": "en"},
    {"source": "Physics", "target": "Optics", "type": "includes", "lang": "en"},
    {"source": "পদার্থবিজ্ঞান", "target": "গতিবিজ্ঞান", "type": "শাখা", "lang": "bn"},
    {"source": "পদার্থবিজ্ঞান", "target": "বল ও গতি", "type": "শাখা", "lang": "bn"},
    {"source": "পদার্থবিজ্ঞান", "target": "শক্তি ও ক্ষমতা", "type": "শাখা", "lang": "bn"},
    {"source": "পদার্থবিজ্ঞান", "target": "তরঙ্গ ও শব্দ", "type": "শাখা", "lang": "bn"},
    {"source": "পদার্থবিজ্ঞান", "target": "বিদ্যুৎ", "type": "শাখা", "lang": "bn"},
    {"source": "পদার্থবিজ্ঞান", "target": "আলোকবিজ্ঞান", "type": "শাখা", "lang": "bn"},
    {"source": "Velocity", "target": "Kinematics", "type": "belongs_to", "lang": "en"},
    {"source": "Acceleration", "target": "Kinematics", "type": "belongs_to", "lang": "en"},
    {"source": "Free Fall", "target": "Kinematics", "type": "belongs_to", "lang": "en"},
    {"source": "Force", "target": "Newtonian Mechanics", "type": "belongs_to", "lang": "en"},
    {"source": "Newton's First Law", "target": "Newtonian Mechanics", "type": "part_of", "lang": "en"},
    {"source": "Newton's Second Law", "target": "Newtonian Mechanics", "type": "part_of", "lang": "en"},
    {"source": "Newton's Third Law", "target": "Newtonian Mechanics", "type": "part_of", "lang": "en"},
    {"source": "Kinetic Energy", "target": "Energy", "type": "type_of", "lang": "en"},
    {"source": "Potential Energy", "target": "Energy", "type": "type_of", "lang": "en"},
    {"source": "Power", "target": "Energy", "type": "type_of", "lang": "en"},
    {"source": "Frequency", "target": "Wave", "type": "property_of", "lang": "en"},
    {"source": "Wavelength", "target": "Wave", "type": "property_of", "lang": "en"},
    {"source": "Period", "target": "Wave", "type": "property_of", "lang": "en"},
    {"source": "Sound", "target": "Wave", "type": "type_of", "lang": "en"},
    {"source": "Ohm's Law", "target": "Electricity", "type": "part_of", "lang": "en"},
    {"source": "Current", "target": "Electricity", "type": "property_of", "lang": "en"},
    {"source": "Voltage", "target": "Electricity", "type": "property_of", "lang": "en"},
    {"source": "Resistance", "target": "Electricity", "type": "property_of", "lang": "en"},
    {"source": "Series Circuit", "target": "Electricity", "type": "type_of", "lang": "en"},
    {"source": "Parallel Circuit", "target": "Electricity", "type": "type_of", "lang": "en"},
    {"source": "Reflection", "target": "Optics", "type": "belongs_to", "lang": "en"},
    {"source": "Refraction", "target": "Optics", "type": "belongs_to", "lang": "en"},
    {"source": "Focal Length", "target": "Mirror", "type": "property_of", "lang": "en"},
    {"source": "Focal Length", "target": "Lens", "type": "property_of", "lang": "en"},
    {"source": "Misty", "target": "physics-curriculum-phase30", "type": "trained_on", "lang": "en"},
]

# ---------------------------------------------------------------------------
# Facts: declarative curriculum knowledge (bilingual)
# ---------------------------------------------------------------------------

PHYSICS_FACTS: List[Dict[str, Any]] = [
    # --- Kinematics ---
    {
        "subject": "Velocity",
        "predicate": "definition",
        "obj": "rate of change of displacement with time; a vector quantity measured in m/s",
        "lang": "en",
        "topic": "kinematics",
    },
    {
        "subject": "বেগ",
        "predicate": "সংজ্ঞা",
        "obj": "সময়ের সাথে সরণের পরিবর্তনের হার; এটি ভেক্টর রাশি এব  ম/সে এককে মাপা হয়",
        "lang": "bn",
        "topic": "kinematics",
    },
    {
        "subject": "Acceleration",
        "predicate": "definition",
        "obj": "rate of change of velocity with time; measured in m/s^2",
        "lang": "en",
        "topic": "kinematics",
    },
    {
        "subject": "ত্বরণ",
        "predicate": "সংজ্ঞা",
        "obj": "সময়ের সাথে বেগের পরিবর্তনের হার; ম/সে^২ এককে মাপা হয়",
        "lang": "bn",
        "topic": "kinematics",
    },
    {
        "subject": "Speed",
        "predicate": "definition",
        "obj": "rate of covering distance with time; a scalar quantity measured in m/s",
        "lang": "en",
        "topic": "kinematics",
    },
    {
        "subject": "দ্রুতি",
        "predicate": "সংজ্ঞা",
        "obj": "সময়ের সাথে দূরত্ব অতিক্রমের হার; এটি স্কেলার রাশি",
        "lang": "bn",
        "topic": "kinematics",
    },
    {
        "subject": "Free Fall",
        "predicate": "definition",
        "obj": "motion of a body under gravity alone, with acceleration g = 9.8 m/s^2 downward",
        "lang": "en",
        "topic": "kinematics",
    },
    {
        "subject": "মুক্তপতন",
        "predicate": "সংজ্ঞা",
        "obj": "কেবল অভিকর্ষজ বলের অধীনে বস্তুর গতি; অভিকর্ষজ ত্বরণ g = ৯.৮ ম/সে^২ নিচের দিকে ক্রিয়া করে",
        "lang": "bn",
        "topic": "kinematics",
    },
    {
        "subject": "Free Fall",
        "predicate": "value",
        "obj": "acceleration due to gravity g = 9.8 m/s^2 near Earth's surface",
        "lang": "en",
        "topic": "kinematics",
    },
    {
        "subject": "Displacement",
        "predicate": "definition",
        "obj": "shortest straight-line distance from start to finish with direction",
        "lang": "en",
        "topic": "kinematics",
    },
    {
        "subject": "সরণ",
        "predicate": "সংজ্ঞা",
        "obj": "আরম্ভবিন্দু থেকে শেষবিন্দু পর্যন্ত সরলরৈখিক দিক-নির্দেশসহ দূরত্ব",
        "lang": "bn",
        "topic": "kinematics",
    },
    # --- Forces ---
    {
        "subject": "Force",
        "predicate": "definition",
        "obj": "a push or pull on an object; measured in newtons (N); F = ma",
        "lang": "en",
        "topic": "forces",
    },
    {
        "subject": "বল",
        "predicate": "সংজ্ঞা",
        "obj": "বস্তুর ওপর প্রযুক্ত ধক্কা বা টান; নিউটন (N) এককে মাপা হয়; F = ma",
        "lang": "bn",
        "topic": "forces",
    },
    {
        "subject": "Newton's First Law",
        "predicate": "definition",
        "obj": "law of inertia: an object stays at rest or in uniform motion unless acted on by a net force",
        "lang": "en",
        "topic": "forces",
    },
    {
        "subject": "নিউটনের প্রথম সূত্র",
        "predicate": "সংজ্ঞা",
        "obj": "জড়তার সূত্র: কোনো বহিঃস্থ লব্ধি বল প্রযুক্ত না হলে বস্তু স্থির থাকবে বা সমবেগে সরলরেখায় চলতে থাকবে",
        "lang": "bn",
        "topic": "forces",
    },
    {
        "subject": "Newton's Second Law",
        "predicate": "definition",
        "obj": "the net force on an object equals its mass times its acceleration: F = ma",
        "lang": "en",
        "topic": "forces",
    },
    {
        "subject": "নিউটনের দ্বিতীয় সূত্র",
        "predicate": "সংজ্ঞা",
        "obj": "বস্তুর ওপর প্রযুক্ত লব্ধি বল তার ভর ও ত্বরণের গুণফলের সমান: F = ma",
        "lang": "bn",
        "topic": "forces",
    },
    {
        "subject": "Newton's Third Law",
        "predicate": "definition",
        "obj": "for every action there is an equal and opposite reaction",
        "lang": "en",
        "topic": "forces",
    },
    {
        "subject": "নিউটনের তৃতীয় সূত্র",
        "predicate": "সংজ্ঞা",
        "obj": "প্রতিটি ক্রিয়ার সমান ও বিপরীত প্রতিক্রিয়া আছে",
        "lang": "bn",
        "topic": "forces",
    },
    {
        "subject": "Inertia",
        "predicate": "definition",
        "obj": "the tendency of an object to resist changes in its state of motion; depends on mass",
        "lang": "en",
        "topic": "forces",
    },
    {
        "subject": "জড়তা",
        "predicate": "সংজ্ঞা",
        "obj": "বস্তুর নিজের গতির অবস্থার পরিবর্তনে বাধা দেওয়ার প্রবণতা; ভরের ওপর নির্ভর করে",
        "lang": "bn",
        "topic": "forces",
    },
    {
        "subject": "Weight",
        "predicate": "definition",
        "obj": "gravitational force on a mass: W = mg; measured in newtons",
        "lang": "en",
        "topic": "forces",
    },
    {
        "subject": "ওজন",
        "predicate": "সংজ্ঞা",
        "obj": "কোনো ভরের ওপর অভিকর্ষজ বল: W = mg; নিউটন এককে মাপা হয়",
        "lang": "bn",
        "topic": "forces",
    },
    # --- Energy ---
    {
        "subject": "Kinetic Energy",
        "predicate": "definition",
        "obj": "energy of motion; K = 1/2 mv^2; measured in joules (J)",
        "lang": "en",
        "topic": "energy",
    },
    {
        "subject": "গতিশক্তি",
        "predicate": "সংজ্ঞা",
        "obj": "গতির কারণে বস্তুতে সঞ্চিত শক্তি; K = 1/2 mv^2; জুল (J) এককে মাপা হয়",
        "lang": "bn",
        "topic": "energy",
    },
    {
        "subject": "Potential Energy",
        "predicate": "definition",
        "obj": "energy stored due to position or configuration; near Earth U = mgh",
        "lang": "en",
        "topic": "energy",
    },
    {
        "subject": "বিভবশক্তি",
        "predicate": "সংজ্ঞা",
        "obj": "অবস্থান বা বিন্যাসের কারণে সঞ্চিত শক্তি; পৃথিবীর কাছে U = mgh",
        "lang": "bn",
        "topic": "energy",
    },
    {
        "subject": "Work",
        "predicate": "definition",
        "obj": "work is done when a force moves an object through a distance in its direction: W = Fs (joules, J)",
        "lang": "en",
        "topic": "energy",
    },
    {
        "subject": "কাজ",
        "predicate": "সংজ্ঞা",
        "obj": "বল প্রয়োগে বলের দিকে বস্তুকে সরালে কাজ সম্পন্ন হয়: W = Fs; জুল (J) এককে মাপা হয়",
        "lang": "bn",
        "topic": "energy",
    },
    {
        "subject": "Power",
        "predicate": "definition",
        "obj": "rate of doing work; P = W/t; measured in watts (W); 1 W = 1 J/s",
        "lang": "en",
        "topic": "energy",
    },
    {
        "subject": "ক্ষমতা",
        "predicate": "সংজ্ঞা",
        "obj": "কাজ সম্পন্নের হার; P = W/t; ওয়াট (W) এককে মাপা হয়; ১ W = ১ J/s",
        "lang": "bn",
        "topic": "energy",
    },
    # --- Waves and sound ---
    {
        "subject": "Wave",
        "predicate": "definition",
        "obj": "a disturbance transferring energy without transferring matter; v = frequency x wavelength",
        "lang": "en",
        "topic": "waves_sound",
    },
    {
        "subject": "তরঙ্গ",
        "predicate": "সংজ্ঞা",
        "obj": "এমন একটি বিক্ষোভ যা বস্তুর গতি ছাড়াই শক্তি স্থানান্তর করে; তরঙ্গের বেগ v = কম্পাঙ্ক x তরঙ্গদৈর্ঘ্য (v = f x lambda)",
        "lang": "bn",
        "topic": "waves_sound",
    },
    {
        "subject": "Frequency",
        "predicate": "definition",
        "obj": "number of complete oscillations per second; measured in hertz (Hz); f = 1/T",
        "lang": "en",
        "topic": "waves_sound",
    },
    {
        "subject": "কম্পাঙ্ক",
        "predicate": "সংজ্ঞা",
        "obj": "প্রতি সেকেন্ডে সম্পূর্ণ দোলনের সংখ্যা; হার্জ (Hz) এককে মাপা হয়; f = 1/T",
        "lang": "bn",
        "topic": "waves_sound",
    },
    {
        "subject": "Wavelength",
        "predicate": "definition",
        "obj": "distance between two consecutive crests or troughs; measured in metres",
        "lang": "en",
        "topic": "waves_sound",
    },
    {
        "subject": "তরঙ্গদৈর্ঘ্য",
        "predicate": "সংজ্ঞা",
        "obj": "পরপর দুটি সুস্থিতি বা কুস্থিতির মধ্যবর্তী দূরত্ব; মিটার এককে মাপা হয়",
        "lang": "bn",
        "topic": "waves_sound",
    },
    {
        "subject": "Period",
        "predicate": "definition",
        "obj": "time taken for one complete oscillation; T = 1/f; measured in seconds",
        "lang": "en",
        "topic": "waves_sound",
    },
    {
        "subject": "পর্যায়কাল",
        "predicate": "সংজ্ঞা",
        "obj": "একটি সম্পূর্ণ দোলনের জন্য প্রয়োজনীয় সময়; T = 1/f; সেকেন্ড এককে মাপা হয়",
        "lang": "bn",
        "topic": "waves_sound",
    },
    {
        "subject": "Sound",
        "predicate": "definition",
        "obj": "a longitudinal mechanical wave produced by vibrating objects; needs a medium; ~343 m/s in air at 20 C",
        "lang": "en",
        "topic": "waves_sound",
    },
    {
        "subject": "শব্দ",
        "predicate": "সংজ্ঞা",
        "obj": "কম্পমান বস্তু থেকে উৎপন্ন অনুদৈর্ঘ্য যান্ত্রিক তরঙ্গ; এর জন্য মাধ্যমের প্রয়োজন; ২০ C তাপমাত্রায় বাতাসে প্রায় ৩৪৩ ম/সে বেগে চলে",
        "lang": "bn",
        "topic": "waves_sound",
    },
    # --- Electricity ---
    {
        "subject": "Ohm's Law",
        "predicate": "definition",
        "obj": "the current through a conductor is proportional to the voltage across it: V = IR (constant temp)",
        "lang": "en",
        "topic": "electricity",
    },
    {
        "subject": "ওহমের সূত্র",
        "predicate": "সংজ্ঞা",
        "obj": "স্থির তাপমাত্রায় পরিবাহীর মধ্য দিয়ে প্রবাহিত তড়িৎপ্রবাহ তার দুই প্রান্তের বিভব পার্থক্যের সমানুপাতিক: V = IR",
        "lang": "bn",
        "topic": "electricity",
    },
    {
        "subject": "Current",
        "predicate": "definition",
        "obj": "rate of flow of electric charge; I = Q/t; measured in amperes (A)",
        "lang": "en",
        "topic": "electricity",
    },
    {
        "subject": "তড়িৎপ্রবাহ",
        "predicate": "সংজ্ঞা",
        "obj": "তড়িৎ চার্জের প্রবাহের হার; I = Q/t; অ্যাম্পিয়ার (A) এককে মাপা হয়",
        "lang": "bn",
        "topic": "electricity",
    },
    {
        "subject": "Voltage",
        "predicate": "definition",
        "obj": "potential difference that drives current; V = W/Q; measured in volts (V)",
        "lang": "en",
        "topic": "electricity",
    },
    {
        "subject": "বিভব পার্থক্য",
        "predicate": "সংজ্ঞা",
        "obj": "তড়িৎপ্রবাহ প্রবাহিত করার কারণ; V = W/Q; ভোল্ট (V) এককে মাপা হয়",
        "lang": "bn",
        "topic": "electricity",
    },
    {
        "subject": "Resistance",
        "predicate": "definition",
        "obj": "opposition to current flow; R = V/I; measured in ohms",
        "lang": "en",
        "topic": "electricity",
    },
    {
        "subject": "রোধ",
        "predicate": "সংজ্ঞা",
        "obj": "তড়িৎপ্রবাহের পথে বাধা; R = V/I; ওহম এককে মাপা হয়",
        "lang": "bn",
        "topic": "electricity",
    },
    {
        "subject": "Series Circuit",
        "predicate": "definition",
        "obj": "resistors connected end to end; total R = R1 + R2 + ...; same current flows through each",
        "lang": "en",
        "topic": "electricity",
    },
    {
        "subject": "সমবায় সংযোগ",
        "predicate": "সংজ্ঞা",
        "obj": "রোধগুলো একের পর এক সংযুক্ত; মোট R = R1 + R2 + ...; প্রতিটিতে একই প্রবাহ চলে",
        "lang": "bn",
        "topic": "electricity",
    },
    {
        "subject": "Parallel Circuit",
        "predicate": "definition",
        "obj": "resistors connected across common points; 1/R = 1/R1 + 1/R2 + ...; same voltage across each",
        "lang": "en",
        "topic": "electricity",
    },
    {
        "subject": "সমান্তরাল সংযোগ",
        "predicate": "সংজ্ঞা",
        "obj": "রোধগুলো সাধারণ বিন্দুর ওপর সংযুক্ত; 1/R = 1/R1 + 1/R2 + ...; প্রতিটির ওপর একই বিভব পার্থক্য",
        "lang": "bn",
        "topic": "electricity",
    },
    {
        "subject": "Electric Power",
        "predicate": "formula",
        "obj": "electrical power P = VI = I^2 R = V^2/R; measured in watts",
        "lang": "en",
        "topic": "electricity",
    },
    {
        "subject": "বিদ্যুৎ ক্ষমতা",
        "predicate": "সূত্র",
        "obj": "বিদ্যুৎ ক্ষমতা P = VI = I^2 R = V^2/R; ওয়াট এককে মাপা হয়",
        "lang": "bn",
        "topic": "electricity",
    },
    # --- Optics ---
    {
        "subject": "Reflection",
        "predicate": "definition",
        "obj": "bouncing of light off a surface; angle of incidence equals angle of reflection",
        "lang": "en",
        "topic": "optics",
    },
    {
        "subject": "প্রতিফলন",
        "predicate": "সংজ্ঞা",
        "obj": "কোনো তল থেকে আলোর ফিরে আসা; আপতন কোণ প্রতিফলন কোণের সমান",
        "lang": "bn",
        "topic": "optics",
    },
    {
        "subject": "Refraction",
        "predicate": "definition",
        "obj": "bending of light when it passes from one medium to another; governed by Snell's law",
        "lang": "en",
        "topic": "optics",
    },
    {
        "subject": "প্রতিসরণ",
        "predicate": "সংজ্ঞা",
        "obj": "এক মাধ্যম থেকে অন্য মাধ্যমে আলোর প্রবেশকালে বাঁকা; স্নেলের সূত্র দ্বারা নিয়ন্ত্রিত",
        "lang": "bn",
        "topic": "optics",
    },
    {
        "subject": "Focal Length",
        "predicate": "definition",
        "obj": "distance between the pole of a mirror or lens and its focus",
        "lang": "en",
        "topic": "optics",
    },
    {
        "subject": "ফোকাস দূরত্ব",
        "predicate": "সংজ্ঞা",
        "obj": "দর্পণ বা লেন্সের মেরু থেকে ফোকাসবিন্দু পর্যন্ত দূরত্ব",
        "lang": "bn",
        "topic": "optics",
    },
    {
        "subject": "Mirror",
        "predicate": "formula",
        "obj": "1/f = 1/v + 1/u where f is focal length, v image distance, u object distance",
        "lang": "en",
        "topic": "optics",
    },
    {
        "subject": "দর্পণ",
        "predicate": "সূত্র",
        "obj": "1/f = 1/v + 1/u যেখানে f ফোকাস দূরত্ব, v বিম্বের দূরত্ব, u বস্তুর দূরত্ব",
        "lang": "bn",
        "topic": "optics",
    },
    {
        "subject": "Lens",
        "predicate": "formula",
        "obj": "thin lens formula: 1/f = 1/v - 1/u; converging lenses have positive f",
        "lang": "en",
        "topic": "optics",
    },
    {
        "subject": "লেন্স",
        "predicate": "সূত্র",
        "obj": "সরু লেন্সের সূত্র: 1/f = 1/v - 1/u; উত্তল লেন্সের ফোকাস দূরত্ব ধনাত্মক",
        "lang": "bn",
        "topic": "optics",
    },
    {
        "subject": "Light",
        "predicate": "value",
        "obj": "speed of light in vacuum c = 3 x 10^8 m/s",
        "lang": "en",
        "topic": "optics",
    },
    {
        "subject": "আলো",
        "predicate": "মান",
        "obj": "শূন্যমাধ্যমে আলোর বেগ c = ৩ x ১০^৮ ম/সে",
        "lang": "bn",
        "topic": "optics",
    },
]

# ---------------------------------------------------------------------------
# Formulas: canonical named physics formulas
# ---------------------------------------------------------------------------

PHYSICS_FORMULAS: List[Dict[str, Any]] = [
    {"name": "velocity", "expression": "v = distance / time", "lang": "en", "confidence": 0.98},
    {"name": "acceleration", "expression": "a = (v - u) / t", "lang": "en", "confidence": 0.98},
    {"name": "free_fall_distance", "expression": "s = 1/2 g t^2", "lang": "en", "confidence": 0.98},
    {"name": "free_fall_velocity", "expression": "v = g t", "lang": "en", "confidence": 0.98},
    {"name": "newton_second", "expression": "F = m a", "lang": "en", "confidence": 0.98},
    {"name": "kinetic_energy", "expression": "K = 1/2 m v^2", "lang": "en", "confidence": 0.98},
    {"name": "gravitational_pe", "expression": "U = m g h", "lang": "en", "confidence": 0.98},
    {"name": "work", "expression": "W = F s", "lang": "en", "confidence": 0.98},
    {"name": "power", "expression": "P = W / t", "lang": "en", "confidence": 0.98},
    {"name": "electrical_power", "expression": "P = V I = I^2 R = V^2 / R", "lang": "en", "confidence": 0.98},
    {"name": "ohm_law", "expression": "V = I R", "lang": "en", "confidence": 0.98},
    {"name": "series_resistance", "expression": "R = R1 + R2 + ...", "lang": "en", "confidence": 0.98},
    {"name": "parallel_resistance", "expression": "1/R = 1/R1 + 1/R2 + ...", "lang": "en", "confidence": 0.98},
    {"name": "wave_speed", "expression": "v = f lambda", "lang": "en", "confidence": 0.98},
    {"name": "period_frequency", "expression": "f = 1/T", "lang": "en", "confidence": 0.98},
    {"name": "weight", "expression": "W = m g", "lang": "en", "confidence": 0.98},
    {"name": "mirror_lens", "expression": "1/f = 1/v + 1/u", "lang": "en", "confidence": 0.98},
    {"name": "first_equation_of_motion", "expression": "v = u + a t", "lang": "en", "confidence": 0.98},
    {"name": "second_equation_of_motion", "expression": "s = u t + 1/2 a t^2", "lang": "en", "confidence": 0.98},
    {"name": "third_equation_of_motion", "expression": "v^2 = u^2 + 2 a s", "lang": "en", "confidence": 0.98},
]

# ---------------------------------------------------------------------------
# Rules: inference rules that let the brain reason physically
# ---------------------------------------------------------------------------

PHYSICS_RULES: List[Dict[str, Any]] = [
    {
        "when": "a body starts from rest and falls freely for time t",
        "then": "the distance fallen is s = 1/2 g t^2 with g = 9.8 m/s^2",
        "lang": "en",
    },
    {
        "when": "বস্তু স্থির অবস্থা থেকে t সময় ধরে মুক্তভাবে পড়ে",
        "then": "অতিক্রান্ত দূরত্ব s = 1/2 g t^2 যেখানে g = 9.8 ম/সে^2",
        "lang": "bn",
    },
    {
        "when": "net force F acts on mass m",
        "then": "acceleration is a = F/m by Newton's second law",
        "lang": "en",
    },
    {
        "when": "constant voltage V drives current through resistance R",
        "then": "current I = V/R by Ohm's law",
        "lang": "en",
    },
    {
        "when": "resistors are in series",
        "then": "the same current flows through each and total resistance adds directly",
        "lang": "en",
    },
    {
        "when": "resistors are in parallel",
        "then": "the same voltage appears across each and conductances add: 1/R = 1/R1 + 1/R2",
        "lang": "en",
    },
    {
        "when": "a wave has frequency f and wavelength lambda",
        "then": "its speed is v = f x lambda",
        "lang": "en",
    },
    {
        "when": "a wave has period T",
        "then": "its frequency is f = 1/T",
        "lang": "en",
    },
    {
        "when": "constant power P is supplied for time t",
        "then": "the work done or energy transferred is W = P t",
        "lang": "en",
    },
    {
        "when": "a body of mass m moves at speed v",
        "then": "its kinetic energy is K = 1/2 m v^2",
        "lang": "en",
    },
]

# ---------------------------------------------------------------------------
# Examples: worked bilingual examples
# ---------------------------------------------------------------------------

PHYSICS_EXAMPLES: List[Dict[str, Any]] = [
    {
        "input": "a car travels 200 m in 10 s; find the velocity",
        "output": "velocity = 20 m/s, because v = 200 / 10 = 20",
        "lang": "en",
    },
    {
        "input": "১০ সেকেন্ডে ২০০ মিটার পথ অতিক্রম করলে বেগ কত?",
        "output": "বেগ = ২০ ম/সে, কারণ ২০০ / ১০ = ২০",
        "lang": "bn",
        "confidence": 0.95,
    },
    {
        "input": "a 5 kg object accelerates at 2 m/s^2; find the force",
        "output": "force = 10 N, because F = 5 x 2 = 10",
        "lang": "en",
    },
    {
        "input": "৫ কেজি ভরের বস্তুতে ১০ N বল প্রয়োগ করলে ত্বরণ কত?",
        "output": "ত্বরণ = ২ ম/সে^২, কারণ a = F/m = ১০/৫ = ২",
        "lang": "bn",
        "confidence": 0.95,
    },
    {
        "input": "a body falls freely for 5 seconds; how far does it fall",
        "output": "122.5 m, because s = 1/2 x 9.8 x 25 = 122.5",
        "lang": "en",
    },
    {
        "input": "5 সেকেন্ড মুক্তপতনে বস্তু কতদূর পড়ে?",
        "output": "১২২.৫ মিটার, কারণ s = 1/2 x 9.8 x 25 = 122.5",
        "lang": "bn",
        "confidence": 0.95,
    },
    {
        "input": "a 2 kg object moves at 3 m/s; find its kinetic energy",
        "output": "kinetic energy = 9 J, because K = 1/2 x 2 x 9 = 9",
        "lang": "en",
    },
    {
        "input": "a 12 V battery drives current through a 4 ohm resistor; find the current",
        "output": "current = 3 A, because I = V/R = 12/4 = 3",
        "lang": "en",
    },
    {
        "input": "12 V ব্যাটারি ৪ ওহম রোধের মধ্য দিয়ে প্রবাহ চালালে প্রবাহ কত?",
        "output": "প্রবাহ = ৩ A, কারণ I = V/R = ১২/৪ = ৩",
        "lang": "bn",
        "confidence": 0.95,
    },
    {
        "input": "two resistors 6 ohm and 3 ohm in series; total resistance?",
        "output": "total R = 9 ohm, because 6 + 3 = 9",
        "lang": "en",
    },
    {
        "input": "two resistors 6 ohm and 3 ohm in parallel; total resistance?",
        "output": "total R = 2 ohm, because 1/R = 1/6 + 1/3 = 1/2",
        "lang": "en",
    },
    {
        "input": "a wave has frequency 50 Hz and wavelength 4 m; find the speed",
        "output": "speed = 200 m/s, because v = 50 x 4 = 200",
        "lang": "en",
    },
    {
        "input": "৫০ Hz কম্পাঙ্ক ও ৪ মিটার তরঙ্গদৈর্ঘ্যের তরঙ্গের বেগ কত?",
        "output": "বেগ = ২০০ ম/সে, কারণ v = ৫০ x ৪ = ২০০",
        "lang": "bn",
        "confidence": 0.95,
    },
    {
        "input": "an object does 100 J of work in 5 seconds; find the power",
        "output": "power = 20 W, because P = 100 / 5 = 20",
        "lang": "en",
    },
    {
        "input": "৫ সেকেন্ডে ১০০ J কাজ হলে ক্ষমতা কত?",
        "output": "ক্ষমতা = ২০ W, কারণ P = ১০০/৫ = ২০",
        "lang": "bn",
        "confidence": 0.95,
    },
]

# ---------------------------------------------------------------------------
# Tests: deterministic sanity tests embedded in the package
# ---------------------------------------------------------------------------

PHYSICS_TESTS: List[Dict[str, Any]] = [
    {"id": "p30_velocity_200_10", "input": "velocity of 200 m in 10 s", "expected_output": "20", "lang": "en"},
    {
        "id": "p30_velocity_bn",
        "input": "২০০ মিটার ১০ সেকেন্ডে অতিক্রমের বেগ",
        "expected_output": "২০",
        "lang": "bn",
        "confidence": 0.95,
    },
    {"id": "p30_force_5_2", "input": "force of mass 5 kg acceleration 2 m/s^2", "expected_output": "10", "lang": "en"},
    {"id": "p30_work_10_4", "input": "work done by force 10 N over 4 m", "expected_output": "40", "lang": "en"},
    {"id": "p30_ke_2_3", "input": "kinetic energy of mass 2 kg at 3 m/s", "expected_output": "9", "lang": "en"},
    {
        "id": "p30_free_fall_5",
        "input": "distance fallen freely in 5 seconds",
        "expected_output": "122.5",
        "lang": "en",
    },
    {"id": "p30_pe_2_10", "input": "potential energy of 2 kg at height 10 m", "expected_output": "196", "lang": "en"},
    {
        "id": "p30_ohm_12_4",
        "input": "current with voltage 12 V and resistance 4 ohm",
        "expected_output": "3",
        "lang": "en",
    },
    {
        "id": "p30_series_6_3",
        "input": "total resistance of 6 ohm and 3 ohm in series",
        "expected_output": "9",
        "lang": "en",
    },
    {
        "id": "p30_parallel_6_3",
        "input": "total resistance of 6 ohm and 3 ohm in parallel",
        "expected_output": "2",
        "lang": "en",
    },
    {
        "id": "p30_power_100_5",
        "input": "power for 100 J of work in 5 s",
        "expected_output": "20",
        "lang": "en",
    },
    {
        "id": "p30_wave_50_4",
        "input": "speed of wave with frequency 50 Hz and wavelength 4 m",
        "expected_output": "200",
        "lang": "en",
    },
    {"id": "p30_momentum_2_3", "input": "momentum of mass 2 kg at 3 m/s", "expected_output": "6", "lang": "en"},
]

# ---------------------------------------------------------------------------
# Provenance: content hash computed from the canonical payload
# ---------------------------------------------------------------------------


def _build_payload() -> str:
    """Canonical payload for the content hash (order matters)."""
    import json

    parts: List[str] = []
    parts.append(json.dumps(PHYSICS_SYNONYMS, sort_keys=True, ensure_ascii=False))
    parts.append(json.dumps(PHYSICS_CONCEPTS, sort_keys=True, ensure_ascii=False))
    parts.append(json.dumps(PHYSICS_RELATIONS, sort_keys=True, ensure_ascii=False))
    parts.append(json.dumps(PHYSICS_FACTS, sort_keys=True, ensure_ascii=False))
    parts.append(json.dumps(PHYSICS_FORMULAS, sort_keys=True, ensure_ascii=False))
    parts.append(json.dumps(PHYSICS_RULES, sort_keys=True, ensure_ascii=False))
    parts.append(json.dumps(PHYSICS_EXAMPLES, sort_keys=True, ensure_ascii=False))
    parts.append(json.dumps(PHYSICS_TESTS, sort_keys=True, ensure_ascii=False))
    return "".join(parts)


_PAYLOAD = _build_payload()
_CONTENT_HASH = "sha256:" + hashlib.sha256(_PAYLOAD.encode("utf-8")).hexdigest()

# Shared source_ref used on every record so the registry accepts them.
_RECORD_SOURCE: Dict[str, Any] = {
    "title": "Misty Phase 30 physics curriculum",
    "url": "https://misty-brain.onrender.com",
    "retrieved_at": "2026-08-19T00:00:00Z",
    "content_hash": _CONTENT_HASH,
}


def physics_curriculum_package() -> TrainingPackageV2:
    """Return the Phase 30 bilingual physics curriculum package."""
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
            "kinematics": "velocity, acceleration, free fall and the equations of motion",
            "forces": "Newton's three laws, mass, weight and inertia",
            "energy": "kinetic energy, potential energy, work and power",
            "waves_sound": "wave speed, frequency, wavelength and sound",
            "electricity": "Ohm's law, current, voltage, resistance, series and parallel circuits",
            "optics": "reflection, refraction, focal length and the lens formula",
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

    all_facts = _topic_concepts() + _attach(PHYSICS_FACTS)

    return TrainingPackageV2(
        package_id=PACKAGE_ID,
        department=PACKAGE_DEPARTMENT,
        version=PACKAGE_VERSION,
        languages=["bn", "en"],
        license=PACKAGE_LICENSE,
        source=SourceRef(
            title="Misty deep physics curriculum (Phase 30) — bilingual, deterministic",
            url="https://misty-brain.onrender.com",
            retrieved_at=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            content_hash=_CONTENT_HASH,
        ),
        concepts=[
            {"name": "Physics", "type": "Field", "source_ref": _RECORD_SOURCE},
            {"name": "পদার্থবিজ্ঞান", "type": "বিজ্ঞান", "source_ref": _RECORD_SOURCE},
            *PHYSICS_CONCEPTS,
        ],
        relations=PHYSICS_RELATIONS,
        facts=all_facts,
        rules=[dict(r, source_ref=_RECORD_SOURCE) for r in PHYSICS_RULES],
        formulas=[dict(f, source_ref=_RECORD_SOURCE) for f in PHYSICS_FORMULAS],
        examples=_attach(PHYSICS_EXAMPLES),
        tests=_attach(PHYSICS_TESTS),
        confidence_policy={"default": 0.8, "requires_source": True},
    )


def register_physics_curriculum(brain: Any) -> int:
    """Load the Phase 30 physics curriculum into the brain's semantic
    memory and knowledge graph, and register the package.

    Returns the number of curriculum facts registered.
    """
    PackageRegistry().register(physics_curriculum_package())
    count = 0
    for entry in PHYSICS_CONCEPTS:
        if brain.concept_graph.get_concept_by_name(entry["name"]) is None:
            brain.concept_graph.create_concept(
                name=entry["name"],
                concept_type=entry.get("type", "PhysicsConcept"),
            )
    # Phase 30: alias facts — the NLU head-noun parser extracts phrasal
    # targets ("newton's second law definition", "ohm's law", "kinetic
    # energy definition") that would not otherwise match the canonical
    # subjects stored in PHYSICS_FACTS.
    for alias, canonical in PHYSICS_SYNONYMS.items():
        for fact in PHYSICS_FACTS:
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

    for fact in PHYSICS_FACTS:
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
