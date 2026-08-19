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
from brain.physics_engine import PHYSICS_ENGINE


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
    PHYSICS = "physics"
    CAPABILITY_QUERY = "capability_query"
    RECOGNITION_QUERY = "recognition_query"
    CONVERSATION = "conversation"
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
        self._bn_capability_pattern = re.compile(r"(?:তুমি|আপনি|মিস্টি).*(?:শিখেছ|জানো|পারো).*[?\uFF1F]?$", re.UNICODE)
        self._bn_recognition_pattern = re.compile(
            r"(?:তুমি|আপনি|মিস্টি)\s+(?:কি|কী)\s+আমাকে\s+চিনতে\s+পারো\s*[?\uFF1F]?$",
            re.UNICODE,
        )
        # Bengali casual/social turns that are neither greetings nor questions
        # the parser can otherwise resolve: "কি খবর", "ভালো ব্যাপার", "কি
        # ভাবছো". A short, friendly, deterministic reply is composed in the
        # brain's conversation act handler instead of the generic echo.
        self._bn_casual_patterns = [
            re.compile(r"(কি খবর|কেমন আছো|কেমন আছ|কি খবরে|ভালো ব্যাপার|বেশ হয়েছে)", re.UNICODE),
            re.compile(r"(তুমি কি ভাবছো|কি ভাবছো|কি করছো|কি করছ)", re.UNICODE),
            # Clarification / casual follow-up signals: "বুঝলাম না",
            # "কি ব্যাপার?", "কেন?" — treated as conversational
            # continuations rather than UNKNOWN intents so the brain
            # never replies with the canned parse-failure message.
            re.compile(
                r"(বুঝলাম না|বুঝতে পারছি না|বুঝছি না|কি ব্যাপার|কী ব্যাপার|কেন|কেন কি হয়েছে)",
                re.UNICODE,
            ),
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

        # Bengali explicit teaching: "আমি জানি যে ...", "মনে রাখো ...".
        # The separator after the trigger may be a space or a colon, so
        # "মনে রাখো: X হলো Y" is still recognized as teaching instead of
        # falling through to the mathematical heuristic.
        self._bn_teach_patterns = [
            re.compile(r"(?:আমি জানি যে|মনে রাখো|মনে রাখুন|শেখো যে)[:\s]+(.+)", re.UNICODE),
        ]

        # Bengali "X হলো Y" generic assertion (statement with is_a relation).
        # Skipped below when the text already matched a relation-declaration
        # pattern, so "X হলো Y-এর Z" is not double-matched.
        # "X হলো Y" — object may span multiple words; clause stop words
        # (এবং, মানে, কিন্তু...) are trimmed after matching.
        self._bn_is_a_pattern = re.compile(
            r"([A-Za-z\u0980-\u09FF]+)\s+হলো\s+([A-Za-z\u0980-\u09FF]+(?:\s+[A-Za-z\u0980-\u09FF]+)*)",
            re.UNICODE,
        )

        # Bengali definition queries: "X মানে কী?"
        self._bn_what_query_pattern = re.compile(
            r"([A-Za-z\u0980-\u09FF]+)\s+মানে\s+(কী|কি)\s*[?\u0964\uff1f]?",
            re.UNICODE,
        )
        # Bare Bengali "what is X" form without হলো/মানে: "স্যাটেলাইট কি?",
        # "পানি কী", "internet কি". Matches a short Bengali/English topic
        # word directly followed by the interrogative কি/কী at the end of
        # the turn. A two-word guard keeps "আমি ভালো কি?" style phrases
        # from being misclassified as definition queries — the topic part
        # must not itself contain an interrogative meaning.
        # The topic part allows possessive "-এর/Xের" constructions so
        # phrases like "আকাশের রঙ" (color of the sky) are captured whole
        # instead of only the first word.
        self._bn_bare_what_pattern = re.compile(
            r"^([A-Za-z\u0980-\u09FF\-]+(?:\s+[A-Za-z\u0980-\u09FF\-]+)*)\s+(কী|কি)\s*[?।\u0964\uff1f]?\s*$",
            re.UNICODE,
        )
        # English bare why follow-up: "Why?" / "why?" — empty target so the
        # brain anchors the reason question to the previous conversation
        # topic (Phase 28). Checked with word boundary so "why are you"
        # style turns are not caught here.
        self._en_bare_why_re = re.compile(r"^why\s*[?।\u0964\uff1f]?\s*$", re.IGNORECASE)

        # Bengali capability / function follow-ups: one explicit regex per
        # phrasing so relations ('use' / 'capability') are unambiguous.
        # Order: most specific phrasings first, generic 'কাজ কি' last.
        self._bn_capability_followups = [
            (re.compile(r"(?:([A-Za-z\u0980-\u09ff]+(?:\s+[A-Za-z\u0980-\u09ff]+){0,2})\s*-?এর)?\s*কিসের\s*কাজে?\s*লাগে?\s*[?।\u0964\uff1f]?", re.UNICODE), "use"),
            (re.compile(r"(সেট|এট|ওট|এটা|সেটা|ওটা)?\s*কি\s*কাজ\s*করতে?\s*পারে\s*[?।\u0964\uff1f]?", re.UNICODE), "capability"),
            (re.compile(r"(এটা|সেটা|ওটা)?\s*কি\s*করতে?\s*পারে\s*[?।\u0964\uff1f]?", re.UNICODE), "capability"),
            (re.compile(r"(?:([A-Za-z\u0980-\u09ff]+(?:\s+[A-Za-z\u0980-\u09ff]+){0,2})\s*-?এর)?\s*কাজ\s*কি\s*[?।\u0964\uff1f]?", re.UNICODE), "use"),
        ]
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
            # Phase 28: "What is the color of the sky?" must anchor
            # the head noun "sky", not the article "the".
            re.compile(r"what\s+is\s+the\s+(\w+(?:\s+\w+){0,3})\s*\??", re.IGNORECASE),
            # "what is X?" — the article form is checked FIRST so
            # "What is a bridge?" captures 'bridge' instead of 'a'.
            re.compile(r"what\s+is\s+(?:a|an)\s+(\w+)\s*\??", re.IGNORECASE),
            re.compile(r"what\s+is\s+(\w+)\s*\??", re.IGNORECASE),
            # "who are you?" / "who created you?" / "who made you?" —
            # self-identity questions; group 1 captures the addressed word
            # so the brain can resolve it to itself (Misty) as the target.
            re.compile(r"^who\s+(?:are|created|made|built)\s+(you)\??\s*$", re.IGNORECASE),
        ]

        self._en_greeting_patterns = [
            re.compile(r"^(hello|hi|hey|greetings)\b", re.IGNORECASE),
        ]
        self._en_capability_pattern = re.compile(
            r"^(?:can|do)\s+(?:you|misty)\b.*\b(?:learn|know|do|understand)\b.*\??$",
            re.IGNORECASE,
        )
        self._en_recognition_pattern = re.compile(
            r"^(?:do\s+you\s+)?remember\s+me\??$|^do\s+you\s+recognize\s+me\??$",
            re.IGNORECASE,
        )
        # English casual/social turns matching the Bengali ones above:
        # "how are you", "what are you thinking", "that's good".
        self._en_casual_patterns = [
            re.compile(r"(how are you|how's it going|how are things)", re.IGNORECASE),
            re.compile(r"(what are you thinking|what are you thinking about)", re.IGNORECASE),
            re.compile(r"(that's good|that is good|nice|sounds good|cool)", re.IGNORECASE),
            # Clarification / casual follow-up: "I don't understand",
            # "what's up", "why" — conversational continuations.
            re.compile(
                r"(i don't understand|i do not understand|i don't get it|"
                r"what's up|what is up|why\b|what happened|say again|repeat)",
                re.IGNORECASE,
            ),
        ]

        # English correction signals that start a turn.
        self._en_correction_patterns = [
            re.compile(r"^\s*(no\b|wrong\b|actually\b|it is\b|it's\b|that's wrong)", re.IGNORECASE),
        ]

        # English explicit teaching: "learn that ...", "remember that ...".
        # Separator may be a space or a colon ("remember that: X is Y").
        self._en_teach_patterns = [
            re.compile(
                r"(?:learn that|remember that|note that|keep in mind that)[:\s]+(.+)$",
                re.IGNORECASE,
            ),
        ]

        # English "X means Y" / "X is a/an Y" assertions
        self._en_is_a_pattern = re.compile(
            r"(\w+)\s+(?:means|is a|is an)\s+(.+)$",
            re.IGNORECASE,
        )

        # English capability/function follow-ups with an empty target,
        # resolved against the previous conversation topic by the brain:
        # "what can that do?" (capability), "what does it do?" (use),
        # "how does that work?" (mechanism).
        self._en_capability_followup_re = re.compile(
            r"\b(what|how)\b\s+(can|does)\s+\b(that|it|this|he|she)\b\s+(do|work)\b",
            re.IGNORECASE,
        )

        # English pronoun-targeted queries with an empty target, resolved
        # against the dialogue context by the brain:
        # "who is he?", "what is it?", "who created her?"
        self._en_pronoun_query_pattern = re.compile(
            r"\b(who|what|which)\b\s+.*\b(it|its|him|her|he|she|this|that)\b",
            re.IGNORECASE,
        )

        # Humor / safe-joke requests (Bengali and English). Kept at class
    # level like the closure patterns so 'মজার কিছু বলো।' / 'Tell me a
    # joke' are recognized before intent classification.
    _BN_HUMOR_REQUEST_RE = re.compile(r"(?<![A-Za-z\u0980-\u09ff])(মজার|রসিকতা|জোকস|হাসার)(?![A-Za-z\u0980-\u09ff]).*(?<![A-Za-z\u0980-\u09ff])(বলো|বলুন|দাও|শোনাও)(?![A-Za-z\u0980-\u09ff])", re.UNICODE)
    _EN_HUMOR_REQUEST_RE = re.compile(r"(?<![A-Za-z])(tell\s+me\s+a\s+joke|say\s+something\s+funny|make\s+me\s+laugh)(?![A-Za-z])", re.IGNORECASE)

    @classmethod
    def _is_humor_request(cls, text: str) -> bool:
        return bool(
            cls._BN_HUMOR_REQUEST_RE.search(text)
            or cls._EN_HUMOR_REQUEST_RE.search(text)
        )

# Bengali pronoun-targeted queries with an empty target (Bengali and English). Kept in the
    # parser so both Bengali and English inputs are caught before intent
    # classification rather than only inside the dialogue driver.
    _BN_CLOSURE_RE = re.compile(r'\b(বাই|বিদায়|ঠিক আছে|অনেক ধন্যবাদ|আজকে এই পর্যন্ত|টাটা|শুভরাত্রি|ঘুমিয়ে পড়লাম)\b', re.UNICODE)
    _EN_CLOSURE_RE = re.compile(r'\b(bye|goodbye|good night|see you|that\'?s all|farewell|goodbye!)\b', re.IGNORECASE)

    @classmethod
    def _is_closure(cls, text: str) -> bool:
        """True when the input is a conversation closing phrase."""
        return bool(
            cls._BN_CLOSURE_RE.search(text or "")
            or cls._EN_CLOSURE_RE.search(text or "")
        )

    # Bengali who-created-X queries: "X তৈরি করেছে কে?", "X কে তৈরি করেছে?"
    _bn_who_creator_re = re.compile(
        r'([A-Za-z\u0980-\u09FF][A-Za-z\u0980-\u09FF0-9\s\-]*?)\s*(?:এর|র)?\s*'
        r'(?:তৈরি\s+(?:কর|বান)\w*\s+কে|কে\s+তৈরি\s+(?:কর|বান)\w*|'
        r'(?:নির্মাতা|প্রস্তুতকারী)\s+(?:কে|কি)\b'
        r'(?:\s*[?।\uff1f]|\s*$))',
        re.IGNORECASE | re.UNICODE,
    )
    # English who-created queries: "who created you?", "who made misty?"
    _en_who_creator_re = re.compile(
        r'who\s+(created|made|built|invented|developed)'
        r'\s+([a-z\u0980-\u09FF][a-z\u0980-\u09FF0-9\s\-]*)',
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

        # Conversation closure ("বাই", "goodbye", "that's all") must override
        # statement detection so farewells are answered politely instead of
        # being absorbed as a teach attempt.
        if self._is_closure(text):
            return ParseResult(
                intent=IntentType.CONVERSATION,
                entities={"closure": True},
                raw_text=text,
                confidence=0.9,
            )
        # Humor requests are CONVERSATION turns with an explicit
        # 'kind': the ACT layer then answers with a safe joke.
        if self._is_humor_request(text):
            return ParseResult(
                intent=IntentType.CONVERSATION,
                entities={"kind": "humor_request"},
                raw_text=text,
                confidence=0.8,
            )
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

    _BN_CLAUSE_STOPS = frozenset({
        "মানে", "এবং", "কিন্তু", "যে", "তা", "এটি", "হলে", "এব", "বা", "তখন",
        "মনে", "এটাই", "সেট", "ওটাই", "এখানে", "সেখানে",
    })

    @staticmethod
    def _trim_bn_clause(obj: str) -> str:
        """Remove trailing clause stop words from a Bengali is_a object."""
        keep: list[str] = []
        for word in obj.split():
            if word in NLUParser._BN_CLAUSE_STOPS:
                break
            keep.append(word)
        return " ".join(keep)
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

        # Bengali who-created queries: X-created-by-whom forms.
        who_match = self._bn_who_creator_re.search(text)
        if who_match:
            subject = who_match.group(1).strip()
            # Normalise accusative/dative forms so the brain resolves
            # "তুমি" / "তোমাকে" / "আপনাকে" to Misty herself.
            # Phase 28: normalise inflected forms; empty subject -> self-query.
            subject = re.sub(r"(তুমি|তোমা|তোমাকে|আপনি?|আপনা|মিস্টি|মিস্টিকে|কে)$", "", subject).strip()
            if not subject or subject in {"তুমি", "তোমা", "তোমাকে", "আপনি", "আপনা", "আপনাকে", "মিস্টি", "মিস্টিকে", "you"}:
                subject = "Misty"
            return ParseResult(
                intent=IntentType.QUERY_WHO,
                query={"subject": subject, "relation": "creator_of"},
                raw_text=text,
                confidence=0.92,
            )
        # English who-created queries ("who created you?", "who made misty?").
        who_match = self._en_who_creator_re.search(text)
        if who_match:
            return ParseResult(
                intent=IntentType.QUERY_WHO,
                query={"subject": who_match.group(2).strip(), "relation": "creator_of"},
                raw_text=text,
                confidence=0.92,
            )
        # Deterministic Physics takes priority over generic questions, but
        # only when the input actually contains numeric values or an
        # equation ("এর কাজ কি?" is a vocabulary question, not physics).
        if PHYSICS_ENGINE.solve(text) is not None and re.search(r"\d|=", text):
            return ParseResult(
                intent=IntentType.PHYSICS,
                entities={"physics_text": text},
                raw_text=text,
                confidence=0.98,
            )

        # Deterministic mathematics takes priority over generic questions,
        # but only when the input contains a number or an operator
        # ("সেতু কী?" / "What is a bridge?" are definitions, not math).
        if MATH_ENGINE.looks_mathematical(text) and re.search(r"\d|[+\-*/^%=]", text):
            return ParseResult(
                intent=IntentType.MATH,
                entities={"math_text": text},
                raw_text=text,
                confidence=0.98,
            )

        if self._bn_recognition_pattern.search(text):
            return ParseResult(
                intent=IntentType.RECOGNITION_QUERY,
                raw_text=text,
                confidence=0.92,
            )
        if self._bn_capability_pattern.search(text):
            return ParseResult(
                intent=IntentType.CAPABILITY_QUERY,
                raw_text=text,
                confidence=0.88,
            )

        # Casual/social turns are detected before greetings so friendly
        # chit-chat ("কি খবর", "তুমি কি ভাবছো") is not reduced to the
        # generic greeting acknowledgement.
        for pattern in self._bn_casual_patterns:
            if pattern.search(text):
                return ParseResult(
                    intent=IntentType.CONVERSATION,
                    raw_text=text,
                    confidence=0.85,
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
            definition = self._trim_bn_clause(is_a_match.group(2).strip())
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

        # Bare Bengali "what is X" form without হলো/মানে: "স্যাটেলাইট কি?"
        # is classified as QUERY_WHAT on X with confidence 0.7 so the
        # knowledge-inference synthesizer can answer from stored facts
        # instead of falling back to the generic echo.
        # Bare reason follow-ups are checked BEFORE the generic Bengali
        # bare-what pattern, otherwise "কারণ কি?" would be captured as a
        # definition query about the word "কারণ" instead of a why-question
        # anchored to the previous topic (Phase 28).
        if re.search(
            r"^(কি|কী)?\s*কারণ(টা|টি)?\s+(কি|কী)[?।\u0964\uff1f]?\s*$|^(কী|কি)\s*কারণ|^(কেন|কেনো)\s*[?।\u0964\uff1f]?\s*$",
            text,
            re.UNICODE,
        ):
            return ParseResult(
                intent=IntentType.QUERY_WHAT,
                query={"type": "what", "relation": "why", "target": ""},
                raw_text=text,
                confidence=0.7,
            )
        if self._en_bare_why_re.search(text):
            return ParseResult(
                intent=IntentType.QUERY_WHAT,
                query={"type": "what", "relation": "why", "target": ""},
                raw_text=text,
                confidence=0.7,
            )
        bare_match = self._bn_bare_what_pattern.search(text)
        if bare_match:
            target = bare_match.group(1).strip()
            # Two-word guard: a subject pronoun plus an adjective before
            # "কি" ("আমি ভালো কি?", "সে খারাপ কি?") is a conversational
            # turn, not a definition query.
            if len(target.split()) == 2 and target.split()[0] in {
                "আমি", "তুমি", "আপনি", "সে", "তার",
            }:
                bare_match = None
            # Possessive-start guard: "এর কাজ কি?" / "এর রঙ কী?" are
            # capability / attribute follow-ups (the "কাজ কি" / capability
            # blocks handle them with an empty target anchored to the
            # previous topic), not definition queries about "এর".
            if target.split() and target.split()[0] in {
                "এর", "আমার", "তার", "এটার", "সেটার",
            }:
                bare_match = None
        if bare_match:
            target = bare_match.group(1).strip()
            if target not in {"তুমি", "আপনি", "মিস্টি", "সে", "এটা", "ওটা", "এই", "সেই"}:
                return ParseResult(
                    intent=IntentType.QUERY_WHAT,
                    query={"type": "what", "relation": "is_a", "target": target},
                    raw_text=text,
                    confidence=0.7,
                )

                # Bengali capability / function follow-ups with an empty or
        # implicit target, resolved against the previous topic by the
        # brain: "এর কিসের কাজে লাগে" (use), "সেটা কি কাজ করতে পারে"
        # (capability), "কাজ কি" (use).
        for cap_re, relation in self._bn_capability_followups:
            cap_match = cap_re.search(text)
            if cap_match:
                topic = cap_match.group(1).strip() if cap_match.group(1) else ""
                # Skip pronoun-only matches here; those reach the
                # pronoun-query block and inherit the prior topic.
                if topic in {"সেট", "এট", "ওট", "এটা", "সেটা", "ওটা", "এর", "এর:", "এর "}:
                    topic = ""
                return ParseResult(
                    intent=IntentType.QUERY_WHAT,
                    query={"type": "what", "relation": relation, "target": topic},
                    raw_text=text,
                    confidence=0.75,
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
        # Deterministic Physics takes priority over generic questions, but
        # only when the input actually contains numeric values or an
        # equation ("এর কাজ কি?" is a vocabulary question, not physics).
        if PHYSICS_ENGINE.solve(text) is not None and re.search(r"\d|=", text):
            return ParseResult(
                intent=IntentType.PHYSICS,
                entities={"physics_text": text},
                raw_text=text,
                confidence=0.98,
            )

        # Deterministic mathematics takes priority over generic questions,
        # but only when the input contains a number or an operator
        # ("সেতু কী?" / "What is a bridge?" are definitions, not math).
        if MATH_ENGINE.looks_mathematical(text) and re.search(r"\d|[+\-*/^%=]", text):
            return ParseResult(
                intent=IntentType.MATH,
                entities={"math_text": text},
                raw_text=text,
                confidence=0.98,
            )

        if self._en_recognition_pattern.search(text):
            return ParseResult(
                intent=IntentType.RECOGNITION_QUERY,
                raw_text=text,
                confidence=0.92,
            )
        if self._en_capability_pattern.search(text):
            return ParseResult(
                intent=IntentType.CAPABILITY_QUERY,
                raw_text=text,
                confidence=0.88,
            )

        for pattern in self._en_casual_patterns:
            if pattern.search(text):
                return ParseResult(
                    intent=IntentType.CONVERSATION,
                    raw_text=text,
                    confidence=0.85,
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

        # Deterministic capability / function follow-ups ("What can that
        # do?", "What does it do?", "How does that work?") — empty target
        # so the brain anchors the question to the previous topic.
        cap_match = self._en_capability_followup_re.search(text)
        if cap_match:
            # 'what can X do' -> capability; 'what does X do' -> use;
            # 'how does X work' -> how (mechanism explanation).
            verb, action = cap_match.group(2).lower(), cap_match.group(4).lower()
            if verb == "can":
                relation = "capability"
            elif action == "work":
                relation = "how"
            else:
                relation = "use"
            return ParseResult(
                intent=IntentType.QUERY_WHAT,
                query={
                    "type": "what",
                    "relation": relation,
                    "target": "",
                },
                raw_text=text,
                confidence=0.75,
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
