# ruff: noqa: RUF001  (Bengali text is visually ambiguous by design)
"""Phase 32: Misty bilingual social-cultural knowledge curriculum.

This module trains Misty with verified, short-fact knowledge about
Bangladesh and India — the two cultures Misty's users most often speak
about. Every record is a confirmed, established fact (capitals, history,
festivals, geography, languages); nothing uncertain is claimed.

Departments (topics):
- bd_state         : Bangladesh state, independence, language movement
- bd_festivals     : Pahela Baishakh, Pohela Boishakh, Eid, Durga Puja,
                     festivals of Bengal
- bd_geography     : Bangladesh rivers, districts, regions, climate
- in_state         : India state, republic, national symbols
- in_geography     : India states, rivers, landmarks, climate
- world            : continents, oceans, planet basics, time

The curriculum records enter the package registry with provenance, so
the brain can answer questions like "Bangladesh er rajdhani ki?" or
"India's national animal?" in both Bengali and English.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any, Dict, List

from brain.knowledge.registry import (
    PackageRegistry,
    SourceRef,
    TrainingPackageV2,
)

PACKAGE_ID = "misty-culture-phase32"
PACKAGE_DEPARTMENT = "culture"
PACKAGE_VERSION = "1.0.0"
PACKAGE_LICENSE = "proprietary"

_TOPIC: List[str] = [
    "bd_state",
    "bd_festivals",
    "bd_geography",
    "in_state",
    "in_geography",
    "world",
]

# ---------------------------------------------------------------------------
# Concepts: the vocabulary of the curriculum (bilingual pairs)
# ---------------------------------------------------------------------------

CULTURE_CONCEPTS: List[Dict[str, Any]] = [
    # Bangladesh state
    {"name": "Bangladesh", "type": "Country", "lang": "en"},
    {"name": "বাংলাদেশ", "type": "দেশ", "lang": "bn"},
    {"name": "Dhaka", "type": "Capital", "lang": "en"},
    {"name": "ঢাকা", "type": "রাজধনী", "lang": "bn"},
    {"name": "Independence Day", "type": "Day", "lang": "en"},
    {"name": "স্বাধীনতা দিবস", "type": "দিন", "lang": "bn"},
    {"name": "Victory Day", "type": "Day", "lang": "en"},
    {"name": "বিজয় দিবস", "type": "দিন", "lang": "bn"},
    {"name": "Language Movement", "type": "Movement", "lang": "en"},
    {"name": "ভাষা আন্দোলন", "type": "আন্দোলন", "lang": "bn"},
    {"name": "International Mother Language Day", "type": "Day", "lang": "en"},
    {"name": "আন্তর্জাতিক মাতৃভাষা দিবস", "type": "দিন", "lang": "bn"},
    # Bangladesh festivals
    {"name": "Pahela Baishakh", "type": "Festival", "lang": "en"},
    {"name": "পহেলা বৈশাখ", "type": "উৎসব", "lang": "bn"},
    {"name": "Bengali New Year", "type": "Festival", "lang": "en"},
    {"name": "বাংলা নববর্ষ", "type": "উৎসব", "lang": "bn"},
    {"name": "Durga Puja", "type": "Festival", "lang": "en"},
    {"name": "দুর্গাপূজা", "type": "উৎসব", "lang": "bn"},
    {"name": "Eid", "type": "Festival", "lang": "en"},
    {"name": "ঈদ", "type": "উৎসব", "lang": "bn"},
    # Bangladesh geography
    {"name": "Padma", "type": "River", "lang": "en"},
    {"name": "পদ্মা", "type": "নদী", "lang": "bn"},
    {"name": "Sundarbans", "type": "Forest", "lang": "en"},
    {"name": "সুন্দরবন", "type": "বন", "lang": "bn"},
    {"name": "Cox's Bazar", "type": "Place", "lang": "en"},
    {"name": "কক্সবাজার", "type": "স্থান", "lang": "bn"},
    # India state
    {"name": "India", "type": "Country", "lang": "en"},
    {"name": "ভারত", "type": "দেশ", "lang": "bn"},
    {"name": "New Delhi", "type": "Capital", "lang": "en"},
    {"name": "নতুন দিল্লি", "type": "রাজধনী", "lang": "bn"},
    {"name": "Republic Day", "type": "Day", "lang": "en"},
    {"name": "সাধারণতন্ত্র দিবস", "type": "দিন", "lang": "bn"},
    {"name": "Independence Day of India", "type": "Day", "lang": "en"},
    {"name": "ভারতের স্বাধীনতা দিবস", "type": "দিন", "lang": "bn"},
    # India geography
    {"name": "Ganges", "type": "River", "lang": "en"},
    {"name": "গঙ্গা", "type": "নদী", "lang": "bn"},
    {"name": "Taj Mahal", "type": "Monument", "lang": "en"},
    {"name": "তাজমহল", "type": "স্মারক", "lang": "bn"},
    {"name": "Himalayas", "type": "MountainRange", "lang": "en"},
    {"name": "হিমালয়", "type": "পর্বতমালা", "lang": "bn"},
    # World
    {"name": "Asia", "type": "Continent", "lang": "en"},
    {"name": "এশিয়া", "type": "মহাদেশ", "lang": "bn"},
    {"name": "Earth", "type": "Planet", "lang": "en"},
    {"name": "পৃথিবী", "type": "গ্রহ", "lang": "bn"},
    {"name": "Pacific Ocean", "type": "Ocean", "lang": "en"},
    {"name": "প্রশান্ত মহাসাগর", "type": "মহাসাগর", "lang": "bn"},
    {"name": "Continents", "type": "Field", "lang": "en"},
    {"name": "মহাদেশ", "type": "ক্ষেত্র", "lang": "bn"},
]

# ---------------------------------------------------------------------------
# Relations between concepts (lightweight, bidirectional weights)
# ---------------------------------------------------------------------------

CULTURE_RELATIONS: List[Dict[str, Any]] = [
    {"source": "Bangladesh", "target": "Dhaka", "type": "has_capital", "weight": 0.98, "confidence": 0.99},
    {"source": "বাংলাদেশ", "target": "ঢাকা", "type": "রাজধনী_আছে", "weight": 0.98, "confidence": 0.99},
    {"source": "Bangladesh", "target": "Pahela Baishakh", "type": "has_festival", "weight": 0.95, "confidence": 0.98},
    {"source": "বাংলাদেশ", "target": "পহেলা বৈশাখ", "type": "উৎসব_আছে", "weight": 0.95, "confidence": 0.98},
    {"source": "Bangladesh", "target": "Padma", "type": "has_river", "weight": 0.92, "confidence": 0.97},
    {"source": "Bangladesh", "target": "Sundarbans", "type": "has_forest", "weight": 0.94, "confidence": 0.97},
    {"source": "India", "target": "New Delhi", "type": "has_capital", "weight": 0.98, "confidence": 0.99},
    {"source": "ভারত", "target": "নতুন দিল্লি", "type": "রাজধনী_আছে", "weight": 0.98, "confidence": 0.99},
    {"source": "India", "target": "Taj Mahal", "type": "has_monument", "weight": 0.94, "confidence": 0.97},
    {"source": "ভারত", "target": "তাজমহল", "type": "স্মারক_আছে", "weight": 0.94, "confidence": 0.97},
    {"source": "India", "target": "Asia", "type": "part_of", "weight": 0.9, "confidence": 0.98},
    {"source": "Bangladesh", "target": "Asia", "type": "part_of", "weight": 0.9, "confidence": 0.98},
    {"source": "Padma", "target": "Ganges", "type": "tributary_of", "weight": 0.85, "confidence": 0.95},
    {"source": "পদ্মা", "target": "গঙ্গা", "type": "উপনদী", "weight": 0.85, "confidence": 0.95},
]

# ---------------------------------------------------------------------------
# Synonyms: question aliases -> canonical subject names
# ---------------------------------------------------------------------------

CULTURE_SYNONYMS: Dict[str, str] = {
    # Bangladesh capital
    "dhaka definition": "Dhaka",
    "rajdhani definition": "Dhaka",
    "bd capital definition": "Dhaka",
    # Bangladesh independence
    "bd independence day definition": "Independence Day",
    "victory day definition": "Victory Day",
    "language movement definition": "Language Movement",
    "mother language day definition": "International Mother Language Day",
    "language day definition": "International Mother Language Day",
    # Bangladesh festivals
    "pahela baishakh definition": "Pahela Baishakh",
    "bengali new year definition": "Bengali New Year",
    "pohela boishakh definition": "Pahela Baishakh",
    "durga puja definition": "Durga Puja",
    "eid definition": "Eid",
    # Bangladesh geography
    "padma definition": "Padma",
    "sundarbans definition": "Sundarbans",
    "cox's bazar definition": "Cox's Bazar",
    # India capital
    "new delhi definition": "New Delhi",
    "india capital definition": "New Delhi",
    "in capital definition": "New Delhi",
    # India days
    "india independence day definition": "Independence Day of India",
    "republic day definition": "Republic Day",
    # India geography
    "ganges definition": "Ganges",
    "ganga definition": "Ganges",
    "taj mahal definition": "Taj Mahal",
    "himalayas definition": "Himalayas",
    # World
    "asia definition": "Asia",
    "earth definition": "Earth",
    "pacific ocean definition": "Pacific Ocean",
    "continents definition": "Continents",
    # Bengali aliases
    "\u09a2\u09be\u0995\u09be\u09b0 \u09aa\u09b0\u09bf\u099a\u09af\u09bc": "Dhaka",
    "\u09ac\u09be\u0982\u09b2\u09be\u09a6\u09c7\u09b6\u09c7\u09b0 \u09b0\u09be\u099c\u09a7\u09be\u09a8\u09c0": "Dhaka",
    "\u09b8\u09cd\u09ac\u09be\u09a7\u09c0\u09a8\u09a4\u09be \u09a6\u09bf\u09ac\u09b8": "Independence Day",
    "\u09ac\u09bf\u099c\u09af\u09bc \u09a6\u09bf\u09ac\u09b8": "Victory Day",
    "\u09ad\u09be\u09b7\u09be \u0986\u09a8\u09cd\u09a6\u09cb\u09b2\u09a8": "Language Movement",
    "\u09ae\u09be\u09a4\u09c3\u09ad\u09be\u09b7\u09be \u09a6\u09bf\u09ac\u09b8": "International Mother Language Day",
    "\u09aa\u09b9\u09c7\u09b2\u09be \u09ac\u09c8\u09b6\u09be\u0996": "Pahela Baishakh",
    "\u09a6\u09c1\u09b0\u09cd\u0997\u09be\u09aa\u09c2\u099c\u09be": "Durga Puja",
    "\u0988\u09a6": "Eid",
    "\u09aa\u09a6\u09cd\u09ae\u09be": "Padma",
    "\u09b8\u09c1\u09a8\u09cd\u09a6\u09b0\u09ac\u09a8": "Sundarbans",
    "\u0995\u0995\u09cd\u09b8\u09ac\u09be\u099c\u09be\u09b0": "Cox's Bazar",
    "\u09a8\u09a4\u09c1\u09a8 \u09a6\u09bf\u09b2\u09cd\u09b2\u09c0": "New Delhi",
    "\u09ad\u09be\u09b0\u09a4\u09c7\u09b0 \u09b0\u09be\u099c\u09a7\u09be\u09a8\u09c0": "New Delhi",
    "\u0997\u0982\u0997\u09be": "Ganges",
    "\u09a4\u09be\u099c\u09ae\u09b9\u09b2": "Taj Mahal",
    "\u09b9\u09bf\u09ae\u09be\u09b2\u09af\u09bc": "Himalayas",
    "\u098f\u09b6\u09bf\u09af\u09bc\u09be": "Asia",
    "\u09aa\u09c3\u09a5\u09bf\u09ac\u09c0": "Earth",
    "\u09ae\u09b9\u09be\u09a6\u09c7\u09b6": "Continents",
    "\u09ae\u09b9\u09be\u09b8\u09be\u0997\u09b0": "Pacific Ocean",
}

# ---------------------------------------------------------------------------
# Facts: verified, short, bilingual (each concept in both languages)
# ---------------------------------------------------------------------------

CULTURE_FACTS: List[Dict[str, Any]] = [
    # ----------------------------------------------------------------
    # bd_state: Bangladesh state, independence, language movement
    # ----------------------------------------------------------------
    {
        "subject": "Bangladesh",
        "predicate": "definition",
        "obj": "South Asian country in the Bengal region; population about "
        "170 million; independence declared 26 March 1971, won 16 December 1971",
        "lang": "en",
        "topic": "bd_state",
        "confidence": 0.98,
    },
    {
        "subject": "বাংলাদেশ",
        "predicate": "সংজ্ঞা",
        "obj": "বাংলা অঞ্চলের দক্ষিণ এশিয়ান দেশ; জনসংখ্যা প্রায় ১৭ কোটি; ২৬ মার্চ ১৯৭১-এ স্বাধীনতা ঘোষণা, ১৬ ডিসেম্বর ১৯৭১-এ বিজয়",
        "lang": "bn",
        "topic": "bd_state",
        "confidence": 0.98,
    },
    # Phase 32: compound-subject capital facts — the BN possessive query
    # "বাংলাদেশের রাজধনী কি?" parses the whole phrase
    # "বাংলাদেশের রাজধনী" as the definition target, so the brain must hold
    # the compound subject itself instead of reducing it to "বাংলাদেশ"
    # (which would return the country's own definition instead of Dhaka).
    {
        "subject": "বাংলাদেশের রাজধনী",
        "predicate": "সংজ্ঞা",
        "obj": "ঢাকা",
        "lang": "bn",
        "topic": "bd_state",
        "confidence": 0.99,
    },
    {
        "subject": "ভারতের রাজধনী",
        "predicate": "সংজ্ঞা",
        "obj": "নতুন দিল্লি",
        "lang": "bn",
        "topic": "in_state",
        "confidence": 0.99,
    },
    {
        "subject": "Dhaka",
        "predicate": "definition",
        "obj": "Capital and largest city of Bangladesh, on the Buriganga river; "
        "city of mosques (Baitul Mukarram) and Rickshaw capital of the world",
        "lang": "en",
        "topic": "bd_state",
        "confidence": 0.98,
    },
    {
        "subject": "ঢাকা",
        "predicate": "সংজ্ঞা",
        "obj": "বাংলাদেশের রাজধনী ও বৃহত্তম শহর, বুড়িগঙ্গা নদীর তীরে; মসজিদের শহর ও রিকশার রাজধনী",
        "lang": "bn",
        "topic": "bd_state",
        "confidence": 0.98,
    },
    {
        "subject": "Independence Day",
        "predicate": "definition",
        "obj": "Bangladesh Independence Day, 26 March 1971; Sheikh Mujibur Rahman declared independence of Bangladesh",
        "lang": "en",
        "topic": "bd_state",
        "confidence": 0.98,
    },
    {
        "subject": "স্বাধীনতা দিবস",
        "predicate": "সংজ্ঞা",
        "obj": "বাংলাদেশের স্বাধীনতা দিবস, ২৬ মার্চ ১৯৭১; শেখ মুজিবুর রহমান বাংলাদেশের স্বাধীনতা ঘোষণা করেন",
        "lang": "bn",
        "topic": "bd_state",
        "confidence": 0.98,
    },
    {
        "subject": "Victory Day",
        "predicate": "definition",
        "obj": "Bangladesh Victory Day, 16 December 1971; the Pakistani army "
        "surrendered, ending the Liberation War; national red-green flag raised",
        "lang": "en",
        "topic": "bd_state",
        "confidence": 0.98,
    },
    {
        "subject": "বিজয় দিবস",
        "predicate": "সংজ্ঞা",
        "obj": "বাংলাদেশের বিজয় দিবস, ১৬ ডিসেম্বর ১৯৭১; পাকিস্তানি সেনাবাহিনী আত্মসমর্পণ করে, মুক্তিযুদ্ধ শেষ হয়",
        "lang": "bn",
        "topic": "bd_state",
        "confidence": 0.98,
    },
    {
        "subject": "Language Movement",
        "predicate": "definition",
        "obj": "The Bengali Language Movement of 1952 in East Bengal; students "
        "died on 21 February 1952 demanding Bengali as a state language",
        "lang": "en",
        "topic": "bd_state",
        "confidence": 0.98,
    },
    {
        "subject": "ভাষা আন্দোলন",
        "predicate": "সংজ্ঞা",
        "obj": "১৯৫২ সালের বাংলা ভাষা আন্দোলন; রাষ্ট্রভাষা হিসেবে বাংলার দাবিতে ২১ ফেব্রুয়ারি ১৯৫২-এ ছাত্ররা প্রাণ দেন",
        "lang": "bn",
        "topic": "bd_state",
        "confidence": 0.98,
    },
    {
        "subject": "International Mother Language Day",
        "predicate": "definition",
        "obj": "UNESCO declared 21 February as International Mother Language "
        "Day in 1999, honouring the 1952 Bengali Language Movement martyrs",
        "lang": "en",
        "topic": "bd_state",
        "confidence": 0.98,
    },
    {
        "subject": "আন্তর্জাতিক মাতৃভাষা দিবস",
        "predicate": "সংজ্ঞা",
        "obj": "ইউনেস্কো ১৯৯৯ সালে ২১ ফেব্রুয়ারিকে আন্তর্জাতিক মাতৃভাষা দিবস ঘোষণা করে, ১৯৫২ সালের ভাষা আন্দোলনের শহীদদের স্মরণে",
        "lang": "bn",
        "topic": "bd_state",
        "confidence": 0.98,
    },
    {
        "subject": "Sheikh Mujibur Rahman",
        "predicate": "definition",
        "obj": "Founding father and first President/Prime Minister of Bangladesh; "
        "known as Bangabandhu, gave the 7 March 1971 speech at Ramna Race Course",
        "lang": "en",
        "topic": "bd_state",
        "confidence": 0.98,
    },
    {
        "subject": "শেখ মুজিবুর রহমান",
        "predicate": "সংজ্ঞা",
        "obj": "বাংলাদেশের জনক ও প্রথম রাষ্ট্রপতি/প্রধানমন্ত্রী; বঙ্গবন্ধু নামে পরিচিত; ৭ মার্চ ১৯৭১-এ রমনা রেসকোর্সে ভাষণ দেন",
        "lang": "bn",
        "topic": "bd_state",
        "confidence": 0.98,
    },
    {
        "subject": "Bangladesh flag",
        "predicate": "definition",
        "obj": "Green field with a red disc; green stands for the green land of "
        "Bengal, red for the blood of liberation-war martyrs",
        "lang": "en",
        "topic": "bd_state",
        "confidence": 0.98,
    },
    {
        "subject": "বাংলাদেশের পতাকা",
        "predicate": "সংজ্ঞা",
        "obj": "সবুজ ফোন্টে লাল বৃত্ত; সবুজ বাংলার সবুজ মাটিকে, লাল মুক্তিযুদ্ধের শহীদদের রক্তকে প্রতীকী করে",
        "lang": "bn",
        "topic": "bd_state",
        "confidence": 0.98,
    },
    # ----------------------------------------------------------------
    # bd_festivals: Bengali festivals
    # ----------------------------------------------------------------
    {
        "subject": "Pahela Baishakh",
        "predicate": "definition",
        "obj": "Bengali New Year, the first day of the Bengali month Baishakh; "
        "celebrated on 14 April with Mangal Shobhajatra and Haal Khata",
        "lang": "en",
        "topic": "bd_festivals",
        "confidence": 0.98,
    },
    {
        "subject": "পহেলা বৈশাখ",
        "predicate": "সংজ্ঞা",
        "obj": "বাংলা নববর্ষ, বাংলা মাস বৈশাখের প্রথম দিন; ১৪ এপ্রিল মন্গল শোভাযাত্রা ও হালখাতা দিয়ে পালন হয়",
        "lang": "bn",
        "topic": "bd_festivals",
        "confidence": 0.98,
    },
    {
        "subject": "Bengali New Year",
        "predicate": "definition",
        "obj": "Bangla Noboborsho, celebrated in Bangladesh and West Bengal; "
        "the Bengali calendar year 1428 began in 2021 (1433 in 2026)",
        "lang": "en",
        "topic": "bd_festivals",
        "confidence": 0.97,
    },
    {
        "subject": "বাংলা নববর্ষ",
        "predicate": "সংজ্ঞা",
        "obj": "বাংলা নববর্ষ, বাংলাদেশ ও পশ্চিমবঙ্গে পালিত; বাংলা সনের নতুন বছর",
        "lang": "bn",
        "topic": "bd_festivals",
        "confidence": 0.97,
    },
    {
        "subject": "Durga Puja",
        "predicate": "definition",
        "obj": "Hindu festival honouring Goddess Durga, the biggest religious "
        "festival of Bangladesh; idols are immersed on Vijaya Dashami",
        "lang": "en",
        "topic": "bd_festivals",
        "confidence": 0.98,
    },
    {
        "subject": "দুর্গাপূজা",
        "predicate": "সংজ্ঞা",
        "obj": "মা দুর্গাকে স্মরণ করে হিন্দুদের প্রধান উৎসব; বিজয়া দশমীতে প্রতিমা বিসর্জন দেওয়া হয়",
        "lang": "bn",
        "topic": "bd_festivals",
        "confidence": 0.98,
    },
    {
        "subject": "Eid",
        "predicate": "definition",
        "obj": "The two major Muslim festivals, Eid-ul-Fitr (after Ramadan) and "
        "Eid-ul-Adha; families gather and share food and gifts",
        "lang": "en",
        "topic": "bd_festivals",
        "confidence": 0.98,
    },
    {
        "subject": "ঈদ",
        "predicate": "সংজ্ঞা",
        "obj": "মুসলমানদের দুটি প্রধান উৎসব, ঈদুল ফিতর (রমজানের পরে) ও ঈদুল আযহা; পরিবার মেলে ও খাবার-উপহার বাটোয়ারা হয়",
        "lang": "bn",
        "topic": "bd_festivals",
        "confidence": 0.98,
    },
    # ----------------------------------------------------------------
    # bd_geography: Bangladesh rivers, regions, landmarks
    # ----------------------------------------------------------------
    {
        "subject": "Padma",
        "predicate": "definition",
        "obj": "The largest river of Bangladesh; the Ganges enters Bangladesh at "
        "Shibganj and flows as the Padma until joining the Meghna",
        "lang": "en",
        "topic": "bd_geography",
        "confidence": 0.98,
    },
    {
        "subject": "পদ্মা",
        "predicate": "সংজ্ঞা",
        "obj": "বাংলাদেশের সবচেয়ে বড় নদী; গঙ্গা শিবগঞ্জে বাংলাদেশে প্রবেশ করে পদ্মা নামে মেঘনার সঙ্গে মিলিত হয়",
        "lang": "bn",
        "topic": "bd_geography",
        "confidence": 0.98,
    },
    {
        "subject": "Sundarbans",
        "predicate": "definition",
        "obj": "The world's largest mangrove forest, shared by Bangladesh and "
        "India; home of the Royal Bengal Tiger; UNESCO World Heritage Site",
        "lang": "en",
        "topic": "bd_geography",
        "confidence": 0.98,
    },
    {
        "subject": "সুন্দরবন",
        "predicate": "সংজ্ঞা",
        "obj": "বিশ্বের সবচেয়ে বড় ম্যাংগ্রোভ বন, বাংলাদেশ ও ভারতের সীমান্তে; রয়্যাল বেঙ্গল টাইগারের আবাস; ইউনেস্কো বিশ্ব ঐতিহ্য",
        "lang": "bn",
        "topic": "bd_geography",
        "confidence": 0.98,
    },
    {
        "subject": "Cox's Bazar",
        "predicate": "definition",
        "obj": "Longest natural sea beach in the world, about 120 km, in southeastern Bangladesh on the Bay of Bengal",
        "lang": "en",
        "topic": "bd_geography",
        "confidence": 0.98,
    },
    {
        "subject": "কক্সবাজার",
        "predicate": "সংজ্ঞা",
        "obj": "বিশ্বের দীর্ঘতম প্রাকৃতিক সমুদ্র সৈকত, প্রায় ১২০ কিলোমিটার, বাংলাদেশের দক্ষিণ-পূর্বে বঙ্গোপসাগরের তীরে",
        "lang": "bn",
        "topic": "bd_geography",
        "confidence": 0.98,
    },
    {
        "subject": "Bangladesh divisions",
        "predicate": "definition",
        "obj": "Bangladesh is divided into 8 administrative divisions: Dhaka, "
        "Chattogram, Khulna, Rajshahi, Barishal, Sylhet, Rangpur and Mymensingh",
        "lang": "en",
        "topic": "bd_geography",
        "confidence": 0.98,
    },
    {
        "subject": "বাংলাদেশের বিভাগ",
        "predicate": "সংজ্ঞা",
        "obj": "বাংলাদেশ ৮টি প্রশাসনিক বিভাগে বিভক্ত: ঢাকা, চট্টগ্রাম, খুলনা, রাজশাহী, বরিশাল, সিলেট, রংপুর ও ময়মনসিংহ",
        "lang": "bn",
        "topic": "bd_geography",
        "confidence": 0.98,
    },
    # ----------------------------------------------------------------
    # in_state: India state and national symbols
    # ----------------------------------------------------------------
    {
        "subject": "India",
        "predicate": "definition",
        "obj": "South Asian country, world's most populous nation (over 1.4 "
        "billion); independence from Britain on 15 August 1947; republic since "
        "26 January 1950",
        "lang": "en",
        "topic": "in_state",
        "confidence": 0.98,
    },
    {
        "subject": "ভারত",
        "predicate": "সংজ্ঞা",
        "obj": "দক্ষিণ এশিয়ান দেশ, বিশ্বের সবচেয়ে জনবহুল রাষ্ট্র (১.৪ "
        "বিলিয়নের বেশি); ১৫ আগস্ট ১৯৪৭-এ ব্রিটেনের কাছ থেকে স্বাধীনতা; "
        "২৬ জানুয়ারি ১৯৫০ থেকে সাধারণতন্ত্র",
        "lang": "bn",
        "topic": "in_state",
        "confidence": 0.98,
    },
    {
        "subject": "New Delhi",
        "predicate": "definition",
        "obj": "Capital of India, in the National Capital Territory; seat of "
        "Parliament (Sansad Bhavan) and Rashtrapati Bhavan",
        "lang": "en",
        "topic": "in_state",
        "confidence": 0.98,
    },
    {
        "subject": "নতুন দিল্লি",
        "predicate": "সংজ্ঞা",
        "obj": "ভারতের রাজধনী, জাতীয় রাজধনী অঞ্চলে; সংসদ ভবন ও রাষ্ট্রপতি ভবনের আসন",
        "lang": "bn",
        "topic": "in_state",
        "confidence": 0.98,
    },
    {
        "subject": "Independence Day of India",
        "predicate": "definition",
        "obj": "India's Independence Day, 15 August 1947; Jawaharlal Nehru "
        "became the first Prime Minister; the flag was hoisted at Red Fort",
        "lang": "en",
        "topic": "in_state",
        "confidence": 0.98,
    },
    {
        "subject": "ভারতের স্বাধীনতা দিবস",
        "predicate": "সংজ্ঞা",
        "obj": "ভারতের স্বাধীনতা দিবস, ১৫ আগস্ট ১৯৪৭; জওহরলাল নেহেরু প্রথম প্রধানমন্ত্রী হন; লাল কেল্লায় পতাকা তোলা হয়",
        "lang": "bn",
        "topic": "in_state",
        "confidence": 0.98,
    },
    {
        "subject": "Republic Day",
        "predicate": "definition",
        "obj": "India's Republic Day, 26 January 1950; the Constitution of India "
        "came into force; celebrated with the parade at Rajpath",
        "lang": "en",
        "topic": "in_state",
        "confidence": 0.98,
    },
    {
        "subject": "সাধারণতন্ত্র দিবস",
        "predicate": "সংজ্ঞা",
        "obj": "ভারতের সাধারণতন্ত্র দিবস, ২৬ জানুয়ারি ১৯৫০; ভারতের সংবিধান কার্যকর হয়; রাজপথে কুচকাওয়াজ দিয়ে পালন হয়",
        "lang": "bn",
        "topic": "in_state",
        "confidence": 0.98,
    },
    {
        "subject": "Mahatma Gandhi",
        "predicate": "definition",
        "obj": "Leader of the Indian independence movement; father of the "
        "nation; champion of non-violence (ahimsa) and Satyagraha",
        "lang": "en",
        "topic": "in_state",
        "confidence": 0.98,
    },
    {
        "subject": "মহাত্মা গান্ধী",
        "predicate": "সংজ্ঞা",
        "obj": "ভারতের স্বাধীনতা আন্দোলনের নেতা; জাতির পিতা; অহিংসা ও সত্যাগ্রহের পুরোধা",
        "lang": "bn",
        "topic": "in_state",
        "confidence": 0.98,
    },
    {
        "subject": "India flag",
        "predicate": "definition",
        "obj": "Tricolour of saffron, white and green with the navy-blue "
        "Ashoka Chakra in the centre; adopted 22 July 1947",
        "lang": "en",
        "topic": "in_state",
        "confidence": 0.98,
    },
    {
        "subject": "ভারতের পতাকা",
        "predicate": "সংজ্ঞা",
        "obj": "গেরুয়া, সাদা ও সবুজ ত্রিবর্ণ; মাঝে নীল অশোক চক্র; ২২ জুলাই ১৯৪৭-এ গৃহীত",
        "lang": "bn",
        "topic": "in_state",
        "confidence": 0.98,
    },
    {
        "subject": "Indian national animal",
        "predicate": "definition",
        "obj": "The Royal Bengal Tiger (Panthera tigris tigris), India's national animal since 1973",
        "lang": "en",
        "topic": "in_state",
        "confidence": 0.97,
    },
    {
        "subject": "ভারতের জাতীয় প্রাণী",
        "predicate": "সংজ্ঞা",
        "obj": "রয়্যাল বেঙ্গল টাইগার (প্যান্থারা টাইগ্রিস টাইগ্রিস), ১৯৭৩ থেকে ভারতের জাতীয় প্রাণী",
        "lang": "bn",
        "topic": "in_state",
        "confidence": 0.97,
    },
    {
        "subject": "Indian national bird",
        "predicate": "definition",
        "obj": "The Indian Peafowl (peacock), India's national bird since 1963",
        "lang": "en",
        "topic": "in_state",
        "confidence": 0.97,
    },
    {
        "subject": "ভারতের জাতীয় পাখি",
        "predicate": "সংজ্ঞা",
        "obj": "ভারতীয় ময়ূর, ১৯৬৩ থেকে ভারতের জাতীয় পাখি",
        "lang": "bn",
        "topic": "in_state",
        "confidence": 0.97,
    },
    {
        "subject": "Bangladesh national animal",
        "predicate": "definition",
        "obj": "The Royal Bengal Tiger, Bangladesh's national animal",
        "lang": "en",
        "topic": "in_state",
        "confidence": 0.97,
    },
    {
        "subject": "বাংলাদেশের জাতীয় প্রাণী",
        "predicate": "সংজ্ঞা",
        "obj": "রয়্যাল বেঙ্গল টাইগার, বাংলাদেশের জাতীয় প্রাণী",
        "lang": "bn",
        "topic": "in_state",
        "confidence": 0.97,
    },
    # ----------------------------------------------------------------
    # in_geography: India geography
    # ----------------------------------------------------------------
    {
        "subject": "Ganges",
        "predicate": "definition",
        "obj": "One of the great rivers of South Asia; rises at Gangotri in the "
        "Himalayas, flows through India and Bangladesh (as the Padma) to the "
        "Bay of Bengal",
        "lang": "en",
        "topic": "in_geography",
        "confidence": 0.98,
    },
    {
        "subject": "গঙ্গা",
        "predicate": "সংজ্ঞা",
        "obj": "দক্ষিণ এশিয়ার মহান নদী; হিমালয়ের গঙ্গোত্রীতে উৎপত্তি, ভারত ও বাংলাদেশ দিয়ে (পদ্মা নামে) বঙ্গোপসাগরে মিশেছে",
        "lang": "bn",
        "topic": "in_geography",
        "confidence": 0.98,
    },
    {
        "subject": "Taj Mahal",
        "predicate": "definition",
        "obj": "White-marble mausoleum in Agra, Uttar Pradesh, built by Mughal "
        "emperor Shah Jahan in memory of Mumtaz Mahal (completed 1653); one of "
        "the Seven Wonders",
        "lang": "en",
        "topic": "in_geography",
        "confidence": 0.98,
    },
    {
        "subject": "তাজমহল",
        "predicate": "সংজ্ঞা",
        "obj": "আগ্রা, উত্তর প্রদেশের শাদা মার্বেলের সমাধি; মুঘল সম্রাট শাহ "
        "জাহান মুমতাজ মহলের স্মরণে তৈরি করেন (১৬৫৩-এ সম্পন্ন); সপ্তাশ্চর্যের "
        "একটি",
        "lang": "bn",
        "topic": "in_geography",
        "confidence": 0.98,
    },
    {
        "subject": "Himalayas",
        "predicate": "definition",
        "obj": "The highest mountain range on Earth; home of Mount Everest "
        "(8,848.86 m), the world's tallest peak, on the Nepal-China border",
        "lang": "en",
        "topic": "in_geography",
        "confidence": 0.98,
    },
    {
        "subject": "হিমালয়",
        "predicate": "সংজ্ঞা",
        "obj": "পৃথিবীর সবচেয়ে উচ্চু পর্বতমালা; এভারেস্ট শৃঙ্গের (৮,৮৪৮.৮৬ মিটার) আবাস, নেপাল-চীন সীমান্তে",
        "lang": "bn",
        "topic": "in_geography",
        "confidence": 0.98,
    },
    # ----------------------------------------------------------------
    # world: continents, oceans, planet
    # ----------------------------------------------------------------
    {
        "subject": "Continents",
        "predicate": "definition",
        "obj": "Earth has seven continents: Asia, Africa, North America, South "
        "America, Antarctica, Europe and Australia (Oceania)",
        "lang": "en",
        "topic": "world",
        "confidence": 0.98,
    },
    {
        "subject": "মহাদেশ",
        "predicate": "সংজ্ঞা",
        "obj": "পৃথিবীতে সাতটি মহাদেশ আছে: এশিয়া, আফ্রিকা, উত্তর আমেরিকা, দক্ষিণ আমেরিকা, আন্টার্কটিকা, ইউরোপ ও অস্ট্রেলিয়া (ওশেনিয়া)",
        "lang": "bn",
        "topic": "world",
        "confidence": 0.98,
    },
    {
        "subject": "Asia",
        "predicate": "definition",
        "obj": "The largest continent by area and population; home of India, Bangladesh, China, Japan and Indonesia",
        "lang": "en",
        "topic": "world",
        "confidence": 0.98,
    },
    {
        "subject": "এশিয়া",
        "predicate": "সংজ্ঞা",
        "obj": "আয়তন ও জনসংখ্যায় বিশ্বের সবচেয়ে বড় মহাদেশ; ভারত, বাংলাদেশ, চীন, জাপান ও ইন্দোনেশিয়ার আবাস",
        "lang": "bn",
        "topic": "world",
        "confidence": 0.98,
    },
    {
        "subject": "Earth",
        "predicate": "definition",
        "obj": "The third planet from the Sun; the only known planet with life; "
        "about 71% of its surface is covered by water",
        "lang": "en",
        "topic": "world",
        "confidence": 0.98,
    },
    {
        "subject": "পৃথিবী",
        "predicate": "সংজ্ঞা",
        "obj": "সূর্য থেকে তৃতীয় গ্রহ; জীবন থাকা একমাত্র পরিচিত গ্রহ; পৃথিবীর প্রায় ৭১% পৃষ্ঠ জলে আবৃত",
        "lang": "bn",
        "topic": "world",
        "confidence": 0.98,
    },
    {
        "subject": "Pacific Ocean",
        "predicate": "definition",
        "obj": "The largest and deepest ocean on Earth, covering about one third of the planet's surface",
        "lang": "en",
        "topic": "world",
        "confidence": 0.98,
    },
    {
        "subject": "প্রশান্ত মহাসাগর",
        "predicate": "সংজ্ঞা",
        "obj": "পৃথিবীর বৃহত্তম ও সবচেয়ে গভীর মহাসাগর, গ্রহের প্রায় এক তৃতীয়াংশ পৃষ্ঠ আবৃত করে",
        "lang": "bn",
        "topic": "world",
        "confidence": 0.98,
    },
]

# ---------------------------------------------------------------------------
# Formulas / rules / examples: not needed for a facts-only culture layer
# ---------------------------------------------------------------------------

CULTURE_FORMULAS: List[Dict[str, Any]] = []
CULTURE_RULES: List[Dict[str, Any]] = []
CULTURE_EXAMPLES: List[Dict[str, Any]] = []

# ---------------------------------------------------------------------------
# Tests: deterministic bilingual probes (>= 20 as required by the plan)
# ---------------------------------------------------------------------------

CULTURE_TESTS: List[Dict[str, Any]] = [
    {
        "id": "p32_bd_capital",
        "input": "dhaka definition?",
        "expected_output": "Dhaka",
        "lang": "en",
        "confidence": 0.95,
    },
    {"id": "p32_bd_capital_bn", "input": "বাংলাদেশের রাজধনী", "expected_output": "ঢাকা", "lang": "bn", "confidence": 0.95},
    {
        "id": "p32_in_capital",
        "input": "india capital definition?",
        "expected_output": "Delhi",
        "lang": "en",
        "confidence": 0.95,
    },
    {
        "id": "p32_bd_independence",
        "input": "independence day definition?",
        "expected_output": "1971",
        "lang": "en",
        "confidence": 0.95,
    },
    {
        "id": "p32_victory_day",
        "input": "victory day definition?",
        "expected_output": "16",
        "lang": "en",
        "confidence": 0.95,
    },
    {
        "id": "p32_language_movement",
        "input": "language movement definition?",
        "expected_output": "1952",
        "lang": "en",
        "confidence": 0.95,
    },
    {
        "id": "p32_language_day_bn",
        "input": "\u09ae\u09be\u09a4\u09c3\u09ad\u09be\u09b7\u09be \u09a6\u09bf\u09ac\u09b8",
        "expected_output": "UNESCO",
        "lang": "bn",
        "confidence": 0.95,
    },
    {
        "id": "p32_pahela_baishakh",
        "input": "pahela baishakh definition?",
        "expected_output": "April",
        "lang": "en",
        "confidence": 0.95,
    },
    {"id": "p32_pahela_bn", "input": "পহেলা বৈশাখ", "expected_output": "এপ্রিল", "lang": "bn", "confidence": 0.95},
    {"id": "p32_padma", "input": "padma definition?", "expected_output": "Ganges", "lang": "en", "confidence": 0.95},
    {"id": "p32_padma_bn", "input": "পদ্মা", "expected_output": "গঙ্গা", "lang": "bn", "confidence": 0.95},
    {
        "id": "p32_sundarbans",
        "input": "sundarbans definition?",
        "expected_output": "mangrove",
        "lang": "en",
        "confidence": 0.95,
    },
    {
        "id": "p32_coxs_bazar",
        "input": "cox's bazar definition?",
        "expected_output": "120",
        "lang": "en",
        "confidence": 0.95,
    },
    {
        "id": "p32_bd_divisions",
        "input": "bangladesh divisions definition?",
        "expected_output": "8",
        "lang": "en",
        "confidence": 0.95,
    },
    {
        "id": "p32_in_republic",
        "input": "republic day definition?",
        "expected_output": "1950",
        "lang": "en",
        "confidence": 0.95,
    },
    {
        "id": "p32_in_independence",
        "input": "independence day of india definition?",
        "expected_output": "15 August",
        "lang": "en",
        "confidence": 0.95,
    },
    {
        "id": "p32_gandhi",
        "input": "mahatma gandhi definition?",
        "expected_output": "non-violence",
        "lang": "en",
        "confidence": 0.95,
    },
    {
        "id": "p32_taj_mahal",
        "input": "taj mahal definition?",
        "expected_output": "Agra",
        "lang": "en",
        "confidence": 0.95,
    },
    {
        "id": "p32_himalayas",
        "input": "himalayas definition?",
        "expected_output": "Everest",
        "lang": "en",
        "confidence": 0.95,
    },
    {
        "id": "p32_continents",
        "input": "continents definition?",
        "expected_output": "seven",
        "lang": "en",
        "confidence": 0.95,
    },
    {"id": "p32_continent_bn", "input": "মহাদেশ", "expected_output": "সাত", "lang": "bn", "confidence": 0.95},
    {"id": "p32_earth", "input": "earth definition?", "expected_output": "71", "lang": "en", "confidence": 0.95},
    {
        "id": "p32_pacific",
        "input": "pacific ocean definition?",
        "expected_output": "largest",
        "lang": "en",
        "confidence": 0.95,
    },
    {
        "id": "p32_national_animal",
        "input": "indian national animal definition?",
        "expected_output": "Tiger",
        "lang": "en",
        "confidence": 0.95,
    },
    {
        "id": "p32_flag_bd",
        "input": "bangladesh flag definition?",
        "expected_output": "red",
        "lang": "en",
        "confidence": 0.95,
    },
]

# ---------------------------------------------------------------------------
# Payload hash: stable content fingerprint for provenance
# ---------------------------------------------------------------------------


def _build_payload() -> str:
    parts: List[str] = []
    parts.append(json.dumps(CULTURE_SYNONYMS, sort_keys=True, ensure_ascii=False))
    parts.append(json.dumps(CULTURE_CONCEPTS, sort_keys=True, ensure_ascii=False))
    parts.append(json.dumps(CULTURE_RELATIONS, sort_keys=True, ensure_ascii=False))
    parts.append(json.dumps(CULTURE_FACTS, sort_keys=True, ensure_ascii=False))
    parts.append(json.dumps(CULTURE_FORMULAS, sort_keys=True, ensure_ascii=False))
    parts.append(json.dumps(CULTURE_RULES, sort_keys=True, ensure_ascii=False))
    parts.append(json.dumps(CULTURE_EXAMPLES, sort_keys=True, ensure_ascii=False))
    parts.append(json.dumps(CULTURE_TESTS, sort_keys=True, ensure_ascii=False))
    return "".join(parts)


_PAYLOAD = _build_payload()
_CONTENT_HASH = "sha256:" + hashlib.sha256(_PAYLOAD.encode("utf-8")).hexdigest()

# Fixed retrieval timestamp keeps the content hash stable across runs.
_RECORD_SOURCE: Dict[str, Any] = {
    "title": "Misty Phase 32 social-cultural knowledge curriculum",
    "url": "https://misty-brain.onrender.com",
    "retrieved_at": "2026-08-19T00:00:00Z",
    "content_hash": _CONTENT_HASH,
}


def _attach(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Attach a stable source_ref to every curriculum record."""
    out: List[Dict[str, Any]] = []
    for record in records:
        rec = dict(record)
        if "source_ref" not in rec:
            rec["source_ref"] = _RECORD_SOURCE
        out.append(rec)
    return out


def culture_curriculum_package() -> TrainingPackageV2:
    """Return the Phase 32 bilingual social-cultural curriculum package."""
    from datetime import datetime, timezone

    all_facts: List[Dict[str, Any]] = _attach(CULTURE_FACTS)
    return TrainingPackageV2(
        package_id=PACKAGE_ID,
        department=PACKAGE_DEPARTMENT,
        version=PACKAGE_VERSION,
        languages=["bn", "en"],
        license=PACKAGE_LICENSE,
        source=SourceRef(
            title="Misty social-cultural knowledge curriculum (Phase 32) — verified facts only",
            url="https://misty-brain.onrender.com",
            retrieved_at=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            content_hash=_CONTENT_HASH,
        ),
        concepts=[
            *(
                {"name": "Culture", "type": "Field", "source_ref": _RECORD_SOURCE},
                {"name": "Bengal", "type": "Region", "source_ref": _RECORD_SOURCE},
                {"name": "বাংলা", "type": "অঞ্চল", "source_ref": _RECORD_SOURCE},
            ),
            *_attach(CULTURE_CONCEPTS),
        ],
        relations=_attach(CULTURE_RELATIONS),
        facts=all_facts,
        tests=_attach(CULTURE_TESTS),
    )


def register_culture_curriculum(brain: Any) -> int:
    """Load the Phase 32 culture curriculum into the brain's semantic
    memory and knowledge graph, and register the package.
    Returns the number of curriculum facts registered.
    """
    PackageRegistry().register(culture_curriculum_package())
    count = 0
    for entry in CULTURE_CONCEPTS:
        if brain.concept_graph.get_concept_by_name(entry["name"]) is None:
            brain.concept_graph.create_concept(
                name=entry["name"],
                concept_type=entry.get("type", "Concept"),
            )
    for alias, canonical in CULTURE_SYNONYMS.items():
        for fact in CULTURE_FACTS:
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
    for fact in CULTURE_FACTS:
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
