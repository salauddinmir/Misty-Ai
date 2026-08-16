"""Coreference Resolution.
Maps pronouns and ellipsis references in Bengali and English input to
the most salient entity from the ongoing dialogue context.

Examples:
    User:  "আমার নাম সালাউদ্দিন"
    Brain: "নাম মনে রাখা হয়েছে, সালাউদ্দিন।"
    User:  "সে কে?"            -> resolves "সে" -> "সালাউদ্দিন"
    User:  "আরও বলো"           -> maps to CONTINUATION intent

This is a rule-based, LLM-free resolver that leans on the salience
ranking maintained by brain.dialogue.context.DialogueContext.

Note: Python's \b word boundary does not recognize Bengali word
characters, so boundaries are expressed with explicit lookarounds
around non-word Unicode categories.
"""

from __future__ import annotations

import re

from brain.dialogue.context import extract_entity_candidates

_BN_WORD = r"(?:^|(?<=[\s\u0964:।\u2019.,;]))"
_BN_TRAIL = r"(?:$|(?=[\s\u0964:।\u2019.,;?]))"

# Pronoun patterns: the pronoun token surrounded by whitespace or
# Bengali sentence punctuation (not using \b, which fails on Bengali).
_BN_PRONOUNS = re.compile(
    _BN_WORD + r"(সে|তার|তাকে|এই|এটা|ওটা|এগুলো|ওগুলো)" + _BN_TRAIL,
    re.UNICODE,
)
_EN_PRONOUNS = re.compile(
    r"\b(it|its|him|her|he|she|this|that|these|those|himself|herself)\b",
    re.IGNORECASE,
)

# Ellipsis/continuation triggers that refer back to the last topic.
_CONTINUATION_PATTERNS = [
    # Bengali continuation keywords allow optional trailing words
    # ("আরো বলো", "আরেকটু বলুন"), while the English triggers match
    # exactly so that ordinary sentences are not swallowed.
    re.compile(
        r"^\s*(আরও|আরো|আরেকটু|আরও বল[োও]?|আর বলো|বলো|বলুন|জানাও|আর|পরে)(?:\s+[\w\u0980-\u09FF]+)*\s*[?.?\u0964]?\s*$",
        re.UNICODE,
    ),
    re.compile(r"^\s*(more|tell me more|again|continue)\s*[?.]?\s*$", re.IGNORECASE),
]

# English who/what queries whose target is a pronoun: "who is he",
# "who created it", "what is this". Resolved against salience.
_EN_PRONOUN_QUERY = re.compile(
    r"\b(?:who|what|which)\b\s+.*\b(it|him|her|he|she|this|that)\b",
    re.IGNORECASE,
)


def _has_pronoun(text: str) -> bool:
    """True if the text contains a pronoun mention."""
    return bool(_BN_PRONOUNS.search(text) or _EN_PRONOUNS.search(text))


def pronoun_target(text: str, salient_entities: list[str]) -> str | None:
    """Return the entity a pronoun in `text` refers to, or None.

    Uses the salience ranking: the most salient entity is the default
    target for any pronoun mention. If the text contains real entity
    names, the first named entity wins (no pronoun resolution needed).
    """
    if not text:
        return None
    names = extract_entity_candidates(text)
    has_own_entity = bool(names)
    is_pronoun_only = not has_own_entity and (_has_pronoun(text) or _EN_PRONOUN_QUERY.search(text))
    if is_pronoun_only and salient_entities:
        return salient_entities[0]
    if has_own_entity:
        return names[0]
    return None


def is_continuation(text: str) -> bool:
    """True if the text is an ellipsis that continues the last topic."""
    return any(pattern.search(text) for pattern in _CONTINUATION_PATTERNS)


def resolve_entities(text: str, salient_entities: list[str]) -> list[str]:
    """Return the effective entity list for this turn.

    Real names mentioned in the text take priority; a pronoun-only
    turn resolves to the most salient prior entity; a continuation
    ellipsis resolves to the current topic entity.
    """
    base = extract_entity_candidates(text)
    if base:
        return base
    if is_continuation(text) and salient_entities:
        return [salient_entities[0]]
    target = pronoun_target(text, salient_entities)
    if target:
        return [target]
    return []
