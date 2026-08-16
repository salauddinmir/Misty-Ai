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


class IntentType(str, Enum):
    """Types of recognized user intents."""

    NAME_DECLARATION = "name_declaration"
    RELATION_DECLARATION = "relation_declaration"
    QUERY_WHO = "query_who"
    QUERY_WHAT = "query_what"
    STATEMENT = "statement"
    GREETING = "greeting"
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
            # "আমি X-এর creator" / "আমি X-এর Y"
            re.compile(
                r"আমি\s+([A-Za-z\u0980-\u09FF]+)-এর\s+([A-Za-z\u0980-\u09FF]+)",
                re.UNICODE,
            ),
            # "আমি X এর creator"
            re.compile(
                r"আমি\s+([A-Za-z\u0980-\u09FF]+)\s+এর\s+([A-Za-z\u0980-\u09FF]+)",
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
        ]

        self._bn_greeting_patterns = [
            re.compile(r"(হ্যালো|হাই|নমস্কার|আসসালামু|সালাম)", re.UNICODE),
        ]

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
        ]

        self._en_greeting_patterns = [
            re.compile(r"^(hello|hi|hey|greetings)\b", re.IGNORECASE),
        ]

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

        # Default: treat as unknown statement
        return ParseResult(
            intent=IntentType.STATEMENT,
            raw_text=text,
            confidence=0.3,
        )

    def _try_bengali(self, text: str) -> ParseResult:
        """Try Bengali pattern matching."""
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

        # Check relation declarations
        for i, pattern in enumerate(self._bn_relation_patterns):
            match = pattern.search(text)
            if match:
                if i < 2:
                    # "আমি X-এর Y" pattern
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
                else:
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

        return ParseResult(intent=IntentType.UNKNOWN, raw_text=text)

    def _try_english(self, text: str) -> ParseResult:
        """Try English pattern matching."""
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
