"""
General knowledge curriculum (bilingual).

The existing curricula are deep but narrow: identity, mathematics, physics,
literature, and culture. Everyday questions about biology, the earth, space,
health, geography, and technology had no stored knowledge at all, so the brain
answered "I have not learned that yet" for very ordinary questions.

This module adds a compact set of well-established facts in both Bengali and
English. Every entry is a stable textbook-level statement rather than a
contested or fast-changing figure, so the brain does not present volatile data
as settled knowledge. Facts are stored with explicit provenance and slightly
below curriculum-perfect confidence, so user teaching and specialist curricula
still take precedence.
"""

from __future__ import annotations

from typing import Any, Dict, List

PACKAGE_ID = "misty-general-knowledge"

#: (subject, predicate, object) triples. Bengali and English forms are paired
#: so the bilingual bridge in :mod:`brain.knowledge.normalize` can link them.
GENERAL_FACTS: List[Dict[str, str]] = [
    # ---------------- life science ----------------
    {
        "subject": "photosynthesis",
        "predicate": "definition",
        "obj": "the process by which green plants use sunlight, water and carbon dioxide"
        " to make food and release oxygen",
    },
    {
        "subject": "সালোকসংশ্লেষণ",
        "predicate": "সংজ্ঞা",
        "obj": "যে প্রক্রিয়ায় সবুজ গাছ সূর্যালোক, পানি ও কার্বন ডাই অক্সাইড ব্যবহার করে খাদ্য তৈরি করে এবং অক্সিজেন ছাড়ে",
    },
    {
        "subject": "cell",
        "predicate": "definition",
        "obj": "the smallest structural and functional unit of a living organism",
    },
    {"subject": "কোষ", "predicate": "সংজ্ঞা", "obj": "জীবদেহের সবচেয়ে ছোট গঠনগত ও কার্যগত একক"},
    {
        "subject": "DNA",
        "predicate": "definition",
        "obj": "the molecule that carries the genetic instructions of living organisms",
    },
    {"subject": "ডিএনএ", "predicate": "সংজ্ঞা", "obj": "যে অণু জীবের বংশগত নির্দেশনা বহন করে"},
    {"subject": "oxygen", "predicate": "definition", "obj": "a gas in the air that most living things need to breathe"},
    {"subject": "অক্সিজেন", "predicate": "সংজ্ঞা", "obj": "বাতাসের যে গ্যাস অধিকাংশ জীবের শ্বাস নিতে প্রয়োজন"},
    {"subject": "heart", "predicate": "function", "obj": "pumps blood through the body"},
    {"subject": "হৃদয়", "predicate": "কাজ", "obj": "সারা শরীরে রক্ত সঞ্চালন করে"},
    {"subject": "lung", "predicate": "function", "obj": "takes in oxygen and removes carbon dioxide from the blood"},
    {"subject": "ফুসফুস", "predicate": "কাজ", "obj": "অক্সিজেন গ্রহণ করে এবং রক্ত থেকে কার্বন ডাই অক্সাইড বের করে"},
    {
        "subject": "brain",
        "predicate": "function",
        "obj": "controls the body and processes thought, memory and sensation",
    },
    {"subject": "মস্তিষ্ক", "predicate": "কাজ", "obj": "শরীর নিয়ন্ত্রণ করে এবং চিন্তা, স্মৃতি ও অনুভূতি প্রক্রিয়া করে"},
    {"subject": "blood", "predicate": "function", "obj": "carries oxygen, nutrients and waste through the body"},
    {"subject": "রক্ত", "predicate": "কাজ", "obj": "শরীরে অক্সিজেন, পুষ্টি ও বর্জ্য বহন করে"},
    {
        "subject": "vitamin",
        "predicate": "definition",
        "obj": "a nutrient the body needs in small amounts to stay healthy",
    },
    {"subject": "ভিটামিন", "predicate": "সংজ্ঞা", "obj": "সুস্থ থাকার জন্য শরীরের অল্প পরিমাণে প্রয়োজনীয় পুষ্টি উপাদান"},
    # ---------------- earth and space ----------------
    {
        "subject": "water cycle",
        "predicate": "definition",
        "obj": "the continuous movement of water through evaporation, condensation and precipitation",
    },
    {"subject": "পানিচক্র", "predicate": "সংজ্ঞা", "obj": "বাষ্পীভবন, ঘনীভবন ও বৃষ্টিপাতের মাধ্যমে পানির অবিরাম চলাচল"},
    {
        "subject": "earthquake",
        "predicate": "definition",
        "obj": "shaking of the ground caused by sudden movement of the earth's crust",
    },
    {"subject": "ভূমিকম্প", "predicate": "সংজ্ঞা", "obj": "ভূত্বকের আকস্মিক নড়াচড়ার ফলে ভূমির কম্পন"},
    {
        "subject": "volcano",
        "predicate": "definition",
        "obj": "an opening in the earth's surface through which lava, ash and gases erupt",
    },
    {"subject": "অগ্নিগিরি", "predicate": "সংজ্ঞা", "obj": "ভূপৃষ্ঠের যে মুখ দিয়ে লাভা, ছাই ও গ্যাস নির্গত হয়"},
    {
        "subject": "solar system",
        "predicate": "definition",
        "obj": "the sun together with the planets and other bodies that orbit it",
    },
    {"subject": "সৌরজগৎ", "predicate": "সংজ্ঞা", "obj": "সূর্য এবং তাকে প্রদক্ষিণ করা গ্রহ ও অন্যান্য বস্তুর সমষ্টি"},
    {
        "subject": "solar system",
        "predicate": "includes",
        "obj": "Mercury, Venus, Earth, Mars, Jupiter, Saturn, Uranus, Neptune",
    },
    {"subject": "সৌরজগৎ", "predicate": "অন্তর্ভুক্ত", "obj": "বুধ, শুক্র, পৃথিবী, মঙ্গল, বৃহস্পতি, শনি, ইউরেনাস, নেপচুন"},
    {
        "subject": "earth",
        "predicate": "definition",
        "obj": "the third planet from the sun and the only known planet with life",
    },
    {"subject": "পৃথিবী", "predicate": "সংজ্ঞা", "obj": "সূর্য থেকে তৃতীয় গ্রহ এবং একমাত্র জানা প্রাণধারী গ্রহ"},
    {"subject": "moon", "predicate": "definition", "obj": "the natural satellite that orbits the earth"},
    {"subject": "চাঁদ", "predicate": "সংজ্ঞা", "obj": "পৃথিবীকে প্রদক্ষিণ করা প্রাকৃতিক উপগ্রহ"},
    {"subject": "season", "predicate": "cause", "obj": "the tilt of the earth's axis as it orbits the sun"},
    {"subject": "ঋতু", "predicate": "কারণ", "obj": "সূর্যকে প্রদক্ষিণ করার সময় পৃথিবীর অক্ষের হেলে থাকা"},
    # ---------------- geography ----------------
    {"subject": "ocean", "predicate": "largest", "obj": "the Pacific Ocean"},
    {"subject": "মহাসাগর", "predicate": "বৃহত্তম", "obj": "প্রশান্ত মহাসাগর"},
    {"subject": "mountain", "predicate": "highest", "obj": "Mount Everest"},
    {"subject": "পর্বত", "predicate": "সর্বোচ্চ", "obj": "মাউন্ট এভারেস্ট"},
    {"subject": "desert", "predicate": "largest", "obj": "the Sahara"},
    {"subject": "মরুভূমি", "predicate": "বৃহত্তম", "obj": "সাহারা"},
    {"subject": "Pacific Ocean", "predicate": "definition", "obj": "the largest and deepest ocean on earth"},
    {"subject": "প্রশান্ত মহাসাগর", "predicate": "সংজ্ঞা", "obj": "পৃথিবীর বৃহত্তম ও গভীরতম মহাসাগর"},
    {
        "subject": "Mount Everest",
        "predicate": "definition",
        "obj": "the highest mountain above sea level, in the Himalayas",
    },
    {"subject": "মাউন্ট এভারেস্ট", "predicate": "সংজ্ঞা", "obj": "সমুদ্রপৃষ্ঠ থেকে পৃথিবীর সর্বোচ্চ পর্বতশৃঙ্গ, হিমালয়ে অবস্থিত"},
    {"subject": "Sahara", "predicate": "definition", "obj": "the largest hot desert in the world, in northern Africa"},
    {"subject": "সাহারা", "predicate": "সংজ্ঞা", "obj": "উত্তর আফ্রিকায় অবস্থিত পৃথিবীর বৃহত্তম উষ্ণ মরুভূমি"},
    {
        "subject": "Amazon",
        "predicate": "definition",
        "obj": "a major river in South America surrounded by the largest tropical rainforest",
    },
    {"subject": "আমাজন", "predicate": "সংজ্ঞা", "obj": "দক্ষিণ আমেরিকার প্রধান নদী, যার চারপাশে পৃথিবীর বৃহত্তম গ্রীষ্মমণ্ডলীয় বনভূমি"},
    {"subject": "Bangladesh", "predicate": "capital", "obj": "Dhaka"},
    {"subject": "Bangladesh", "predicate": "language", "obj": "Bengali"},
    {"subject": "India", "predicate": "language", "obj": "Hindi, English and many state languages"},
    {"subject": "ভারত", "predicate": "ভাষা", "obj": "হিন্দি, ইংরেজি এবং আরও অনেক রাজ্যভাষা"},
    # ---------------- civics and history ----------------
    {"subject": "India", "predicate": "independence", "obj": "15 August 1947"},
    {"subject": "ভারত", "predicate": "স্বাধীনতা", "obj": "১৫ আগস্ট ১৯৪৭"},
    {"subject": "Bangladesh", "predicate": "independence", "obj": "26 March 1971, with victory on 16 December 1971"},
    {"subject": "বাংলাদেশ", "predicate": "স্বাধীনতা", "obj": "২৬ মার্চ ১৯৭১, বিজয় ১৬ ডিসেম্বর ১৯৭১"},
    {
        "subject": "United Nations",
        "predicate": "definition",
        "obj": "an international organisation founded in 1945 to promote peace and cooperation",
    },
    {"subject": "জাতিসংঘ", "predicate": "সংজ্ঞা", "obj": "শান্তি ও সহযোগিতা প্রতিষ্ঠার জন্য ১৯৪৫ সালে গঠিত আন্তর্জাতিক সংস্থা"},
    {
        "subject": "democracy",
        "predicate": "definition",
        "obj": "a system of government in which citizens choose their representatives by voting",
    },
    {"subject": "গণতন্ত্র", "predicate": "সংজ্ঞা", "obj": "যে শাসনব্যবস্থায় নাগরিকরা ভোটের মাধ্যমে প্রতিনিধি নির্বাচন করে"},
    {
        "subject": "constitution",
        "predicate": "definition",
        "obj": "the fundamental set of laws and principles by which a state is governed",
    },
    {"subject": "সংবিধান", "predicate": "সংজ্ঞা", "obj": "যে মৌলিক আইন ও নীতিমালা অনুসারে রাষ্ট্র পরিচালিত হয়"},
    # ---------------- technology ----------------
    {
        "subject": "internet",
        "predicate": "definition",
        "obj": "a global network that connects computers so they can exchange information",
    },
    {"subject": "ইন্টারনেট", "predicate": "সংজ্ঞা", "obj": "বিশ্বব্যাপী নেটওয়ার্ক যা কম্পিউটারগুলোকে যুক্ত করে তথ্য বিনিময় করতে দেয়"},
    {
        "subject": "artificial intelligence",
        "predicate": "definition",
        "obj": "computer systems that perform tasks such as reasoning, recognition and decision making",
    },
    {"subject": "কৃত্রিম বুদ্ধিমত্তা", "predicate": "সংজ্ঞা", "obj": "যে কম্পিউটার ব্যবস্থা যুক্তি, শনাক্তকরণ ও সিদ্ধান্ত গ্রহণের কাজ করে"},
    {
        "subject": "computer",
        "predicate": "definition",
        "obj": "an electronic machine that stores and processes data using instructions",
    },
    {"subject": "কম্পিউটার", "predicate": "সংজ্ঞা", "obj": "নির্দেশ অনুসারে তথ্য সংরক্ষণ ও প্রক্রিয়াকরণ করা বৈদ্যুতিন যন্ত্র"},
    {
        "subject": "software",
        "predicate": "definition",
        "obj": "the programs and instructions that tell a computer what to do",
    },
    {"subject": "সফটওয়্যার", "predicate": "সংজ্ঞা", "obj": "যে প্রোগ্রাম ও নির্দেশনা কম্পিউটারকে কী করতে হবে তা বলে"},
    {"subject": "programming", "predicate": "definition", "obj": "writing instructions that a computer can execute"},
    {"subject": "প্রোগ্রামিং", "predicate": "সংজ্ঞা", "obj": "কম্পিউটার চালাতে পারে এমন নির্দেশ লেখার কাজ"},
    {"subject": "electricity", "predicate": "definition", "obj": "energy carried by moving electric charge"},
    {"subject": "বিদ্যুৎ", "predicate": "সংজ্ঞা", "obj": "চলমান বৈদ্যুতিক চার্জ দ্বারা বাহিত শক্তি"},
    # ---------------- language and learning ----------------
    {"subject": "language", "predicate": "definition", "obj": "a system of words and rules people use to communicate"},
    {"subject": "ভাষা", "predicate": "সংজ্ঞা", "obj": "যে শব্দ ও নিয়মের ব্যবস্থা দিয়ে মানুষ ভাব প্রকাশ করে"},
    {"subject": "grammar", "predicate": "definition", "obj": "the rules that describe how words combine in a language"},
    {"subject": "ব্যাকরণ", "predicate": "সংজ্ঞা", "obj": "ভাষায় শব্দ কীভাবে যুক্ত হয় তা বর্ণনা করা নিয়মাবলি"},
    {
        "subject": "education",
        "predicate": "definition",
        "obj": "the process of gaining knowledge and skills through study and teaching",
    },
    {"subject": "শিক্ষা", "predicate": "সংজ্ঞা", "obj": "অধ্যয়ন ও শিক্ষাদানের মাধ্যমে জ্ঞান ও দক্ষতা অর্জনের প্রক্রিয়া"},
]

#: Concepts worth having in the graph so association and listing work.
GENERAL_CONCEPTS: List[Dict[str, str]] = [
    {"name": "photosynthesis", "type": "Process"},
    {"name": "সালোকসংশ্লেষণ", "type": "প্রক্রিয়া"},
    {"name": "solar system", "type": "Astronomy"},
    {"name": "সৌরজগৎ", "type": "মহাকাশ"},
    {"name": "continent", "type": "Geography"},
    {"name": "মহাদেশ", "type": "ভূগোল"},
    {"name": "artificial intelligence", "type": "Technology"},
    {"name": "কৃত্রিম বুদ্ধিমত্তা", "type": "প্রযুক্তি"},
    {"name": "democracy", "type": "Civics"},
    {"name": "গণতন্ত্র", "type": "পৌরনীতি"},
]


def register_general_knowledge(brain: Any) -> int:
    """Load the general-knowledge facts into ``brain``.

    Existing facts are never overwritten, so identity, curriculum, and
    user-taught knowledge keep priority. Returns the number of facts stored.
    """
    for entry in GENERAL_CONCEPTS:
        if brain.concept_graph.get_concept_by_name(entry["name"]) is None:
            brain.concept_graph.create_concept(name=entry["name"], concept_type=entry.get("type", "Entity"))

    stored = 0
    for fact in GENERAL_FACTS:
        if brain.semantic_memory.query(subject=fact["subject"], predicate=fact["predicate"]):
            continue
        brain.semantic_memory.store_fact(
            subject=fact["subject"],
            predicate=fact["predicate"],
            obj=fact["obj"],
            confidence=0.93,
            source=PACKAGE_ID,
        )
        stored += 1
    return stored
