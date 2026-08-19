"""
Phase 41: Self-correction (CorrectionAuditor).

Misty listens for challenges — messages that say her previous answer was
wrong ("এটা ভুল", "আপনার উত্তর ভুল", "no, that's wrong") — and reacts
the way a careful human would:

1. Detect the challenge (bilingual pattern set, Bengali + English).
2. Inspect her own memory: was her previous answer contradicted by a
   fact she already knows?  If yes, retract it (lower confidence / mark
   the claim) and state the corrected version in warm, humble Bengali.
3. Log every correction attempt in ``self_correction`` — how many
   challenges arrived, how many she accepted, and why — so the behavior
   is fully inspectable rather than magical.

Deterministic (no LLM). All memory operations happen against the brain's
semantic memory / knowledge graph, exactly like Phase 33's gap
assessor.
"""

import re
import time as time_module
from dataclasses import dataclass
from typing import Any, Dict, List, Tuple

# ---------------------------------------------------------------------------
# Challenge detection
# ---------------------------------------------------------------------------
_CHALLENGE_MARKERS = (
    # English markers
    "that's wrong",
    "thats wrong",
    "that is wrong",
    "that's incorrect",
    "thats incorrect",
    "that is incorrect",
    "wrong answer",
    "incorrect answer",
    "that's not right",
    "thats not right",
    "you are wrong",
    "u are wrong",
    "you're wrong",
    "ur wrong",
    "not correct",
    "not true",
    "it's false",
    "its false",
    "that's false",
    "thats false",
    "you got it wrong",
    # Bengali markers (Bengali script only; visually-unambiguous tokens)
    "ভুল",  # wrong / mistake
    "এটা ভুল",
    "এটা ঠিক নয়",
    "এটা ঠিকনা",
    "আপনার উত্তর ভুল",
    "আপনার উত্তরটা ভুল",
    "উত্তর ভুল",
    "সেটা ঠিক হয়নি",
    "এটা মিলে নি",
    "ভুল বলছো",
    "ভুল বলছেন",
    "আসলে তা না",
    "আসলে তা নয়",
)


def _detect_challenge(text: str) -> Tuple[bool, str]:
    """Return (is_challenge, matched_marker) for the user input."""
    normalized = re.sub(r"\s+", " ", text.strip().lower())
    for marker in _CHALLENGE_MARKERS:
        if marker in normalized:
            return True, marker
    return False, ""


# ---------------------------------------------------------------------------
# Correction log
# ---------------------------------------------------------------------------
@dataclass
class CorrectionEntry:
    """One recorded self-correction event."""

    correction_id: str
    timestamp: float
    challenge: str
    matched_marker: str
    claimed_claim: str
    accepted: bool
    reason: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "correction_id": self.correction_id,
            "timestamp": self.timestamp,
            "challenge": self.challenge,
            "matched_marker": self.matched_marker,
            "claimed_claim": self.claimed_claim,
            "accepted": self.accepted,
            "reason": self.reason,
        }


# ---------------------------------------------------------------------------
# Auditor
# ---------------------------------------------------------------------------
class CorrectionAuditor:
    """Watches conversation turns for challenges and self-corrects.

    The auditor never mutates memory during detection — correction only
    happens when a contradiction is provable from the brain's own stored
    knowledge.  When Misty is unsure, she admits it instead of guessing.
    """

    def __init__(self, max_log_entries: int = 50) -> None:
        self._log: List[CorrectionEntry] = []
        self._max_entries = max_log_entries
        self._next_id = 0
        # The brain's previous answer text (set per turn by the wiring).
        self.last_output: str = ""

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    @property
    def last_output(self) -> str:  # pragma: no cover - property setter below
        return self._last_output

    @last_output.setter
    def last_output(self, value: str) -> None:
        self._last_output = value

    def last_correction(self) -> CorrectionEntry | None:
        return self._log[-1] if self._log else None

    def audit(
        self,
        user_input: str,
        previous_answer: str,
        check_fn: Any,
    ) -> Tuple[bool, str | None]:
        """Audit one turn.

        Args:
            user_input: Current user message.
            previous_answer: The brain's previous reply text.
            check_fn: Callable(claim_tokens: List[str]) -> Dict[str, Any]
                      that re-checks candidate claims against the brain's
                      own knowledge and returns
                      ``{"contradicted": bool, "reason": str}``.
        Returns:
            (challenge_detected, correction_note).  ``correction_note`` is
            set only when the auditor accepted the correction; it is the
            warm bilingual line the brain prepends/appends to its reply.
        """
        is_challenge, marker = _detect_challenge(user_input)
        if not is_challenge:
            return False, None

        # Extract the most likely claim tokens from the user's challenge
        # (tokens not present in any marker phrase) to re-check against
        # the brain's own knowledge.
        claim_tokens = self._claim_tokens(user_input)

        entry = CorrectionEntry(
            correction_id=f"corr-{self._next_id:04d}",
            timestamp=time_module.time(),
            challenge=user_input.strip()[:500],
            matched_marker=marker,
            claimed_claim=previous_answer.strip()[:300],
            accepted=False,
            reason="no contradictory evidence",
        )
        self._next_id += 1

        note: str | None = None
        if claim_tokens:
            verdict = check_fn(claim_tokens)
            entry.accepted = bool(verdict.get("contradicted", False))
            entry.reason = str(verdict.get("reason", entry.reason))

        if entry.accepted:
            # Warm Bengali admission — the brain owns the mistake and
            # does not pretend otherwise.
            note = "আপনি ঠিক বলেছেন — আমার আগের উত্তরটা ভুল ছিল। ধন্যবাদ, আমি এটি সংশোধন করে নিচ্ছি।"
        elif claim_tokens:
            # Challenge detected but nothing provable: the humble
            # epistemic admission instead of a confident claim.
            note = (
                "আপনার কথাটা আমি মনোদিয়ে শুনেছি। আমার সাম্প্রতিক তথ্যে "
                "এর প্রমাণ পাচ্ছি না — আপাতত আমি নিশ্চিত উত্তর দেওয়ার "
                "পরিবর্তে এটি নিয়ে আগে সাবধানে ভেবে নেই।"
            )
        else:
            # Generic challenge with no extractable claim.
            note = (
                "আমি বুঝতে পারছি আপনি আমার আগের উত্তরটায় দ্বিমত করছেন। "
                "আপনি কোন বিষয়ে সঠিক তথ্য চাচ্ছেন সেটা একটু খোলসায় "
                "বললে আমি আবার যাচাই করে দেব।"
            )

        self._log.append(entry)
        if len(self._log) > self._max_entries:
            self._log = self._log[-self._max_entries :]
        return True, note

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------
    @staticmethod
    def _claim_tokens(text: str) -> List[str]:
        """Strip marker phrases and keep remaining meaningful tokens."""
        normalized = re.sub(r"\s+", " ", text.strip().lower())
        cleaned = normalized
        for marker in _CHALLENGE_MARKERS:
            cleaned = cleaned.replace(marker, " ")
        cleaned = re.sub(r"[^\w\u0980-\u09ff]", " ", cleaned).strip()
        tokens = [w for w in cleaned.split() if len(w) > 2]
        return tokens[:6]

    def summary(self) -> Dict[str, Any]:
        return {
            "enabled": True,
            "challenges_received": len(self._log),
            "corrections_accepted": sum(1 for entry in self._log if entry.accepted),
            "last_correction": self.last_correction().to_dict() if self.last_correction() else None,
        }
