# ruff: noqa: RUF001
"""Phase 31: Misty bilingual Bengali literature curriculum.

This module trains Misty with verified, short-fact knowledge about the
three giants of modern Bengali literature — Rabindranath Tagore, Kazi
Nazrul Islam and Jibanananda Das — along with a few landmark works and
the Bengali literary renaissance. Every record is a confirmed,
established fact (life summary, major works, dates, awards); nothing
uncertain is claimed.

Departments (topics):
- tagore           : Rabindranath Tagore, his life, Gitanjali, works
- nazrul           : Kazi Nazrul Islam, Bidrohi, Nazrul Geeti
- jibanananda      : Jibanananda Das, Bonolata Sen, Rupasi Bangla
- renaissance      : Bengali literary renaissance, Bankimchandra, anthems
- songs            : Rabindra Sangeet, Nazrul Geeti

The curriculum records enter the package registry with provenance, so
the brain can answer concept questions like "Gitanjali ki?" (what is
Gitanjali?) or "রবীন্দ্রনাথ কে?" (who is Rabindranath?) from stored
knowledge, in both Bengali and English.
"""

from __future__ import annotations

import hashlib
from typing import Any, Dict, List

from brain.knowledge.registry import PackageRegistry, SourceRef, TrainingPackageV2

PACKAGE_ID = "misty-literature-phase31"
PACKAGE_DEPARTMENT = "literature"
PACKAGE_VERSION = "1.0.0"
PACKAGE_LICENSE = "proprietary"

_TOPIC: List[str] = ["tagore", "nazrul", "jibanananda", "renaissance", "songs"]

# ---------------------------------------------------------------------------
# Concepts: the vocabulary of the curriculum (bilingual pairs)
# ---------------------------------------------------------------------------

LITERATURE_CONCEPTS: List[Dict[str, Any]] = [
    # The writers
    {"name": "Rabindranath Tagore", "type": "Poet", "lang": "en"},
    {"name": "রবীন্দ্রনাথ ঠাকুর", "type": "কবি", "lang": "bn"},
    {"name": "Kazi Nazrul Islam", "type": "Poet", "lang": "en"},
    {"name": "কাজি নজরুল ইসলাম", "type": "কবি", "lang": "bn"},
    {"name": "Jibanananda Das", "type": "Poet", "lang": "en"},
    {"name": "জীবনানন্দ দাশ", "type": "কবি", "lang": "bn"},
    {"name": "Bankimchandra Chattopadhyay", "type": "Writer", "lang": "en"},
    {"name": "বঙ্কিমচন্দ্র চট্টোপাধ্যায়", "type": "লেখক", "lang": "bn"},
    {"name": "Bengali Literature", "type": "Field", "lang": "en"},
    {"name": "বাংলা সাহিত্য", "type": "বিষয়ক্ষেত্র", "lang": "bn"},
    # Tagore works and places
    {"name": "Gitanjali", "type": "Book", "lang": "en"},
    {"name": "গীতাঞ্জলি", "type": "গ্রন্থ", "lang": "bn"},
    {"name": "Rabindra Sangeet", "type": "MusicGenre", "lang": "en"},
    {"name": "রবীন্দ্রসঙ্গীত", "type": "সঙ্গীত ধারা", "lang": "bn"},
    {"name": "Gora", "type": "Novel", "lang": "en"},
    {"name": "গোরা", "type": "উপন্যাস", "lang": "bn"},
    {"name": "Chokher Bali", "type": "Novel", "lang": "en"},
    {"name": "ঘরে বাইরে", "type": "উপন্যাস", "lang": "bn"},
    {"name": "Home and the World", "type": "Novel", "lang": "en"},
    {"name": "Amar Sonar Bangla", "type": "Song", "lang": "en"},
    {"name": "আমার সোনার বাংলা", "type": "গান", "lang": "bn"},
    {"name": "Jana Gana Mana", "type": "Song", "lang": "en"},
    {"name": "জনগণমন", "type": "গান", "lang": "bn"},
    {"name": "Visva-Bharati", "type": "University", "lang": "en"},
    {"name": "বিশ্বভারতী", "type": "বিশ্ববিদ্যালয়", "lang": "bn"},
    {"name": "Santiniketan", "type": "Place", "lang": "en"},
    {"name": "শান্তিনিকেতন", "type": "স্থান", "lang": "bn"},
    {"name": "Jorasanko", "type": "Place", "lang": "en"},
    {"name": "জোড়াসাঁকো", "type": "স্থান", "lang": "bn"},
    {"name": "Nobel Prize in Literature", "type": "Award", "lang": "en"},
    {"name": "সাহিত্যে নোবেল পুরস্কার", "type": "পুরস্কার", "lang": "bn"},
    # Nazrul works
    {"name": "Bidrohi", "type": "Poem", "lang": "en"},
    {"name": "বিদ্রোহী", "type": "কবিতা", "lang": "bn"},
    {"name": "Nazrul Geeti", "type": "MusicGenre", "lang": "en"},
    {"name": "নজরুলগীতি", "type": "সঙ্গীত ধারা", "lang": "bn"},
    {"name": "Dhumketu", "type": "Newspaper", "lang": "en"},
    {"name": "ধূমকেতু", "type": "সংবাদপত্র", "lang": "bn"},
    {"name": "Rebel Poet", "type": "Title", "lang": "en"},
    {"name": "বিদ্রোহী কবি", "type": "উপাধি", "lang": "bn"},
    {"name": "National Poet of Bangladesh", "type": "Title", "lang": "en"},
    {"name": "বাংলাদেশের জাতীয় কবি", "type": "উপাধি", "lang": "bn"},
    # Jibanananda works
    {"name": "Bonolata Sen", "type": "Poem", "lang": "en"},
    {"name": "বনলতা সেন", "type": "কবিতা", "lang": "bn"},
    {"name": "Rupasi Bangla", "type": "Poem", "lang": "en"},
    {"name": "রূপসী বাংলা", "type": "কবিতা", "lang": "bn"},
    # Renaissance
    {"name": "Anandamath", "type": "Novel", "lang": "en"},
    {"name": "আনন্দমঠ", "type": "উপন্যাস", "lang": "bn"},
    {"name": "Vande Mataram", "type": "Song", "lang": "en"},
    {"name": "বন্দে মাতরম", "type": "গান", "lang": "bn"},
    {"name": "Bengali Renaissance", "type": "Movement", "lang": "en"},
    {"name": "বাংলার নবজাগরণ", "type": "আন্দোলন", "lang": "bn"},
]

LITERATURE_RELATIONS: List[Dict[str, Any]] = [
    {"source": "Bengali Literature", "target": "Rabindranath Tagore", "type": "includes", "lang": "en"},
    {"source": "Bengali Literature", "target": "Kazi Nazrul Islam", "type": "includes", "lang": "en"},
    {"source": "Bengali Literature", "target": "Jibanananda Das", "type": "includes", "lang": "en"},
    {"source": "বাংলা সাহিত্য", "target": "রবীন্দ্রনাথ ঠাকুর", "type": "সংযুক্ত", "lang": "bn"},
    {"source": "বাংলা সাহিত্য", "target": "কাজি নজরুল ইসলাম", "type": "সংযুক্ত", "lang": "bn"},
    {"source": "বাংলা সাহিত্য", "target": "জীবনানন্দ দাশ", "type": "সংযুক্ত", "lang": "bn"},
    {"source": "Rabindranath Tagore", "target": "Gitanjali", "type": "authored", "lang": "en"},
    {"source": "Rabindranath Tagore", "target": "Rabindra Sangeet", "type": "authored", "lang": "en"},
    {"source": "Rabindranath Tagore", "target": "Visva-Bharati", "type": "founded", "lang": "en"},
    {"source": "Kazi Nazrul Islam", "target": "Bidrohi", "type": "authored", "lang": "en"},
    {"source": "Kazi Nazrul Islam", "target": "Nazrul Geeti", "type": "authored", "lang": "en"},
    {"source": "Kazi Nazrul Islam", "target": "Dhumketu", "type": "founded", "lang": "en"},
    {"source": "Jibanananda Das", "target": "Bonolata Sen", "type": "authored", "lang": "en"},
    {"source": "Jibanananda Das", "target": "Rupasi Bangla", "type": "authored", "lang": "en"},
    {"source": "Bankimchandra Chattopadhyay", "target": "Anandamath", "type": "authored", "lang": "en"},
    {"source": "Bankimchandra Chattopadhyay", "target": "Vande Mataram", "type": "authored", "lang": "en"},
    {"source": "Gitanjali", "target": "Nobel Prize in Literature", "type": "won", "lang": "en"},
    {"source": "Rabindra Sangeet", "target": "Rabindranath Tagore", "type": "belongs_to", "lang": "en"},
    {"source": "Nazrul Geeti", "target": "Kazi Nazrul Islam", "type": "belongs_to", "lang": "en"},
    {"source": "Amar Sonar Bangla", "target": "Bangladesh", "type": "national_anthem_of", "lang": "en"},
    {"source": "Jana Gana Mana", "target": "India", "type": "national_anthem_of", "lang": "en"},
    {"source": "Misty", "target": "literature-curriculum-phase31", "type": "trained_on", "lang": "en"},
]

# ---------------------------------------------------------------------------
# Synonyms: NLU alias expansion — query phrases -> canonical subjects
# ---------------------------------------------------------------------------

LITERATURE_SYNONYMS: Dict[str, str] = {
    "tagore definition": "Rabindranath Tagore",
    "rabindranath tagore definition": "Rabindranath Tagore",
    "রবীন্দ্রনাথ ঠাকুরের পরিচয়": "রবীন্দ্রনাথ ঠাকুর",
    "rabindranath definition": "Rabindranath Tagore",
    "rabinranath tagore definition": "Rabindranath Tagore",
    "nazrul definition": "Kazi Nazrul Islam",
    "kazi nazrul islam definition": "Kazi Nazrul Islam",
    "নজরুলের পরিচয়": "কাজি নজরুল ইসলাম",
    "rebel poet definition": "Kazi Nazrul Islam",
    "jibanananda das definition": "Jibanananda Das",
    "জীবনানন্দ দাশের পরিচয়": "জীবনানন্দ দাশ",
    "jibanananda definition": "Jibanananda Das",
    "gitanjali definition": "Gitanjali",
    "গীতাঞ্জলির পরিচয়": "গীতাঞ্জলি",
    "gitanjali song offerings definition": "Gitanjali",
    "bidrohi definition": "Bidrohi",
    "বিদ্রোহীর পরিচয়": "বিদ্রোহী",
    "bidrohi poem definition": "Bidrohi",
    "bonolata sen definition": "Bonolata Sen",
    "বনলতা সেনের পরিচয়": "বনলতা সেন",
    "bonolata sen poem definition": "Bonolata Sen",
    "rupasi bangla definition": "Rupasi Bangla",
    "রূপসী বাংলার পরিচয়": "রূপসী বাংলা",
    "rabinra sangeet definition": "Rabindra Sangeet",
    "রবীন্দ্রসঙ্গীতের পরিচয়": "রবীন্দ্রসঙ্গীত",
    "nazrul geeti definition": "Nazrul Geeti",
    "নজরুলগীতির পরিচয়": "নজরুলগীতি",
    "amar sonar bangla definition": "Amar Sonar Bangla",
    "আমার সোনার বাংলার পরিচয়": "আমার সোনার বাংলা",
    "vande mataram definition": "Vande Mataram",
    "বন্দে মাতরমের পরিচয়": "বন্দে মাতরম",
    "anandamath definition": "Anandamath",
    "আনন্দমঠের পরিচয়": "আনন্দমঠ",
    "visva-bharati definition": "Visva-Bharati",
    "বিশ্বভারতীর পরিচয়": "বিশ্বভারতী",
    "santiniketan definition": "Santiniketan",
    "শান্তিনিকেতনের পরিচয়": "শান্তিনিকেতন",
    "bengali renaissance definition": "Bengali Renaissance",
    "বাংলার নবজাগরণের পরিচয়": "বাংলার নবজাগরণ",
}

# ---------------------------------------------------------------------------
# Facts: declarative curriculum knowledge (bilingual, verified only)
# ---------------------------------------------------------------------------

LITERATURE_FACTS: List[Dict[str, Any]] = [
    # --- Tagore: life ---
    {
        "subject": "Rabindranath Tagore",
        "predicate": "definition",
        "obj": "Bengali poet, writer and polymath (1861-1941); won the 1913 Nobel Prize in Literature for Gitanjali",
        "lang": "en",
        "topic": "tagore",
        "confidence": 0.98,
    },
    {
        "subject": "রবীন্দ্রনাথ ঠাকুর",
        "predicate": "সংজ্ঞা",
        "obj": "বাঙালি কবি, সাহিত্যিক ও সঙ্গীতজ্ঞ (৭ মে ১৮৬১ - ৭ আগস্ট ১৯৪১); গীতাঞ্জলির জন্য ১৯১৩ সালে সাহিত্যে নোবেল পুরস্কার পান",
        "lang": "bn",
        "topic": "tagore",
        "confidence": 0.98,
    },
    {
        "subject": "Rabindranath Tagore",
        "predicate": "born",
        "obj": "7 May 1861, Jorasanko, Kolkata",
        "lang": "en",
        "topic": "tagore",
        "confidence": 0.98,
    },
    {
        "subject": "রবীন্দ্রনাথ ঠাকুর",
        "predicate": "জন্ম",
        "obj": "৭ মে ১৮৬১, জোড়াসাঁকো, কলকাতা",
        "lang": "bn",
        "topic": "tagore",
        "confidence": 0.98,
    },
    {
        "subject": "Rabindranath Tagore",
        "predicate": "died",
        "obj": "7 August 1941, Kolkata",
        "lang": "en",
        "topic": "tagore",
        "confidence": 0.98,
    },
    {
        "subject": "রবীন্দ্রনাথ ঠাকুর",
        "predicate": "মৃত্যু",
        "obj": "৭ আগস্ট ১৯৪১, কলকাতা",
        "lang": "bn",
        "topic": "tagore",
        "confidence": 0.98,
    },
    {
        "subject": "Rabindranath Tagore",
        "predicate": "won",
        "obj": "Nobel Prize in Literature 1913 for Gitanjali (Song Offerings); first non-European laureate",
        "lang": "en",
        "topic": "tagore",
        "confidence": 0.98,
    },
    {
        "subject": "রবীন্দ্রনাথ ঠাকুর",
        "predicate": "পুরস্কার",
        "obj": "১৯১৩ সালে গীতাঞ্জলির জন্য সাহিত্যে নোবেল পুরস্কার; ইউরোপের বাইরে থেকে প্রথম বিজয়ী",
        "lang": "bn",
        "topic": "tagore",
        "confidence": 0.98,
    },
    {
        "subject": "Rabindranath Tagore",
        "predicate": "wrote_anthems",
        "obj": "Amar Sonar Bangla (Bangladesh) and Jana Gana Mana (India)",
        "lang": "en",
        "topic": "tagore",
        "confidence": 0.98,
    },
    {
        "subject": "Rabindranath Tagore",
        "predicate": "founded",
        "obj": "Visva-Bharati University, Santiniketan, 1921",
        "lang": "en",
        "topic": "tagore",
        "confidence": 0.98,
    },
    {
        "subject": "Visva-Bharati",
        "predicate": "definition",
        "obj": "university founded by Rabindranath Tagore in Santiniketan, 1921",
        "lang": "en",
        "topic": "tagore",
        "confidence": 0.98,
    },
    {
        "subject": "বিশ্বভারতী",
        "predicate": "সংজ্ঞা",
        "obj": "১৯২১ সালে রবীন্দ্রনাথ ঠাকুর শান্তিনিকেতনে প্রতিষ্ঠিত বিশ্ববিদ্যালয়",
        "lang": "bn",
        "topic": "tagore",
        "confidence": 0.98,
    },
    {
        "subject": "রবীন্দ্রনাথ ঠাকুর",
        "predicate": "প্রতিষ্ঠা",
        "obj": "১৯২১ সালে শান্তিনিকেতনে বিশ্বভারতী বিশ্ববিদ্যালয়",
        "lang": "bn",
        "topic": "tagore",
        "confidence": 0.98,
    },
    {
        "subject": "Rabindranath Tagore",
        "predicate": "wrote",
        "obj": "Gora, Chokher Bali, Home and the World, Gitanjali, Rabindra Sangeet",
        "lang": "en",
        "topic": "tagore",
        "confidence": 0.98,
    },
    {
        "subject": "রবীন্দ্রনাথ ঠাকুর",
        "predicate": "রচনা",
        "obj": "গোরা, চোখের বালি, ঘরে বাইরে, গীতাঞ্জলি, রবীন্দ্রসঙ্গীত",
        "lang": "bn",
        "topic": "tagore",
        "confidence": 0.98,
    },
    # --- Gitanjali ---
    {
        "subject": "Gitanjali",
        "predicate": "definition",
        "obj": "collection of poems by Rabindranath Tagore; won the 1913 Nobel Prize in Literature",
        "lang": "en",
        "topic": "tagore",
        "confidence": 0.98,
    },
    {
        "subject": "গীতাঞ্জলি",
        "predicate": "সংজ্ঞা",
        "obj": "রবীন্দ্রনাথ ঠাকুরের কবিতার সংকলন; ১৯১৩ সালে সাহিত্যে নোবেল পুরস্কার জয় করে",
        "lang": "bn",
        "topic": "tagore",
        "confidence": 0.98,
    },
    {
        "subject": "Gitanjali",
        "predicate": "meaning",
        "obj": "Song Offerings",
        "lang": "en",
        "topic": "tagore",
        "confidence": 0.95,
    },
    # --- Rabindra Sangeet ---
    {
        "subject": "Rabindra Sangeet",
        "predicate": "definition",
        "obj": "songs written and composed by Rabindranath Tagore; over 2000 songs",
        "lang": "en",
        "topic": "songs",
        "confidence": 0.98,
    },
    {
        "subject": "রবীন্দ্রসঙ্গীত",
        "predicate": "সংজ্ঞা",
        "obj": "রবীন্দ্রনাথ ঠাকুরের লেখা ও সুরকৃত গান; ২০০০-এর বেশি গান",
        "lang": "bn",
        "topic": "songs",
        "confidence": 0.98,
    },
    {
        "subject": "Amar Sonar Bangla",
        "predicate": "definition",
        "obj": "song by Rabindranath Tagore (1905); national anthem of Bangladesh",
        "lang": "en",
        "topic": "songs",
        "confidence": 0.98,
    },
    {
        "subject": "আমার সোনার বাংলা",
        "predicate": "সংজ্ঞা",
        "obj": "রবীন্দ্রনাথ ঠাকুরের গান (১৯০৫); বাংলাদেশের জাতীয় সঙ্গীত",
        "lang": "bn",
        "topic": "songs",
        "confidence": 0.98,
    },
    {
        "subject": "Jana Gana Mana",
        "predicate": "definition",
        "obj": "song by Rabindranath Tagore (1911); national anthem of India",
        "lang": "en",
        "topic": "songs",
        "confidence": 0.98,
    },
    # --- Nazrul ---
    {
        "subject": "Kazi Nazrul Islam",
        "predicate": "definition",
        "obj": "Bengali poet known as the Rebel Poet (1899-1976); National Poet of Bangladesh",
        "lang": "en",
        "topic": "nazrul",
        "confidence": 0.98,
    },
    {
        "subject": "কাজি নজরুল ইসলাম",
        "predicate": "সংজ্ঞা",
        "obj": "বাঙালি কবি, বিদ্রোহী কবি নামে পরিচিত (১৮৯৯-১৯৭৬); বাংলাদেশের জাতীয় কবি",
        "lang": "bn",
        "topic": "nazrul",
        "confidence": 0.98,
    },
    {
        "subject": "Kazi Nazrul Islam",
        "predicate": "born",
        "obj": "25 May 1899, Churulia, West Bengal",
        "lang": "en",
        "topic": "nazrul",
        "confidence": 0.98,
    },
    {
        "subject": "কাজি নজরুল ইসলাম",
        "predicate": "জন্ম",
        "obj": "২৫ মে ১৮৯৯, চুরুলিয়া, পশ্চিমবঙ্গ",
        "lang": "bn",
        "topic": "nazrul",
        "confidence": 0.98,
    },
    {
        "subject": "Kazi Nazrul Islam",
        "predicate": "died",
        "obj": "29 August 1976, Dhaka; buried beside the Dhaka University central mosque",
        "lang": "en",
        "topic": "nazrul",
        "confidence": 0.98,
    },
    {
        "subject": "কাজি নজরুল ইসলাম",
        "predicate": "মৃত্যু",
        "obj": "২৯ আগস্ট ১৯৭৬, ঢাকা; ঢাকা বিশ্ববিদ্যালয়ের কেন্দ্রীয় মসজিদের পাশে সমাধিস্থ",
        "lang": "bn",
        "topic": "nazrul",
        "confidence": 0.98,
    },
    {
        "subject": "Kazi Nazrul Islam",
        "predicate": "title",
        "obj": "Rebel Poet (Bidrohi Kobi); National Poet of Bangladesh (1972)",
        "lang": "en",
        "topic": "nazrul",
        "confidence": 0.98,
    },
    {
        "subject": "কাজি নজরুল ইসলাম",
        "predicate": "উপাধি",
        "obj": "বিদ্রোহী কবি; বাংলাদেশের জাতীয় কবি (১৯৭২)",
        "lang": "bn",
        "topic": "nazrul",
        "confidence": 0.98,
    },
    {
        "subject": "Bidrohi",
        "predicate": "definition",
        "obj": "Nazrul's most famous poem, published 1922; expresses human defiance against oppression",
        "lang": "en",
        "topic": "nazrul",
        "confidence": 0.98,
    },
    {
        "subject": "বিদ্রোহী",
        "predicate": "সংজ্ঞা",
        "obj": "নজরুলের সবচেয়ে বিখ্যাত কবিতা, ১৯২২ সালে প্রকাশিত; নিয়ন্ত্রণের বিরুদ্ধে মানুষের বিদ্রোহের প্রকাশ",
        "lang": "bn",
        "topic": "nazrul",
        "confidence": 0.98,
    },
    {
        "subject": "Kazi Nazrul Islam",
        "predicate": "founded",
        "obj": "Dhumketu newspaper, 1922",
        "lang": "en",
        "topic": "nazrul",
        "confidence": 0.98,
    },
    {
        "subject": "Dhumketu",
        "predicate": "definition",
        "obj": "literary and political weekly magazine founded by Kazi Nazrul Islam in 1922",
        "lang": "en",
        "topic": "nazrul",
        "confidence": 0.98,
    },
    {
        "subject": "ধূমকেতু",
        "predicate": "সংজ্ঞা",
        "obj": "কাজি নজরুল ইসলামের ১৯২২ সালে প্রতিষ্ঠিত সাহিত্যিক ও রাজনৈতিক সাপ্তাহিক পত্রিকা",
        "lang": "bn",
        "topic": "nazrul",
        "confidence": 0.98,
    },
    {
        "subject": "কাজি নজরুল ইসলাম",
        "predicate": "প্রতিষ্ঠা",
        "obj": "১৯২২ সালে ধূমকেতু সংবাদপত্র",
        "lang": "bn",
        "topic": "nazrul",
        "confidence": 0.98,
    },
    # --- Nazrul Geeti ---
    {
        "subject": "Nazrul Geeti",
        "predicate": "definition",
        "obj": "over 3000 songs written and composed by Kazi Nazrul Islam",
        "lang": "en",
        "topic": "songs",
        "confidence": 0.98,
    },
    {
        "subject": "নজরুলগীতি",
        "predicate": "সংজ্ঞা",
        "obj": "কাজি নজরুল ইসলামের লেখা ও সুরকৃত ৩০০০-এর বেশি গান",
        "lang": "bn",
        "topic": "songs",
        "confidence": 0.98,
    },
    # --- Jibanananda ---
    {
        "subject": "Jibanananda Das",
        "predicate": "definition",
        "obj": "modernist Bengali poet (1899-1954); known for sensual imagery of Bengal",
        "lang": "en",
        "topic": "jibanananda",
        "confidence": 0.98,
    },
    {
        "subject": "জীবনানন্দ দাশ",
        "predicate": "সংজ্ঞা",
        "obj": "আধুনিক বাঙালি কবি (১৮৯৯-১৯৫৪); বাংলার প্রাকৃতিক রূপ ও অনুভূতির কবি",
        "lang": "bn",
        "topic": "jibanananda",
        "confidence": 0.98,
    },
    {
        "subject": "Jibanananda Das",
        "predicate": "born",
        "obj": "17 February 1899, Barisal, Bengal",
        "lang": "en",
        "topic": "jibanananda",
        "confidence": 0.98,
    },
    {
        "subject": "জীবনানন্দ দাশ",
        "predicate": "জন্ম",
        "obj": "১৭ ফেব্রুয়ারি ১৮৯৯, বরিশাল",
        "lang": "bn",
        "topic": "jibanananda",
        "confidence": 0.98,
    },
    {
        "subject": "Jibanananda Das",
        "predicate": "died",
        "obj": "22 October 1954, Kolkata, in a tram accident",
        "lang": "en",
        "topic": "jibanananda",
        "confidence": 0.98,
    },
    {
        "subject": "জীবনানন্দ দাশ",
        "predicate": "মৃত্যু",
        "obj": "২২ অক্টোবর ১৯৫৪, কলকাতায়, ট্রাম দুর্ঘটনায়",
        "lang": "bn",
        "topic": "jibanananda",
        "confidence": 0.98,
    },
    {
        "subject": "Bonolata Sen",
        "predicate": "definition",
        "obj": "Jibanananda Das's most famous poem (1942); ends with 'hoyto ebar phire asi'",
        "lang": "en",
        "topic": "jibanananda",
        "confidence": 0.98,
    },
    {
        "subject": "বনলতা সেন",
        "predicate": "সংজ্ঞা",
        "obj": "জীবনানন্দ দাশের সবচেয়ে বিখ্যাত কবিতা (১৯৪২); সমাপ্তি 'হয়তো এবার ফিরে আসি'",
        "lang": "bn",
        "topic": "jibanananda",
        "confidence": 0.98,
    },
    {
        "subject": "Rupasi Bangla",
        "predicate": "definition",
        "obj": "poem collection by Jibanananda Das (1957, posthumous) celebrating beautiful Bengal",
        "lang": "en",
        "topic": "jibanananda",
        "confidence": 0.98,
    },
    {
        "subject": "রূপসী বাংলা",
        "predicate": "সংজ্ঞা",
        "obj": "জীবনানন্দ দাশের কবিতার সংকলন (১৯৫৭, মৃত্যুর পর প্রকাশিত); সুন্দর বাংলার প্রতি উৎসর্গ",
        "lang": "bn",
        "topic": "jibanananda",
        "confidence": 0.98,
    },
    # --- Renaissance ---
    {
        "subject": "Bengali Renaissance",
        "predicate": "definition",
        "obj": "19th-20th century cultural awakening in Bengal; Tagore, Bankimchandra and others",
        "lang": "en",
        "topic": "renaissance",
        "confidence": 0.95,
    },
    {
        "subject": "বাংলার নবজাগরণ",
        "predicate": "সংজ্ঞা",
        "obj": "১৯-২০ শতকের বাংলা সাংস্কৃতিক জাগরণ; ঠাকুর, বঙ্কিমচন্দ্র প্রমুখ",
        "lang": "bn",
        "topic": "renaissance",
        "confidence": 0.95,
    },
    {
        "subject": "Bankimchandra Chattopadhyay",
        "predicate": "definition",
        "obj": "Bengali novelist (1838-1894); wrote Anandamath and Vande Mataram (1882)",
        "lang": "en",
        "topic": "renaissance",
        "confidence": 0.98,
    },
    {
        "subject": "বঙ্কিমচন্দ্র চট্টোপাধ্যায়",
        "predicate": "সংজ্ঞা",
        "obj": "বাঙালি ঔপন্যাসিক (১৮৩৮-১৮৯৪); আনন্দমঠ ও বন্দে মাতরম (১৮৮২) রচয়িতা",
        "lang": "bn",
        "topic": "renaissance",
        "confidence": 0.98,
    },
    {
        "subject": "Anandamath",
        "predicate": "definition",
        "obj": "Bankimchandra's 1882 historical novel; contains the song Vande Mataram",
        "lang": "en",
        "topic": "renaissance",
        "confidence": 0.98,
    },
    {
        "subject": "আনন্দমঠ",
        "predicate": "সংজ্ঞা",
        "obj": "বঙ্কিমচন্দ্রের ১৮৮২ সালের ঐতিহাসিক উপন্যাস; বন্দে মাতরম গান এতে স্থান পেয়েছে",
        "lang": "bn",
        "topic": "renaissance",
        "confidence": 0.98,
    },
    {
        "subject": "Vande Mataram",
        "predicate": "definition",
        "obj": "patriotic song by Bankimchandra (1882); national song of India",
        "lang": "en",
        "topic": "renaissance",
        "confidence": 0.98,
    },
    {
        "subject": "বন্দে মাতরম",
        "predicate": "সংজ্ঞা",
        "obj": "বঙ্কিমচন্দ্রের দেশাত্মবোধক গান (১৮৮২); ভারতের জাতীয় সঙ্গীত",
        "lang": "bn",
        "topic": "renaissance",
        "confidence": 0.98,
    },
]

LITERATURE_RULES: List[Dict[str, Any]] = [
    {
        "rule": "If a question asks 'who is X?' about a poet, answer with the poet's definition fact.",
        "rationale": "Definition facts are the canonical first response for 'who' questions.",
        "lang": "en",
        "topic": "renaissance",
    },
    {
        "rule": "If a question asks 'ki?' (what?) in Bengali, answer with the definition or meaning fact.",
        "rationale": "'কী' questions map to definition facts in both languages.",
        "lang": "bn",
        "topic": "renaissance",
    },
    {
        "rule": "Never claim uncertain biographical details; literature facts must be established and dated.",
        "rationale": "Verified-facts-only policy for the literature curriculum.",
        "lang": "en",
        "topic": "renaissance",
    },
]

LITERATURE_EXAMPLES: List[Dict[str, Any]] = [
    {
        "input": "Who wrote Gitanjali?",
        "output": "Gitanjali was written by Rabindranath Tagore; it won the 1913 Nobel Prize in Literature",
        "lang": "en",
        "confidence": 0.95,
    },
    {
        "input": "গীতাঞ্জলি কী?",
        "output": "গীতাঞ্জলি রবীন্দ্রনাথ ঠাকুরের কবিতার সংকলন; ১৯১৩ সালে সাহিত্যে নোবেল পুরস্কার জয় করে",
        "lang": "bn",
        "confidence": 0.95,
    },
    {
        "input": "Who is Kazi Nazrul Islam?",
        "output": "Kazi Nazrul Islam is the Rebel Poet of Bengal (1899-1976) and the National Poet of Bangladesh",
        "lang": "en",
        "confidence": 0.95,
    },
    {
        "input": "বিদ্রোহী কবিতা কে লিখেছেন?",
        "output": "বিদ্রোহী কবিতাটি লিখেছেন কাজি নজরুল ইসলাম, ১৯২২ সালে প্রকাশিত",
        "lang": "bn",
        "confidence": 0.95,
    },
    {
        "input": "Bonolata Sen ki?",
        "output": "Bonolata Sen is Jibanananda Das's most famous poem (1942); it ends with 'hoyto ebar phire asi'",
        "lang": "en",
        "confidence": 0.95,
    },
    {
        "input": "বনলতা সেন কে?",
        "output": "বনলতা সেন জীবনানন্দ দাশের সবচেয়ে বিখ্যাত কবিতা (১৯৪২)",
        "lang": "bn",
        "confidence": 0.95,
    },
    {
        "input": "Who wrote the Indian national anthem?",
        "output": "Rabindranath Tagore wrote Jana Gana Mana, the national anthem of India (1911)",
        "lang": "en",
        "confidence": 0.95,
    },
    {
        "input": "আমার সোনার বাংলা কার লেখা?",
        "output": "আমার সোনার বাংলা রবীন্দ্রনাথ ঠাকুরের লেখা (১৯০৫); বাংলাদেশের জাতীয় সঙ্গীত",
        "lang": "bn",
        "confidence": 0.95,
    },
]

LITERATURE_TESTS: List[Dict[str, Any]] = [
        {
        "id": "p31_tagore_nobel",
        "input": "tagore definition?",
        "expected_output": "1913",
        "lang": "en",
        "confidence": 0.95,
    },
        {
        "id": "p31_tagore_nobel_bn",
        "input": "রবীন্দ্রনাথ ঠাকুরের পরিচয়?",
        "expected_output": "১৯১৩",
        "lang": "bn",
        "confidence": 0.95,
    },
        {
        "id": "p31_gitanjali_year",
        "input": "gitanjali definition?",
        "expected_output": "1913",
        "lang": "en",
        "confidence": 0.95,
    },
        {
        "id": "p31_tagore_birth",
        "input": "rabindranath tagore definition?",
        "expected_output": "1861",
        "lang": "en",
        "confidence": 0.95,
    },
        {
        "id": "p31_nazrul_death",
        "input": "kazi nazrul islam definition?",
        "expected_output": "1976",
        "lang": "en",
        "confidence": 0.95,
    },
        {
        "id": "p31_bidrohi_year",
        "input": "bidrohi definition?",
        "expected_output": "1922",
        "lang": "en",
        "confidence": 0.95,
    },
        {
        "id": "p31_jibanananda_death",
        "input": "jibanananda das definition?",
        "expected_output": "1954",
        "lang": "en",
        "confidence": 0.95,
    },
        {
        "id": "p31_vande_mataram_year",
        "input": "vande mataram definition?",
        "expected_output": "1882",
        "lang": "en",
        "confidence": 0.95,
    },
        {
        "id": "p31_visva_bharati_year",
        "input": "visva-bharati definition?",
        "expected_output": "1921",
        "lang": "en",
        "confidence": 0.95,
    },
        {
        "id": "p31_bonolata_year",
        "input": "bonolata sen definition?",
        "expected_output": "1942",
        "lang": "en",
        "confidence": 0.95,
    },
]

# ---------------------------------------------------------------------------
# Provenance: content hash computed from the canonical payload
# ---------------------------------------------------------------------------

def _build_payload() -> str:
    """Canonical payload for the content hash (order matters)."""
    import json

    parts: List[str] = []
    parts.append(json.dumps(LITERATURE_SYNONYMS, sort_keys=True, ensure_ascii=False))
    parts.append(json.dumps(LITERATURE_CONCEPTS, sort_keys=True, ensure_ascii=False))
    parts.append(json.dumps(LITERATURE_RELATIONS, sort_keys=True, ensure_ascii=False))
    parts.append(json.dumps(LITERATURE_FACTS, sort_keys=True, ensure_ascii=False))
    parts.append(json.dumps(LITERATURE_FORMULAS, sort_keys=True, ensure_ascii=False))
    parts.append(json.dumps(LITERATURE_RULES, sort_keys=True, ensure_ascii=False))
    parts.append(json.dumps(LITERATURE_EXAMPLES, sort_keys=True, ensure_ascii=False))
    parts.append(json.dumps(LITERATURE_TESTS, sort_keys=True, ensure_ascii=False))
    return "".join(parts)

LITERATURE_FORMULAS: List[Dict[str, Any]] = []

_PAYLOAD = _build_payload()
_CONTENT_HASH = "sha256:" + hashlib.sha256(_PAYLOAD.encode("utf-8")).hexdigest()

_RECORD_SOURCE: Dict[str, Any] = {
    "title": "Misty Phase 31 Bengali literature curriculum",
    "url": "https://misty-brain.onrender.com",
    "retrieved_at": "2026-08-19T00:00:00Z",
    "content_hash": _CONTENT_HASH,
}


def literature_curriculum_package() -> TrainingPackageV2:
    """Return the Phase 31 bilingual Bengali literature curriculum package."""
    from datetime import datetime, timezone

    def _attach(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        out: List[Dict[str, Any]] = []
        for record in records:
            rec = dict(record)
            if "source_ref" not in rec:
                rec["source_ref"] = _RECORD_SOURCE
            out.append(rec)
        return out

    def _topic_concepts() -> List[Dict[str, Any]]:
        topics = {
            "tagore": "Rabindranath Tagore, his life, Gitanjali and works",
            "nazrul": "Kazi Nazrul Islam, Bidrohi, Dhumketu and Nazrul Geeti",
            "jibanananda": "Jibanananda Das, Bonolata Sen and Rupasi Bangla",
            "renaissance": "Bengali literary renaissance, Bankimchandra and anthems",
            "songs": "Rabindra Sangeet and Nazrul Geeti song traditions",
        }
        out: List[Dict[str, Any]] = []
        for topic, description in topics.items():
            out.append({
                "subject": "Misty",
                "predicate": "knows_topic",
                "obj": topic,
                "lang": "en",
                "source_ref": _RECORD_SOURCE,
            })
            out.append({
                "subject": topic,
                "predicate": "description",
                "obj": description,
                "lang": "en",
                "source_ref": _RECORD_SOURCE,
            })
        return out

    all_facts = _topic_concepts() + _attach(LITERATURE_FACTS)
    return TrainingPackageV2(
        package_id=PACKAGE_ID,
        department=PACKAGE_DEPARTMENT,
        version=PACKAGE_VERSION,
        languages=["bn", "en"],
        license=PACKAGE_LICENSE,
        source=SourceRef(
            title="Misty Bengali literature curriculum (Phase 31) "
            "— verified facts only",
            url="https://misty-brain.onrender.com",
            retrieved_at=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            content_hash=_CONTENT_HASH,
        ),
        concepts=[
            *({"name": "Literature", "type": "Field",
               "source_ref": _RECORD_SOURCE},
              {"name": "Poetry", "type": "Branch",
               "source_ref": _RECORD_SOURCE},
              {"name": "কবিতা", "type": "শাখা",
               "source_ref": _RECORD_SOURCE}),
            *_attach(LITERATURE_CONCEPTS),
        ],
        relations=_attach(LITERATURE_RELATIONS),
        facts=all_facts,
        tests=_attach(LITERATURE_TESTS),
    )


def register_literature_curriculum(brain: Any) -> int:
    """Load the Phase 31 Bengali literature curriculum into the brain's
    semantic memory and knowledge graph, and register the package.
    Returns the number of curriculum facts registered.
    """
    PackageRegistry().register(literature_curriculum_package())
    count = 0
    for entry in LITERATURE_CONCEPTS:
        if brain.concept_graph.get_concept_by_name(entry["name"]) is None:
            brain.concept_graph.create_concept(
                name=entry["name"],
                concept_type=entry.get("type", "Concept"),
            )
    for alias, canonical in LITERATURE_SYNONYMS.items():
        for fact in LITERATURE_FACTS:
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
    for fact in LITERATURE_FACTS:
        if brain.semantic_memory.query(
            subject=fact["subject"], predicate=fact["predicate"]
        ):
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
