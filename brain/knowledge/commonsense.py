"""
Commonsense Knowledge Layer.

A curated, bilingual (Bengali/English) seed of everyday world facts
that lets MISTY answer questions like "আকাশের রঙ কি?" or
"পানি কি দিয়ে বানানো হয়?" by *deriving* an answer from stored
concepts rather than echoing a memorized phrase.

Each fact is a triple (subject, predicate, object) tagged with a
confidence and a source. On startup,
``register_commonsense_layer(brain)`` loads these triples into the
Brain's ``semantic_memory`` so they participate in ordinary fact
lookups and in ``InferenceSynthesizer`` chain reasoning.
"""

from dataclasses import dataclass
from typing import Any, Dict, List


@dataclass
class CommonsenseFact:
    """One curated world fact."""

    subject: str
    predicate: str
    obj: str
    confidence: float = 0.95
    source: str = "commonsense_layer"


# ---------------------------------------------------------------------------
# Curated bilingual commonsense facts
# ---------------------------------------------------------------------------

_COMMONSENSE_FACTS: List[CommonsenseFact] = [
    # ---------- আকাশ, আবহাওয়া ও পৃথিবী (sky, weather, earth) ----------
    CommonsenseFact("আকাশ", "color", "নীল"),
    CommonsenseFact("sky", "color", "blue"),
    CommonsenseFact("আকাশ", "day_color_reason", "সূর্যের আলো বায়ুতে ছড়িয়ে পড়ে"),
    CommonsenseFact("sky", "day_color_reason", "sunlight scatters in the air"),
    CommonsenseFact("সূর্য", "is_a", "তারা"),
    CommonsenseFact("sun", "is_a", "star"),
    CommonsenseFact("সূর্য", "gives", "আলো ও তাপ"),
    CommonsenseFact("sun", "gives", "light and heat"),
    CommonsenseFact("সূর্য", "rises_in", "পূর্ব"),
    CommonsenseFact("sun", "rises_in", "the east"),
    CommonsenseFact("সূর্য", "sets_in", "পশ্চিম"),
    CommonsenseFact("sun", "sets_in", "the west"),
    CommonsenseFact("চাঁদ", "is_a", "পৃথিবীর উপগ্রহ"),
    CommonsenseFact("moon", "is_a", "satellite of the earth"),
    CommonsenseFact("চাঁদ", "glows_at", "রাতে"),
    CommonsenseFact("moon", "glows_at", "night"),
    CommonsenseFact("পৃথিবী", "is_a", "গ্রহ"),
    CommonsenseFact("earth", "is_a", "planet"),
    CommonsenseFact("পৃথিবী", "has", "একটি চাঁদ"),
    CommonsenseFact("earth", "has", "one moon"),
    CommonsenseFact("বৃষ্টি", "is_made_of", "পানির ফোঁটা"),
    CommonsenseFact("rain", "is_made_of", "water droplets"),
    CommonsenseFact("বৃষ্টি", "falls_from", "মেঘ"),
    CommonsenseFact("rain", "falls_from", "clouds"),
    CommonsenseFact("মেঘ", "is_made_of", "জলীয় বাষ্প"),
    CommonsenseFact("clouds", "is_made_of", "water vapor"),
    CommonsenseFact("দিন", "has", "রাত"),
    CommonsenseFact("day", "has", "night"),
    CommonsenseFact("দিন হয়", "because", "সূর্যের আলো"),
    CommonsenseFact("daylight", "because", "sunlight"),
    CommonsenseFact("রাত", "because", "সূর্যের আলো অনুপস্থিতি"),
    CommonsenseFact("night", "because", "absence of sunlight"),
    CommonsenseFact("বাংলাদেশ", "capital", "ঢাকা"),
    CommonsenseFact("Bangladesh", "capital", "Dhaka"),
    CommonsenseFact("বাংলাদেশ", "language", "বাংলা"),
    CommonsenseFact("Bangladesh", "language", "Bengali"),
    CommonsenseFact("ভারত", "capital", "নয়াদিল্লি"),
    CommonsenseFact("India", "capital", "New Delhi"),
    CommonsenseFact("West Bengal", "capital", "Kolkata"),
    CommonsenseFact("পশ্চিমবঙ্গ", "capital", "কলকাতা"),
    CommonsenseFact("বাংলাদেশ", "continent", "এশিয়া"),
    CommonsenseFact("Bangladesh", "continent", "Asia"),
    CommonsenseFact("কলকাতা", "is_a", "বাংলাদেশের পাশের শহর"),
    CommonsenseFact("Dhaka", "is_a", "capital city"),
    CommonsenseFact("ঢাকা", "is_a", "রাজধানী শহর"),
    CommonsenseFact("নদী", "water_flows_in", "নদী"),
    CommonsenseFact("water", "flows_in", "river"),
    CommonsenseFact("পানি", "flows_in", "নদী"),
    CommonsenseFact("সমুদ্রের পানি", "taste", "নোনা"),
    CommonsenseFact("sea water", "taste", "salty"),
    CommonsenseFact("নদীর পানি", "taste", "তাড়া"),
    CommonsenseFact("river water", "taste", "fresh"),

    # ---------- পানি ও পদার্থ (water, matter) ----------
    CommonsenseFact("পানি", "is_a", "তরল পদার্থ"),
    CommonsenseFact("water", "is_a", "liquid"),
    CommonsenseFact("পানি", "color", "স্বচ্ছ"),
    CommonsenseFact("water", "color", "colorless"),
    CommonsenseFact("পানি", "need_for", "জীবন"),
    CommonsenseFact("water", "need_for", "life"),
    CommonsenseFact("বরফ", "is_frozen", "পানি"),
    CommonsenseFact("ice", "is_frozen", "water"),
    CommonsenseFact("বরফ", "is_a", "কঠিন"),
    CommonsenseFact("ice", "is_a", "solid"),
    CommonsenseFact("বরফ", "coldness", "ঠান্ডা"),
    CommonsenseFact("ice", "coldness", "cold"),
    CommonsenseFact("বাষ্প", "is_heated", "পানি"),
    CommonsenseFact("steam", "is_heated", "water"),
    CommonsenseFact("বাষ্প", "is_a", "গ্যাস"),
    CommonsenseFact("steam", "is_a", "gas"),
    CommonsenseFact("বাষ্প", "hotness", "গরম"),
    CommonsenseFact("steam", "hotness", "hot"),
    CommonsenseFact("পানি", "boils_at", "১০০ ডিগ্রি সেলসিয়াস"),
    CommonsenseFact("water", "boils_at", "100 degrees celsius"),
    CommonsenseFact("পানি", "freezes_at", "০ (শূন্য) ডিগ্রি সেলসিয়াস"),  # noqa: RUF001
    CommonsenseFact("water", "freezes_at", "0 degrees celsius"),

    # ---------- আগুন ও তাপ (fire, heat) ----------
    CommonsenseFact("আগুন", "heat", "গরম"),
    CommonsenseFact("fire", "heat", "hot"),
    CommonsenseFact("আগুন", "gives", "তাপ ও আলো"),
    CommonsenseFact("fire", "gives", "heat and light"),
    CommonsenseFact("আগুন", "danger", "পুড়িয়ে দেয়"),
    CommonsenseFact("fire", "danger", "can burn"),
    CommonsenseFact("সূর্যের আলো", "color", "সাদা/কিছুটা সোনালি"),
    CommonsenseFact("sunlight", "color", "white/golden"),

    # ---------- উদ্ভিদ ও প্রাণী (plants, animals) ----------
    CommonsenseFact("গাছ", "makes_food_by", "সালোকসংশ্লেষণ"),
    CommonsenseFact("trees", "makes_food_by", "photosynthesis"),
    CommonsenseFact("পাতা", "color", "সবুজ"),
    CommonsenseFact("leaves", "color", "green"),
    CommonsenseFact("ফুল", "need", "জল, আলো, মাটি"),
    CommonsenseFact("plants", "need", "water, light, soil"),
    CommonsenseFact("ঘাস", "color", "সবুজ"),
    CommonsenseFact("grass", "color", "green"),
    CommonsenseFact("গরু", "gives", "দুধ"),
    CommonsenseFact("cow", "gives", "milk"),
    CommonsenseFact("গরু", "is_a", "পশু"),
    CommonsenseFact("cow", "is_a", "animal"),
    CommonsenseFact("মানুষ", "is_a", "প্রাণী"),
    CommonsenseFact("human", "is_a", "animal"),
    CommonsenseFact("মানুষ", "is_a", "বুদ্ধিমান প্রাণী"),
    CommonsenseFact("human", "is_a", "intelligent animal"),
    CommonsenseFact("মাছ", "lives_in", "পানিতে"),
    CommonsenseFact("fish", "lives_in", "water"),
    CommonsenseFact("পাখি", "can_do", "ওড়া"),
    CommonsenseFact("birds", "can_do", "fly"),
    CommonsenseFact("মুরগি", "gives", "ডিম"),
    CommonsenseFact("hen", "gives", "eggs"),
    CommonsenseFact("মধু", "makes", "মৌমাছি"),
    CommonsenseFact("honey", "makes", "bees"),
    CommonsenseFact("মধু", "taste", "মিষ্টি"),
    CommonsenseFact("honey", "taste", "sweet"),
    CommonsenseFact("লেবু", "taste", "টক"),
    CommonsenseFact("lemon", "taste", "sour"),
    CommonsenseFact("চিনি", "taste", "মিষ্টি"),
    CommonsenseFact("sugar", "taste", "sweet"),
    CommonsenseFact("লবণ", "taste", "নোনা"),
    CommonsenseFact("salt", "taste", "salty"),

    # ---------- মানবদেহ (human body) ----------
    CommonsenseFact("মানুষের চোখ", "function", "দেখা"),
    CommonsenseFact("human eyes", "function", "sight"),
    CommonsenseFact("মানুষের কান", "function", "শোনা"),
    CommonsenseFact("human ears", "function", "hearing"),
    CommonsenseFact("মানুষের নাক", "function", "গন্ধ শোঁকা"),
    CommonsenseFact("human nose", "function", "smell"),
    CommonsenseFact("হৃদয়", "function", "রক্ত পাম্প করা"),
    CommonsenseFact("heart", "function", "pumps blood"),
    CommonsenseFact("মানুষ", "breathe", "বায়ু/অক্সিজেন"),
    CommonsenseFact("human", "breathe", "air/oxygen"),
    CommonsenseFact("মানুষ", "has", "দুই হাত"),
    CommonsenseFact("human", "has", "two hands"),
    CommonsenseFact("মানুষ", "has", "দুই পা"),
    CommonsenseFact("human", "has", "two legs"),
    CommonsenseFact("মানুষ", "needs", "ঘুম"),
    CommonsenseFact("human", "needs", "sleep"),
    CommonsenseFact("মানুষ", "needs", "খাবার"),
    CommonsenseFact("human", "needs", "food"),
    CommonsenseFact("মানুষ", "needs", "পানি"),
    CommonsenseFact("human", "needs", "water"),
    CommonsenseFact("বায়ু", "is_a", "গ্যাসের মিশ্রণ"),
    CommonsenseFact("air", "is_a", "mixture of gases"),
    CommonsenseFact("অক্সিজেন", "need_for", "বাঁচা"),
    CommonsenseFact("oxygen", "need_for", "breathing/life"),

    # ---------- সংখ্যা, সময় ও সাধারণ (numbers, time, general) ----------
    CommonsenseFact("সপ্তাহ", "has", "সাত দিন"),
    CommonsenseFact("week", "has", "seven days"),
    CommonsenseFact("বছর", "has", "বারো মাস"),
    CommonsenseFact("year", "has", "twelve months"),
    CommonsenseFact("দিন", "has", "চব্বিশ ঘণ্টা"),
    CommonsenseFact("day", "has", "twenty four hours"),
    CommonsenseFact("ঘণ্টা", "has", "ষাট মিনিট"),
    CommonsenseFact("hour", "has", "sixty minutes"),
    CommonsenseFact("সালমান", "example", "নাম"),
    CommonsenseFact("রবিবার", "is_a", "সাপ্তাহিক ছুটি"),
    CommonsenseFact("Friday", "is_a", "weekly holiday"),
    CommonsenseFact("শুক্রবার", "is_a", "সাপ্তাহিক ছুটি"),
    CommonsenseFact("রোদ", "comes_from", "সূর্য"),
    CommonsenseFact("sunlight", "comes_from", "the sun"),
    CommonsenseFact("ছায়া", "forms_when", "আলো আটকায়"),
    CommonsenseFact("shadow", "forms_when", "light is blocked"),
    CommonsenseFact("আয়না", "shows", "প্রতিবিম্ব"),
    CommonsenseFact("mirror", "shows", "reflection"),
    CommonsenseFact("বিদ্যুৎ", "gives", "আলো ও শক্তি"),
    CommonsenseFact("electricity", "gives", "light and power"),
    CommonsenseFact("ফোন", "use", "কথা বলা"),
    CommonsenseFact("phone", "use", "talking"),
    CommonsenseFact("মিস্টি", "is_a", "কৃত্রিম ব্রেইন"),
    CommonsenseFact("Misty", "is_a", "artificial brain"),
    CommonsenseFact("Misty", "creator", "Pixline Incorporate"),
    CommonsenseFact("মিস্টি", "creator", "Pixline Incorporate"),
    CommonsenseFact("Pixline Incorporate", "founder", "Salauddin Mir"),
    CommonsenseFact("Salauddin Mir", "known_as", "Netvai"),
    CommonsenseFact("Netvai", "real_name", "Salauddin Mir"),

    # ---------- প্রযুক্তি (technology) ----------
    CommonsenseFact("স্যাটেলাইট", "is_a", "পৃথিবীর চারদিকে ঘূর্ণনরত যন্ত্র"),
    CommonsenseFact("satellite", "is_a", "a machine that orbits the earth"),
    CommonsenseFact("স্যাটেলাইট", "use", "যোগাযোগ ও আবহাওয়া পর্যবেক্ষণ"),
    CommonsenseFact("satellite", "use", "communication and weather observation"),
    CommonsenseFact("গুরুত্বাকর্ষণ", "is_a", "ভরের মধ্যে ক্রিয়াশীল আকর্ষণ বল"),
    CommonsenseFact("gravity", "is_a", "a force of attraction between masses"),
    CommonsenseFact("গুরুত্বাকর্ষণ", "why_reason", "ভরের কারণে সৃষ্টি হওয়া প্রাকৃতিক বল"),
    CommonsenseFact("gravity", "why_reason", "a natural force created by mass"),
    CommonsenseFact("কম্পিউটার", "is_a", "তথ্য প্রক্রিয়াকরণের যন্ত্র"),
    CommonsenseFact("computer", "is_a", "a machine that processes information"),
    CommonsenseFact("কম্পিউটার", "needs", "বিদ্যুত ও নির্দেশাবলী"),
    CommonsenseFact("computer", "needs", "electricity and instructions"),
    CommonsenseFact("ইন্টারনেট", "is_a", "বিশ্বের কম্পিউটারের সংযোগ জাল"),
    CommonsenseFact("internet", "is_a", "a worldwide network of computers"),
    CommonsenseFact("টিভি", "is_a", "ছবি ও শব্দের প্রকাশ যন্ত্র"),
    CommonsenseFact("tv", "is_a", "a device that displays images and sound"),
    CommonsenseFact("রোবট", "is_a", "স্বয়ংক্রিয় যন্ত্র যা মানুষের কাজ করে"),
    CommonsenseFact("robot", "is_a", "an automatic machine that does human tasks"),
    CommonsenseFact("বিদ্যুত", "powers", "যন্ত্র ও বাতি"),
    CommonsenseFact("electricity", "powers", "machines and lights"),
    CommonsenseFact("বাতি", "gives", "আলো"),
    CommonsenseFact("bulb", "gives", "light"),
]

# English question-word mapping used by InferenceSynthesizer to decide
# which predicate to look up when the question asks "what is X",
# "what color is X", "who created X" etc.
QUESTION_PATTERNS: List[Dict[str, Any]] = [
    # (predicate, english_phrases, bengali_phrases, answer_label_bn, answer_label_en)
    {
        "predicate": "color",
        "en": ["color", "colour", "রঙ", "রং"],
        "bn": ["রঙ", "রং"],
        "ans_bn": "রঙ",
        "ans_en": "color",
    },
    {
        "predicate": "is_a",
        "en": ["what is", "who is", "হলো", "কি", "কী", "কোনটা"],
        "bn": ["হলো", "কি", "কী", "কোনটা", "কে"],
        "ans_bn": "হলো",
        "ans_en": "is",
    },
    {
        "predicate": "capital",
        "en": ["capital", "রাজধানী"],
        "bn": ["রাজধানী"],
        "ans_bn": "রাজধানী",
        "ans_en": "capital",
    },
    {
        "predicate": "taste",
        "en": ["taste", "স্বাদ"],
        "bn": ["স্বাদ"],
        "ans_bn": "স্বাদ",
        "ans_en": "taste",
    },
    {
        "predicate": "creator",
        "en": ["created", "made by", "creator", "founder", "তৈরি", "বানিয়েছে", "প্রতিষ্ঠাতা"],
        "bn": ["তৈরি", "বানিয়েছে", "প্রতিষ্ঠাতা"],
        "ans_bn": "তৈরিকারী",
        "ans_en": "creator",
    },
    {
        "predicate": "gives",
        "en": ["gives", "দেয়", "প্রদান"],
        "bn": ["দেয়", "প্রদান"],
        "ans_bn": "দেয়",
        "ans_en": "gives",
    },
    {
        "predicate": "function",
        "en": ["function", "use", "কাজ", "কী কাজ"],
        "bn": ["কাজ", "কী কাজ"],
        "ans_bn": "কাজ",
        "ans_en": "function",
    },
    {
        "predicate": "lives_in",
        "en": ["lives", "থাকে", "বাস করে"],
        "bn": ["থাকে", "বাস করে"],
        "ans_bn": "থাকে",
        "ans_en": "lives",
    },
    {
        "predicate": "need",
        "en": ["need", "প্রয়োজন", "খাওয়া"],
        "bn": ["প্রয়োজন", "খাওয়া"],
        "ans_bn": "প্রয়োজন",
        "ans_en": "needs",
    },
    {
        "predicate": "boils_at",
        "en": ["boil", "সিদ্ধ"],
        "bn": ["সিদ্ধ", "ফোটে"],
        "ans_bn": "ফুটবিন্দু",
        "ans_en": "boiling point",
    },
    {
        "predicate": "can_do",
        "en": ["can do", "পারে"],
        "bn": ["পারে"],
        "ans_bn": "পারে",
        "ans_en": "can",
    },
    {
        "predicate": "falls_from",
        "en": ["falls from", "থেকে আসে", "ঝরে"],
        "bn": ["থেকে আসে", "ঝরে"],
        "ans_bn": "থেকে আসে",
        "ans_en": "falls from",
    },
    {
        "predicate": "is_made_of",
        "en": ["made of", "dieu banano", "দিয়ে বানানো"],
        "bn": ["দিয়ে বানানো", "দিয়ে তৈরি"],
        "ans_bn": "দিয়ে তৈরি",
        "ans_en": "made of",
    },
    {
        "predicate": "heat",
        "en": ["hot", "cold", "তাপ", "গরম", "ঠান্ডা"],
        "bn": ["তাপ", "গরম", "ঠান্ডা"],
        "ans_bn": "তাপ",
        "ans_en": "heat",
    },
    {
        "predicate": "hotness",
        "en": ["temperature", "hot", "temperature", "তাপমাত্রা"],
        "bn": ["তাপমাত্রা", "তাপ"],
        "ans_bn": "তাপ",
        "ans_en": "temperature",
    },
    {
        "predicate": "coldness",
        "en": ["cold", "ঠান্ডা"],
        "bn": ["ঠান্ডা"],
        "ans_bn": "ঠান্ডা",
        "ans_en": "cold",
    },
    {
        "predicate": "rises_in",
        "en": ["rises", "উদয়"],
        "bn": ["উদয়", "ওঠে"],
        "ans_bn": "উদয় হয়",
        "ans_en": "rises",
    },
    {
        "predicate": "flows_in",
        "en": ["flows", "বয়ে যায়"],
        "bn": ["বয়ে যায়", "বইতে"],
        "ans_bn": "বয়ে যায়",
        "ans_en": "flows",
    },
    {
        "predicate": "makes_food_by",
        "en": ["food", "খাবার"],
        "bn": ["খাবার", "খাদ্য"],
        "ans_bn": "খাদ্য তৈরি",
        "ans_en": "food making",
    },
    {
        "predicate": "has",
        "en": ["has", "আছে", "পায়"],
        "bn": ["আছে", "পায়"],
        "ans_bn": "আছে",
        "ans_en": "has",
    },
    {
        "predicate": "continent",
        "en": ["continent", "মহাদেশ"],
        "bn": ["মহাদেশ"],
        "ans_bn": "মহাদেশ",
        "ans_en": "continent",
    },
    {
        "predicate": "language",
        "en": ["language", "ভাষা"],
        "bn": ["ভাষা"],
        "ans_bn": "ভাষা",
        "ans_en": "language",
    },
]


def load_commonsense_facts() -> List[CommonsenseFact]:
    """Return the curated bilingual commonsense fact list."""
    return list(_COMMONSENSE_FACTS)


def register_commonsense_layer(brain: Any) -> int:
    """Load commonsense facts into ``brain.semantic_memory``.

    Returns the number of facts registered. Facts already present
    (identical triple) are not overwritten so user-taught overrides win.
    """
    count = 0
    for fact in _COMMONSENSE_FACTS:
        key = f"{fact.subject}:{fact.predicate}:{fact.obj}"
        if key in brain.semantic_memory.facts:
            continue
        brain.semantic_memory.store_fact(
            subject=fact.subject,
            predicate=fact.predicate,
            obj=fact.obj,
            confidence=fact.confidence,
            source=fact.source,
        )
        count += 1
    return count


# ---------------------------------------------------------------------------
# Phase 27: conversation corpus integration
# ---------------------------------------------------------------------------


def register_conversation_corpus(brain: Any) -> int:
    """Load the conversation corpus' social-norm facts into the brain's
    semantic memory, create its dialogue-act concepts in the knowledge
    graph, and register the package in the package registry.

    Returns the number of corpus facts registered.
    """
    try:
        from brain.knowledge.corpus_conversation import (
            CONVERSATION_CONCEPTS,
            CONVERSATION_FACTS,
            conversation_corpus,
        )
        from brain.knowledge.registry import PackageRegistry
    except ImportError:  # pragma: no cover - corpus module optional
        return 0

    PackageRegistry().register(conversation_corpus())

    for entry in CONVERSATION_CONCEPTS:
        if brain.concept_graph.get_concept_by_name(entry["name"]) is None:
            brain.concept_graph.create_concept(
                name=entry["name"], concept_type=entry["type"]
            )

    count = 0
    for fact in CONVERSATION_FACTS:
        key = f"{fact['subject']}:{fact['predicate']}:{fact['obj']}"
        if key in brain.semantic_memory.facts:
            continue
        brain.semantic_memory.store_fact(
            subject=fact["subject"],
            predicate=fact["predicate"],
            obj=fact["obj"],
            confidence=0.85,
            source="conversation_corpus",
        )
        count += 1
    return count
