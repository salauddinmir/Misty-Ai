"""
Rule-Based NLU Parser.

Pattern matching to extract concepts, relations, and queries
from Bengali and English text input. NO LLM involved.

Handles the MVP test cases:
- "আমার নাম X" -> name declaration
- "আমি X-এর creator" -> relation declaration
- "X কে তৈরি করেছে?" -> query (who created X?)
"""

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List

from brain.math_engine import MATH_ENGINE


class IntentType(str, Enum):
    """Types of recognized user intents."""

    NAME_DECLARATION = "name_declaration"
    RELATION_DECLARATION = "relation_declaration"
    QUERY_WHO = "query_who"
    QUERY_WHAT = "query_what"
    STATEMENT = "statement"
    TEACH = "teach"
    CORRECTION = "correction"
    CONTINUATION = "continuation"
    GREETING = "greeting"
    MATH = "math"
    UNKNOWN = "unknown"


@dataclass
class ParseResult:
    """Result of NLU parsing.

    Attributes:
        intent: Recognized intent type.
        entities: Extracted entities (concepts, names, etc.).
        relations: Extracted relationships.
        query: Query parameters if this is a question.
        raw_text: Original input text.
        confidence: Parser confidence in this interpretation.
    """

    intent: IntentType
    entities: Dict[str, Any] = field(default_factory=dict)
    relations: List[Dict[str, str]] = field(default_factory=list)
    query: Dict[str, str] = field(default_factory=dict)
    raw_text: str = ""
    confidence: float = 1.0
    # Extracted classification facts {subject, obj} from is_a / means
    # patterns (used by the brain's absorption handlers in Phase 3).
    facts: List[Dict[str, str]] = field(default_factory=list)


class NLUParser:
    """Rule-based parser for Bengali and English text.

    Uses regex patterns to extract structured information
    from natural language input.
    """

    def __init__(self) -> None:
        """Initialize the parser with pattern rules."""
        self._compile_patterns()

    def _compile_patterns(self) -> None:
        """Compile regex patterns for intent recognition."""
        # Bengali patterns
        self._bn_name_patterns = [
            # "আমার নাম X" / "আমার নাম X।"
            re.compile(r"আমার\s+নাম\s+([A-Za-z\u0980-\u09FF]+)", re.UNICODE),
        ]

        self._bn_relation_patterns = [
            # "আমি X-এর Y Z" (I am Y of X, Z) / "আমি Xের Y Z"
            # group(1)=possessor X, group(2)=role Y, group(3)=target Z.
            # The possessive marker attaches with a hyphen ("-এর") or
            # directly ("সালাউদ্দিনের"), so it must not require a space.
            # "আমি Xের Y Z" (possessive এর attached directly to X)
            re.compile(
                # "আমি X-এর Y Z" / "আমি Xের Y Z" — possessive marker may
                # attach with a hyphen ("-এর") or directly ("Xের").
                # Longer possessive forms first (-(এর|ের) before bare র) so
                # "রহিমের" is not wrongly split as "রহিমে" + "র".
                r"আমি\s+([A-Za-z\u0980-\u09FF]+?)(?:-এর|-ের|ের|র)\s+([A-Za-z\u0980-\u09FF]+)\s+([A-Za-z\u0980-\u09FF]+)",
                re.UNICODE,
            ),
            # "আমি X-এর Y" (I am Y of X) — must not be followed by another
            # word, otherwise the 3-group pattern above should apply first.
            re.compile(
                r"আমি\s+([A-Za-z\u0980-\u09FF]+?)(?:-এর|-ের|ের|র)\s+([A-Za-z\u0980-\u09FF]+)(?!\s+[A-Za-z\u0980-\u09FF])",
                re.UNICODE,
            ),
            # "X হলো Y-এর Z" (X is Z of Y)
            re.compile(
                r"([A-Za-z\u0980-\u09FF]+)\s+হলো\s+([A-Za-z\u0980-\u09FF]+)-এর\s+([A-Za-z\u0980-\u09FF]+)",
                re.UNICODE,
            ),
        ]

        self._bn_query_patterns = [
            # "X কে তৈরি করেছে?" (who created X?)
            re.compile(
                r"([A-Za-z\u0980-\u09FF]+)\s+কে\s+তৈরি\s+করেছে\s*[?\u0964\uff1f]?",
                re.UNICODE,
            ),
            # "X-এর creator কে?" (who is X's creator?)
            re.compile(
                r"([A-Za-z\u0980-\u09FF]+)-এর\s+creator\s+কে\s*[?\u0964\uff1f]?",
                re.UNICODE,
            ),
            # "X কে বানিয়েছে?" (who made X?)
            re.compile(
                r"([A-Za-z\u0980-\u09FF]+)\s+কে\s+বানিয়েছে\s*[?\u0964\uff1f]?",
                re.UNICODE,
            ),
            # "কে X তৈরি করেছে?" (who created X?)
            re.compile(
                r"কে\s+([A-Za-z\u0980-\u09FF]+)\s+তৈরি\s+করেছে\s*[?\u0964\uff1f]?",
                re.UNICODE,
            ),
            # "তুমি কে?" / "আপনি কে?" / "মিস্টি কে?" — direct identity
            # question; group 1 captures the addressed entity so the brain
            # can resolve "তুমি/আপনি" to itself and "মিস্টি" by name.
            re.compile(
                r"(তুমি|আপনি|মিস্টি কে|মিস্টি)\s+কে\s*[?\u0964\uff1f]?\s*$",
                re.UNICODE,
            ),
        ]

        self._bn_greeting_patterns = [
            re.compile(r"(হ্যালো|হাই|নমস্কার|আসসালামু|সালাম)", re.UNICODE),
        ]

        # Bengali correction signals that start a turn (highest priority in
        # Bengali path). Examples: "না, ভুল হয়েছে", "আসলে মিস্টি",
        # "এটা সালাউদ্দিন".
        self._bn_correction_patterns = [
            # "এটা" followed by "কী/কি" is a definition question, not a
            # correction, so those continuations are excluded here.
            re.compile(
                r"^\s*(না[ ,।]|ভুল|আসলে\s|এটা\s(?!কী|কি))",
                re.UNICODE,
            ),
        ]

        # Bengali explicit teaching: "আমি জানি যে ...", "মনে রাখো ..."
        self._bn_teach_patterns = [
            re.compile(r"(?:আমি জানি যে|মনে রাখো|মনে রাখুন|শেখো যে)\s+(.+)", re.UNICODE),
        ]

        # Bengali "X হলো Y" generic assertion (statement with is_a relation).
        # Skipped below when the text already matched a relation-declaration
        # pattern, so "X হলো Y-এর Z" is not double-matched.
        self._bn_is_a_pattern = re.compile(
            r"([A-Za-z\u0980-\u09FF]+)\s+হলো\s+([A-Za-z\u0980-\u09FF]+)",
            re.UNICODE,
        )

        # Bengali definition queries: "X মানে কী?"
        self._bn_what_query_pattern = re.compile(
            r"([A-Za-z\u0980-\u09FF]+)\s+মানে\s+(কী|কি)\s*[?\u0964\uff1f]?",
            re.UNICODE,
        )

        # Bengali pronoun-targeted queries with an empty target, to be
        # resolved against the dialogue context by the brain:
        # "সে কে?", "এটা কী?", "তার creator কে?"
        # "সে কে?" / "এটা কী?" / "সে কী।" — the trailing word boundary
        # cannot use \b because it does not recognize Bengali characters,
        # so the pattern anchors at optional sentence-ending punctuation.
        self._bn_pronoun_query_pattern = re.compile(
            r"(সে|এটা|ওটা|এই|সেই)\s+(কে|কী|কি)\s*[?।\u0964]?\s*$",
            re.UNICODE,
        )

        # Bengali interrogative words that must NEVER be captured as a name.
        # Prevents inputs like "আমার নাম কি?" being parsed as a name declaration.
        self._bn_interrogatives = re.compile(
            r"(কি|কী|কে|কোন|কোথা|কখন|কেমন|কতটা|কার|কেন|কিসের)$",
            re.UNICODE,
        )

        # English patterns
        self._en_name_patterns = [
            re.compile(r"my\s+name\s+is\s+(\w+)", re.IGNORECASE),
            re.compile(r"i\s+am\s+(\w+)", re.IGNORECASE),
            re.compile(r"call\s+me\s+(\w+)", re.IGNORECASE),
        ]

        self._en_relation_patterns = [
            # "I am the creator of X" / "I am creator of X"
            re.compile(r"i\s+am\s+(?:the\s+)?(\w+)\s+of\s+(\w+)", re.IGNORECASE),
            # "I created X"
            re.compile(r"i\s+created\s+(\w+)", re.IGNORECASE),
            # "X is a Y" / "X is Y"
            re.compile(r"(\w+)\s+is\s+(?:a\s+)?(\w+)", re.IGNORECASE),
        ]

        self._en_query_patterns = [
            # "who created X?"
            re.compile(r"who\s+created\s+(\w+)\s*\??", re.IGNORECASE),
            # "who is the creator of X?"
            re.compile(r"who\s+is\s+(?:the\s+)?creator\s+of\s+(\w+)\s*\??", re.IGNORECASE),
            # "what is X?"
            re.compile(r"what\s+is\s+(\w+)\s*\??", re.IGNORECASE),
            # "who are you?" / "who created you?" / "who made you?" —
            # self-identity questions; group 1 captures the addressed word
            # so the brain can resolve it to itself (Misty) as the target.
            re.compile(r"^who\s+(?:are|created|made|built)\s+(you)\??\s*$", re.IGNORECASE),
        ]

        self._en_greeting_patterns = [
            re.compile(r"^(hello|hi|hey|greetings)\b", re.IGNORECASE),
        ]

        # English correction signals that start a turn.
        self._en_correction_patterns = [
            re.compile(r"^\s*(no\b|wrong\b|actually\b|it is\b|it's\b|that's wrong)", re.IGNORECASE),
        ]

        # English explicit teaching: "learn that ...", "remember that ..."
        self._en_teach_patterns = [
            re.compile(r"(?:learn that|remember that|note that|keep in mind that)\s+(.+)$", re.IGNORECASE),
        ]

        # English "X means Y" / "X is a/an Y" assertions
        self._en_is_a_pattern = re.compile(
            r"(\w+)\s+(?:means|is a|is an)\s+(.+)$",
            re.IGNORECASE,
        )

        # English pronoun-targeted queries with an empty target, resolved
        # against the dialogue context by the brain:
        # "who is he?", "what is it?", "who created her?"
        self._en_pronoun_query_pattern = re.compile(
            r"\b(who|what|which)\b\s+.*\b(it|its|him|her|he|she|this|that)\b",
            re.IGNORECASE,
        )

    def parse(self, text: str) -> ParseResult:
        """Parse input text and extract structured information.

        Args:
            text: Raw text input (Bengali or English).

        Returns:
            ParseResult with intent, entities, relations, and/or query.
        """
        text = text.strip()
        if not text:
            return ParseResult(intent=IntentType.UNKNOWN, raw_text=text)

        # Try Bengali patterns first, then English
        result = self._try_bengali(text)
        if result.intent != IntentType.UNKNOWN:
            return result

        result = self._try_english(text)
        if result.intent != IntentType.UNKNOWN:
            return result

        # Ellipsis/continuation patterns (Bengali or English) map to the
        # CONTINUATION intent so the brain can reuse the last topic.
        # Imported lazily to keep the parser importable on its own.
        from brain.nlu.coreference import is_continuation

        # Continuation triggers must be very short; a sentence with
        # several words (e.g. "আমার নাম কি?") must never be swallowed
        # as a continuation even when it contains a trigger word.
        if is_continuation(text) and len(text.split()) <= 3:
            return ParseResult(
                intent=IntentType.CONTINUATION,
                raw_text=text,
                confidence=0.6,
            )

        # Questions that no pattern understood must stay UNKNOWN instead
        # of becoming a confident-enough statement. This also preserves
        # the phase-2 guard where "আমার নাম কি?" is not a name
        # declaration and not an assertion either.
        is_question = (
            "?" in text or "\u0964" in text or "\uff1f" in text or re.search(r"\b(কি|কী|কেন|কীভাবে)\b", text, re.UNICODE)
        )
        if is_question:
            return ParseResult(
                intent=IntentType.UNKNOWN,
                raw_text=text,
                confidence=0.3,
            )
        # Default: treat as unknown statement
        return ParseResult(
            intent=IntentType.STATEMENT,
            raw_text=text,
            confidence=0.3,
        )

    def _try_bengali(self, text: str) -> ParseResult:
        """Try Bengali pattern matching."""
        # Check corrections first (a correction overrides anything else)
        for pattern in self._bn_correction_patterns:
            if pattern.search(text):
                return ParseResult(
                    intent=IntentType.CORRECTION,
                    raw_text=text,
                    confidence=0.8,
                )

        # Check explicit teach patterns
        for pattern in self._bn_teach_patterns:
            match = pattern.search(text)
            if match:
                taught = match.group(1).strip("।. ")
                return ParseResult(
                    intent=IntentType.TEACH,
                    entities={"taught": taught},
                    raw_text=text,
                    confidence=0.8,
                )

        # Deterministic mathematics takes priority over generic questions.
        if MATH_ENGINE.looks_mathematical(text):
            return ParseResult(
                intent=IntentType.MATH,
                entities={"math_text": text},
                raw_text=text,
                confidence=0.98,
            )

        # Check greetings
        for pattern in self._bn_greeting_patterns:
            if pattern.search(text):
                return ParseResult(
                    intent=IntentType.GREETING,
                    raw_text=text,
                    confidence=0.9,
                )

        # Check name declarations
        for pattern in self._bn_name_patterns:
            match = pattern.search(text)
            if match:
                name = match.group(1).strip("\u0964. ")
                # Guard: an interrogative word after "আমার নাম" (or any
                # question mark) means this is a question, not a declaration.
                if self._bn_interrogatives.search(name) or "?" in text:
                    return ParseResult(
                        intent=IntentType.UNKNOWN,
                        raw_text=text,
                        confidence=0.3,
                    )
                return ParseResult(
                    intent=IntentType.NAME_DECLARATION,
                    entities={"name": name, "type": "Person", "is_self": True},
                    raw_text=text,
                    confidence=0.95,
                )

        # Check queries (before relations to avoid false matches)
        for pattern in self._bn_query_patterns:
            match = pattern.search(text)
            if match:
                target = match.group(1).strip("\u0964. ")
                # Self-identity phrasings: "তুমি কে?", "আপনি কে?", "মিস্টি কে?"
                # resolve to the brain itself (Misty) as the query target.
                if (target or "").strip() in {"তুমি", "আপনি", "মিস্টি", "মিস্টি কে"}:
                    target = "Misty"
                return ParseResult(
                    intent=IntentType.QUERY_WHO,
                    query={
                        "type": "who",
                        "relation": "creator_of",
                        "target": target,
                    },
                    raw_text=text,
                    confidence=0.9,
                )

        # Check "X হলো Y" generic assertions before relation patterns
        is_a_match = self._bn_is_a_pattern.search(text)

        # Check relation declarations
        for i, pattern in enumerate(self._bn_relation_patterns):
            match = pattern.search(text)
            if match:
                if i == 0:
                    # "আমি X-এর Y Z" pattern
                    possessor = match.group(1).strip("\u0964. ")
                    relation = match.group(2).strip("\u0964. ")
                    target = match.group(3).strip("\u0964. ")
                    return ParseResult(
                        intent=IntentType.RELATION_DECLARATION,
                        entities={"target": target, "relation_role": relation, "possessor": possessor},
                        relations=[
                            {
                                "source": possessor,
                                "relation_type": f"{relation}_of",
                                "target": target,
                            }
                        ],
                        raw_text=text,
                        confidence=0.9,
                    )
                if i == 1:
                    # Legacy "আমি X-এর Y" pattern: I am Y of X
                    target = match.group(1).strip("\u0964. ")
                    relation = match.group(2).strip("\u0964. ")
                    return ParseResult(
                        intent=IntentType.RELATION_DECLARATION,
                        entities={"target": target, "relation_role": relation},
                        relations=[
                            {
                                "source": "__self__",
                                "relation_type": f"{relation}_of",
                                "target": target,
                            }
                        ],
                        raw_text=text,
                        confidence=0.9,
                    )
                if i == 2:
                    # "X হলো Y-এর Z" pattern
                    subject = match.group(1)
                    obj = match.group(2)
                    relation = match.group(3)
                    return ParseResult(
                        intent=IntentType.RELATION_DECLARATION,
                        entities={
                            "subject": subject,
                            "object": obj,
                            "relation": relation,
                        },
                        relations=[
                            {
                                "source": subject,
                                "relation_type": f"{relation}_of",
                                "target": obj,
                            }
                        ],
                        raw_text=text,
                        confidence=0.85,
                    )

        # "X হলো Y" generic assertion (only if no relation pattern matched)
        if is_a_match:
            subject = is_a_match.group(1).strip()
            definition = is_a_match.group(2).strip()
            if definition not in {"কী", "কি"}:
                return ParseResult(
                    intent=IntentType.STATEMENT,
                    entities={"subject": subject, "is_a": definition},
                    relations=[
                        {
                            "source": subject,
                            "relation_type": "is_a",
                            "target": definition,
                        }
                    ],
                    facts=[{"subject": subject, "obj": definition}],
                    raw_text=text,
                    confidence=0.7,
                )

        # Pronoun-targeted query "সে কে?" / "এটা কী?"
        pron_match = self._bn_pronoun_query_pattern.search(text)
        if pron_match:
            pronoun = pron_match.group(1)
            question_word = pron_match.group(2)
            return ParseResult(
                intent=IntentType.QUERY_WHO if question_word == "কে" else IntentType.QUERY_WHAT,
                query={
                    "type": "who" if question_word == "কে" else "what",
                    "relation": "creator_of" if question_word == "কে" else "is_a",
                    "target": "",
                    "pronoun": pronoun,
                },
                raw_text=text,
                confidence=0.6,
            )

        # Definition query "X মানে কী?"
        what_match = self._bn_what_query_pattern.search(text)
        if what_match:
            target = what_match.group(1).strip()
            # A pronoun/stopword target ("এর মানে কী?", "সে মানে কি?") is
            # not a definition query on its own; coreference in the brain
            # will map the pronoun to the salient entity instead.
            if target in {"এর", "সে", "এই", "সেই", "এ", "ও", "তার", "কি", "কী", "মানে"}:
                return ParseResult(
                    intent=IntentType.QUERY_WHAT,
                    query={"type": "what", "relation": "is_a", "target": ""},
                    raw_text=text,
                    confidence=0.6,
                )
            return ParseResult(
                intent=IntentType.QUERY_WHAT,
                query={"type": "what", "relation": "is_a", "target": target},
                raw_text=text,
                confidence=0.8,
            )

        return ParseResult(intent=IntentType.UNKNOWN, raw_text=text)

    def _try_english(self, text: str) -> ParseResult:
        # Check corrections first (a correction overrides anything else)
        for pattern in self._en_correction_patterns:
            if pattern.search(text):
                return ParseResult(
                    intent=IntentType.CORRECTION,
                    raw_text=text,
                    confidence=0.8,
                )

        # Check explicit teach patterns
        for pattern in self._en_teach_patterns:
            match = pattern.search(text)
            if match:
                taught = match.group(1).strip(". ")
                return ParseResult(
                    intent=IntentType.TEACH,
                    entities={"taught": taught},
                    raw_text=text,
                    confidence=0.8,
                )
        """Try English pattern matching."""
        # Deterministic mathematics takes priority over generic questions.
        if MATH_ENGINE.looks_mathematical(text):
            return ParseResult(
                intent=IntentType.MATH,
                entities={"math_text": text},
                raw_text=text,
                confidence=0.98,
            )

        # Check greetings
        for pattern in self._en_greeting_patterns:
            if pattern.search(text):
                return ParseResult(
                    intent=IntentType.GREETING,
                    raw_text=text,
                    confidence=0.9,
                )

        # English interrogative words that must NEVER be captured as a name.
        self._en_interrogatives = re.compile(
            r"^(what|who|where|when|why|how|which|whose|whatever|anything)$",
            re.IGNORECASE,
        )
        # Check name declarations
        for pattern in self._en_name_patterns:
            match = pattern.search(text)
            if match:
                name = match.group(1)
                # Guard: an interrogative word (or any question mark) after
                # "my name is" means this is a question, not a declaration
                # (e.g. "my name is what?")
                if self._en_interrogatives.match(name) or "?" in text:
                    return ParseResult(
                        intent=IntentType.UNKNOWN,
                        raw_text=text,
                        confidence=0.3,
                    )
                return ParseResult(
                    intent=IntentType.NAME_DECLARATION,
                    entities={"name": name, "type": "Person", "is_self": True},
                    raw_text=text,
                    confidence=0.9,
                )

        # Check queries
        for pattern in self._en_query_patterns:
            match = pattern.search(text)
            if match:
                target = match.group(1)
                # Self-identity phrasings resolve to the brain itself.
                if (target or "").lower() == "you":
                    target = "Misty"
                if "created" in text.lower() or "creator" in text.lower():
                    relation = "creator_of"
                    query_type = "who"
                else:
                    relation = "is_a"
                    query_type = "what"
                return ParseResult(
                    intent=IntentType.QUERY_WHO if query_type == "who" else IntentType.QUERY_WHAT,
                    query={
                        "type": query_type,
                        "relation": relation,
                        "target": target,
                    },
                    raw_text=text,
                    confidence=0.85,
                )

        # Pronoun-targeted query "who is he?" / "what is it?"
        pron_match = self._en_pronoun_query_pattern.search(text)
        if pron_match:
            question_word = pron_match.group(1).lower()
            if question_word == "what":
                query_type = "what"
                relation = "is_a"
            else:
                query_type = "who"
                relation = "creator_of"
            return ParseResult(
                intent=IntentType.QUERY_WHO if query_type == "who" else IntentType.QUERY_WHAT,
                query={
                    "type": query_type,
                    "relation": relation,
                    "target": "",
                    "pronoun": pron_match.group(2).lower(),
                },
                raw_text=text,
                confidence=0.6,
            )

        # Check "X means Y" / "X is a Y" assertions
        is_a_match = self._en_is_a_pattern.search(text)
        if is_a_match:
            subject = is_a_match.group(1)
            definition = is_a_match.group(2).strip(". ")
            return ParseResult(
                intent=IntentType.STATEMENT,
                entities={"subject": subject, "is_a": definition},
                relations=[
                    {
                        "source": subject,
                        "relation_type": "is_a",
                        "target": definition,
                    }
                ],
                facts=[{"subject": subject, "obj": definition}],
                raw_text=text,
                confidence=0.7,
            )

        # Check relations
        for i, pattern in enumerate(self._en_relation_patterns):
            match = pattern.search(text)
            if match:
                if i == 0:
                    # "I am the X of Y"
                    relation = match.group(1)
                    target = match.group(2)
                    return ParseResult(
                        intent=IntentType.RELATION_DECLARATION,
                        entities={"target": target, "relation_role": relation},
                        relations=[
                            {
                                "source": "__self__",
                                "relation_type": f"{relation}_of",
                                "target": target,
                            }
                        ],
                        raw_text=text,
                        confidence=0.85,
                    )
                elif i == 1:
                    # "I created X"
                    target = match.group(1)
                    return ParseResult(
                        intent=IntentType.RELATION_DECLARATION,
                        entities={"target": target, "relation_role": "creator"},
                        relations=[
                            {
                                "source": "__self__",
                                "relation_type": "creator_of",
                                "target": target,
                            }
                        ],
                        raw_text=text,
                        confidence=0.85,
                    )

        return ParseResult(intent=IntentType.UNKNOWN, raw_text=text)

    def __repr__(self) -> str:
        return "NLUParser(rule-based, Bengali+English)"
