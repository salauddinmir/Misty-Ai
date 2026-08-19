"""
Universal term normalization and Bengali/English concept bridging.

Knowledge in this brain is stored under many surface forms: English canonical
subjects ("Kinetic Energy"), Bengali canonical subjects ("গতিশক্তি"), Bengali
transliterations of English words ("কিনেটিক এনার্জি"), inflected Bengali forms
("আকাশের"), and English plurals ("robots"). Retrieval used strict string
equality, so a question phrased in one form could not reach a fact stored in
another form even when the brain already knew the answer.

This module centralizes that problem:

* :func:`canonicalize` produces one comparable key for a term.
* :func:`variants` expands a term into every equivalent surface form worth
  looking up, including its counterpart in the other language.
* :data:`BILINGUAL_CONCEPTS` links Bengali and English names for the same
  concept so knowledge learned in one language answers questions in the other.

No translation is generated at runtime: the bridge is an explicit, reviewable
lexicon, so the brain never invents a word it was not taught.
"""

from __future__ import annotations

import re
from functools import lru_cache
from typing import Dict, Iterable, List, Set, Tuple

# ---------------------------------------------------------------------------
# Bengali morphology
# ---------------------------------------------------------------------------

# Ordered longest-first so "েরটা" is removed before "ের".
_BN_SUFFIXES: Tuple[str, ...] = (
    "েরটাও",
    "েরটা",
    "েরটি",
    "গুলোর",
    "গুলির",
    "গুলো",
    "গুলি",
    "দেরকে",
    "টিকে",
    "টাকে",
    "কেই",
    "ের",
    "য়ের",
    "েই",
    "তে",
    "কে",
    "রা",
    "টি",
    "টা",
    "খানা",
    "র",
)

_BN_RANGE = ("\u0980", "\u09ff")

# Words that never carry topic meaning on their own.
_GENERIC_TOKENS: frozenset[str] = frozenset(
    {
        "of",
        "the",
        "a",
        "an",
        "and",
        "or",
        "in",
        "on",
        "at",
        "to",
        "for",
        "with",
        "from",
        "is",
        "are",
        "was",
        "were",
        "be",
        "about",
        "এর",
        "ও",
        "এবং",
        "কি",
        "কী",
        "হলো",
        "হয়",
        "কে",
        "নাম",
        "সম্পর্কে",
        "মানে",
    }
)

_BN_DIGITS = str.maketrans("\u09e6\u09e7\u09e8\u09e9\u09ea\u09eb\u09ec\u09ed\u09ee\u09ef", "0123456789")

_PUNCTUATION_RE = re.compile(r"[^\w\u0980-\u09ff\s+\-/^=.]", re.UNICODE)
_WHITESPACE_RE = re.compile(r"\s+", re.UNICODE)


def is_bengali(text: str) -> bool:
    """True when ``text`` contains any Bengali character."""
    return any(_BN_RANGE[0] <= char <= _BN_RANGE[1] for char in text or "")


def strip_bengali_suffix(word: str) -> str:
    """Remove one Bengali inflectional suffix from ``word`` when it is safe.

    The stem must keep at least two characters, so short words such as "ের"
    are never reduced to nothing.
    """
    for suffix in _BN_SUFFIXES:
        if word.endswith(suffix) and len(word) - len(suffix) >= 2:
            return word[: -len(suffix)]
    return word


def singularize(word: str) -> str:
    """Reduce a simple English plural to its singular form."""
    if not word.isascii() or len(word) <= 3 or not word.endswith("s"):
        return word
    if word.endswith("ies") and len(word) > 4:
        return word[:-3] + "y"
    if word.endswith("ses") or word.endswith("xes") or word.endswith("zes"):
        return word[:-2]
    if word.endswith("es") and len(word) > 4 and not word.endswith("ees"):
        return word[:-2]
    if word.endswith("ss"):
        return word
    return word[:-1]


@lru_cache(maxsize=200_000)
def canonicalize(term: str) -> str:
    """Return a single comparable key for ``term``.

    Case, punctuation, Bengali digits, possessives, inflections, English
    plurals, and filler words are all folded away.
    """
    if not term:
        return ""
    text = term.strip().translate(_BN_DIGITS)
    # Khanda ta and ta are written interchangeably ("সৌরজগৎ" / "সৌরজগত").
    text = text.replace("\u09ce", "\u09a4")
    text = text.replace("\u2019", "'").replace("'s", " ")
    text = _PUNCTUATION_RE.sub(" ", text)
    text = _WHITESPACE_RE.sub(" ", text).strip().casefold()
    if not text:
        return ""

    words: List[str] = []
    for word in text.split():
        if word in _GENERIC_TOKENS:
            continue
        word = strip_bengali_suffix(word) if is_bengali(word) else singularize(word)
        if word:
            words.append(word)
    return " ".join(words) if words else text


# ---------------------------------------------------------------------------
# Bengali <-> English concept bridge
# ---------------------------------------------------------------------------

# Each entry links names for the SAME concept. Left side is Bengali, right side
# is English. Transliterations are listed as extra Bengali spellings so common
# user phrasing ("কিনেটিক এনার্জি") reaches canonical knowledge ("গতিশক্তি").
_CONCEPT_GROUPS: Tuple[Tuple[str, ...], ...] = (
    # --- nature / sky ---
    ("আকাশ", "sky"),
    ("সূর্য", "sun"),
    ("চাঁদ", "moon"),
    ("তারা", "নক্ষত্র", "star"),
    ("মেঘ", "cloud"),
    ("বৃষ্টি", "rain"),
    ("বাতাস", "হাওয়া", "air", "wind"),
    ("পানি", "জল", "water"),
    ("আগুন", "অগ্নি", "fire"),
    ("মাটি", "soil"),
    ("পৃথিবী", "earth"),
    ("সমুদ্র", "সাগর", "sea", "ocean"),
    ("নদী", "river"),
    ("পাহাড়", "পর্বত", "mountain"),
    ("বরফ", "ice"),
    ("তুষার", "snow"),
    ("বজ্রপাত", "lightning"),
    ("রংধনু", "rainbow"),
    ("ঋতু", "season"),
    ("আবহাওয়া", "weather"),
    # --- living things ---
    ("গাছ", "বৃক্ষ", "tree"),
    ("ফুল", "flower"),
    ("ফল", "fruit"),
    ("পাতা", "leaf"),
    ("বীজ", "seed"),
    ("প্রাণী", "animal"),
    ("পাখি", "bird"),
    ("মাছ", "fish"),
    ("কুকুর", "dog"),
    ("বিড়াল", "cat"),
    ("গরু", "cow"),
    ("ছাগল", "goat"),
    ("ঘোড়া", "horse"),
    ("হাতি", "elephant"),
    ("বাঘ", "tiger"),
    ("সিংহ", "lion"),
    ("সাপ", "snake"),
    ("মানুষ", "human", "person"),
    # --- body ---
    ("হৃদয়", "হার্ট", "heart"),
    ("মস্তিষ্ক", "ব্রেইন", "brain"),
    ("চোখ", "eye"),
    ("কান", "ear"),
    ("নাক", "nose"),
    ("হাত", "hand"),
    ("পা", "leg", "foot"),
    ("রক্ত", "blood"),
    ("ফুসফুস", "lung"),
    ("হাড়", "bone"),
    # --- food ---
    ("ভাত", "rice"),
    ("রুটি", "bread"),
    ("দুধ", "milk"),
    ("চিনি", "sugar"),
    ("লবণ", "salt"),
    ("তেল", "oil"),
    ("ডিম", "egg"),
    ("মধু", "honey"),
    ("চা", "tea"),
    ("কফি", "coffee"),
    ("সবজি", "vegetable"),
    # --- everyday objects / places ---
    ("বই", "book"),
    ("কলম", "pen"),
    ("ঘর", "বাড়ি", "house", "home"),
    ("স্কুল", "বিদ্যালয়", "school"),
    ("হাসপাতাল", "hospital"),
    ("শহর", "city"),
    ("গ্রাম", "village"),
    ("দেশ", "country"),
    ("রাজধানী", "রাজধনী", "capital"),
    ("ভাষা", "language"),
    ("টাকা", "মুদ্রা", "money", "currency"),
    ("সেতু", "ব্রিজ", "bridge"),
    ("রাস্তা", "road"),
    ("গাড়ি", "car"),
    ("বিমান", "উড়োজাহাজ", "aeroplane", "airplane"),
    ("ট্রেন", "রেলগাড়ি", "train"),
    ("ঘড়ি", "clock", "watch"),
    ("আয়না", "mirror"),
    ("চাবি", "key"),
    ("দরজা", "door"),
    ("জানালা", "window"),
    # --- technology ---
    ("কম্পিউটার", "computer"),
    ("ইন্টারনেট", "internet"),
    ("রোবট", "robot"),
    ("স্যাটেলাইট", "কৃত্রিম উপগ্রহ", "satellite"),
    ("মোবাইল", "mobile", "phone"),
    ("বিদ্যুৎ", "electricity"),
    ("যন্ত্র", "machine"),
    ("সফটওয়্যার", "software"),
    ("তথ্য", "data", "information"),
    ("কৃত্রিম বুদ্ধিমত্তা", "artificial intelligence"),
    # --- science: physics ---
    ("গতিশক্তি", "কিনেটিক এনার্জি", "কাইনেটিক এনার্জি", "kinetic energy"),
    ("বিভবশক্তি", "পটেনশিয়াল এনার্জি", "potential energy"),
    ("শক্তি", "এনার্জি", "energy"),
    ("বল", "ফোর্স", "force"),
    ("ভর", "মাস", "mass"),
    ("ওজন", "weight"),
    ("বেগ", "ভেলোসিটি", "velocity"),
    ("দ্রুতি", "স্পিড", "speed"),
    ("ত্বরণ", "অ্যাকসিলারেশন", "acceleration"),
    ("দূরত্ব", "distance"),
    ("সময়", "টাইম", "time"),
    ("কাজ", "work"),
    ("ক্ষমতা", "পাওয়ার", "power"),
    ("ভরবেগ", "মোমেন্টাম", "momentum"),
    ("মহাকর্ষ", "গ্র্যাভিটি", "gravity"),
    ("চাপ", "প্রেসার", "pressure"),
    ("তাপ", "হিট", "heat"),
    ("তাপমাত্রা", "temperature"),
    ("আলো", "light"),
    ("শব্দ", "sound"),
    ("তরঙ্গ", "ওয়েভ", "wave"),
    ("কম্পাঙ্ক", "ফ্রিকোয়েন্সি", "frequency"),
    ("রোধ", "রেজিস্ট্যান্স", "resistance"),
    ("তড়িৎপ্রবাহ", "কারেন্ট", "current"),
    ("বিভব", "ভোল্টেজ", "voltage"),
    ("পরমাণু", "অ্যাটম", "atom"),
    ("অণু", "molecule"),
    ("ঘনত্ব", "density"),
    ("আয়তন", "volume"),
    # --- science: general ---
    ("পদার্থবিজ্ঞান", "physics"),
    ("রসায়ন", "chemistry"),
    ("জীববিজ্ঞান", "biology"),
    ("গণিত", "mathematics", "math"),
    ("বিজ্ঞান", "science"),
    ("কোষ", "cell"),
    ("অক্সিজেন", "oxygen"),
    ("কার্বন ডাই অক্সাইড", "carbon dioxide"),
    ("সালোকসংশ্লেষণ", "photosynthesis"),
    # --- mathematics ---
    ("যোগ", "addition"),
    ("বিয়োগ", "subtraction"),
    ("গুণ", "multiplication"),
    ("ভাগ", "division"),
    ("বর্গ", "square"),
    ("বর্গমূল", "square root"),
    ("ভগ্নাংশ", "fraction"),
    ("শতকরা", "percentage"),
    ("গড়", "average", "mean"),
    ("ক্ষেত্রফল", "area"),
    ("পরিসীমা", "perimeter"),
    ("কোণ", "angle"),
    ("ত্রিভুজ", "triangle"),
    ("বৃত্ত", "circle"),
    ("সমীকরণ", "equation"),
    # --- geography / civics ---
    ("ভারত", "india"),
    ("বাংলাদেশ", "bangladesh"),
    # continents
    ("আফ্রিকা", "africa"),
    ("ইউরোপ", "europe"),
    ("অ্যান্টার্কটিকা", "আন্টার্কটিকা", "antarctica"),
    ("উত্তর আমেরিকা", "north america"),
    ("দক্ষিণ আমেরিকা", "south america"),
    ("অস্ট্রেলিয়া", "australia"),
    ("ওশেনিয়া", "oceania"),
    # planets
    ("বুধ", "mercury"),
    ("শুক্র", "venus"),
    ("মঙ্গল", "mars"),
    ("বৃহস্পতি", "jupiter"),
    ("শনি", "saturn"),
    ("ইউরেনাস", "uranus"),
    ("নেপচুন", "neptune"),
    ("বাংলা", "bengali"),
    ("ইংরেজি", "english"),
    ("এশিয়া", "asia"),
    ("মহাদেশ", "continent"),
    ("সংবিধান", "constitution"),
    ("স্বাধীনতা", "independence"),
    ("সরকার", "government"),
    ("প্রধানমন্ত্রী", "prime minister"),
    ("রাষ্ট্রপতি", "president"),
    # --- literature / arts ---
    ("কবিতা", "poem", "poetry"),
    ("কবি", "poet"),
    ("গল্প", "story"),
    ("উপন্যাস", "novel"),
    ("নাটক", "drama", "play"),
    ("সাহিত্য", "literature"),
    ("লেখক", "author", "writer"),
    ("গান", "song"),
    ("সঙ্গীত", "music"),
    ("ছবি", "picture", "painting"),
    # --- abstract ---
    ("সময়সূচি", "schedule"),
    ("কারণ", "reason", "cause"),
    ("উদাহরণ", "example"),
    ("সংজ্ঞা", "definition"),
    ("অর্থ", "meaning"),
    ("ইতিহাস", "history"),
    ("ভবিষ্যৎ", "future"),
    ("অতীত", "past"),
    ("বর্তমান", "present"),
    ("জীবন", "life"),
    ("মৃত্যু", "death"),
    ("স্বাস্থ্য", "health"),
    ("রোগ", "disease"),
    ("ঔষধ", "medicine"),
    ("শিক্ষা", "education"),
    ("কাজকর্ম", "occupation", "job"),
)


def _build_bridge() -> Dict[str, Tuple[str, ...]]:
    bridge: Dict[str, Set[str]] = {}
    for group in _CONCEPT_GROUPS:
        canonical_names = {name for name in group if name}
        for name in canonical_names:
            key = canonicalize(name)
            if not key:
                continue
            bridge.setdefault(key, set()).update(canonical_names)
    return {key: tuple(sorted(names)) for key, names in bridge.items()}


#: Canonical key -> every known name for that concept, in both languages.
BILINGUAL_CONCEPTS: Dict[str, Tuple[str, ...]] = _build_bridge()


@lru_cache(maxsize=100_000)
def linked_names(term: str) -> Tuple[str, ...]:
    """Return every known name for the concept ``term`` refers to."""
    return BILINGUAL_CONCEPTS.get(canonicalize(term), ())


def translated_names(term: str) -> Tuple[str, ...]:
    """Return names for ``term`` written in the other language."""
    source_is_bengali = is_bengali(term)
    return tuple(name for name in linked_names(term) if is_bengali(name) != source_is_bengali)


def variants(term: str, *, include_cross_language: bool = True) -> List[str]:
    """Expand ``term`` into equivalent surface forms worth looking up.

    The original spelling is always first so exact stored knowledge keeps
    priority over bridged or normalized matches.
    """
    if not term:
        return []
    ordered: List[str] = []
    seen: Set[str] = set()

    def _add(candidate: str) -> None:
        candidate = (candidate or "").strip()
        if not candidate:
            return
        key = candidate.casefold()
        if key in seen:
            return
        seen.add(key)
        ordered.append(candidate)

    _add(term)
    _add(term.strip().title() if term.isascii() else term.strip())

    canonical = canonicalize(term)
    _add(canonical)
    if canonical.isascii():
        _add(canonical.title())

    words = term.split()
    if len(words) > 1:
        # Head noun: last content word in English, first in Bengali.
        content = [word for word in words if canonicalize(word)]
        if content:
            _add(content[0] if is_bengali(term) else content[-1])
    for word in words:
        stem = canonicalize(word)
        if stem and stem != canonical:
            _add(stem)

    if include_cross_language:
        for name in linked_names(term):
            _add(name)
        for word in words:
            for name in linked_names(word):
                _add(name)

    return ordered


def matches(left: str, right: str) -> bool:
    """True when two terms name the same concept."""
    if not left or not right:
        return False
    if left.casefold() == right.casefold():
        return True
    left_key, right_key = canonicalize(left), canonicalize(right)
    if left_key and left_key == right_key:
        return True
    left_names = set(linked_names(left)) or {left}
    right_names = set(linked_names(right)) or {right}
    return bool({name.casefold() for name in left_names} & {name.casefold() for name in right_names})


def canonical_keys(terms: Iterable[str]) -> Set[str]:
    """Canonical keys for an iterable of terms, empty keys removed."""
    return {key for key in (canonicalize(term) for term in terms) if key}
