"""
Fact Aging and Confidence Decay.

A small but biologically meaningful layer on top of semantic memory.

Why it matters
--------------
Web-learned knowledge is not immortal. News changes, rankings shift and a
"fact" captured from the internet in 2026 may be false by 2028. Meanwhile the
brain's own curated knowledge (user input, training corpus) is deliberately
stable. This module therefore treats memory the way real brains treat it:

- Confidence of *learned* (web_learning) facts decays slowly over calendar
  time. Stale knowledge fades; it never gets a free pass.
- Facts that are still being *used* (accessed during recall) keep their
  freshness — accessed_at is refreshed on each sweep that touches them.
- Facts that decay below a prune threshold are removed from memory, but the
  decision is always written to an inspectable audit log. Nothing silently
  disappears.
- Manually taught and curated facts are protected from aging so the brain's
  identity and core training are stable.

All decisions are deterministic, rule-based and fully inspectable — no LLM.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Dict, List

if TYPE_CHECKING:  # pragma: no cover
    from brain.core.brain import Brain

# Confidence halves over this many days for web-learned facts.
_HALF_LIFE_DAYS: float = 90.0
# Below this confidence a fact is pruned from memory.
_PRUNE_THRESHOLD: float = 0.35
# Floor: even a brand-new web fact below this is pruned immediately (junk).
_JUNK_THRESHOLD: float = 0.20
# Sources that are protected from decay (curated, taught or identity facts).
_PROTECTED_SOURCES: tuple = ("user_input", "curriculum", "training")
# Hard cap on the audit log so state snapshots stay bounded.
_MAX_LOG_ENTRIES: int = 100


@dataclass
class AgingDecision:
    """One record in the aging audit log."""

    fact_key: str
    subject: str
    predicate: str
    obj: str
    confidence_before: float
    confidence_after: float
    action: str  # decayed | refreshed | pruned | protected | skipped


class FactAger:
    """Ages and prunes web-learned semantic facts with an audit log."""

    def __init__(self, brain: Brain) -> None:
        self.brain = brain
        self._decisions: List[AgingDecision] = []

    # ------------------------------------------------------------------
    # Core mechanics
    # ------------------------------------------------------------------

    @staticmethod
    def _decayed_confidence(confidence: float, days_old: float) -> float:
        """Apply half-life decay; never below zero."""
        if days_old <= 0.0:
            return confidence
        return max(0.0, confidence * 2.0 ** (-days_old / _HALF_LIFE_DAYS))

    def _record(self, decision: AgingDecision) -> None:
        self._decisions.append(decision)
        if len(self._decisions) > _MAX_LOG_ENTRIES:
            self._decisions = self._decisions[-_MAX_LOG_ENTRIES:]

    def age_facts(self, now: float | None = None) -> Dict[str, Any]:
        """One aging pass over semantic memory.

        Returns a summary dict and writes every decision to the audit log.
        Facts whose source is in ``_PROTECTED_SOURCES`` are only refreshed
        (accessed_at updated) and never decayed or pruned.
        """
        now = now if now is not None else __import__("time").time()
        semantic = self.brain.semantic_memory
        summary: Dict[str, Any] = {
            "scanned": 0,
            "decayed": 0,
            "refreshed": 0,
            "pruned": 0,
            "protected": 0,
            "skipped": 0,
        }

        for key, fact in list(semantic.facts.items()):
            summary["scanned"] += 1
            if fact.source in _PROTECTED_SOURCES:
                fact.accessed_at = now
                summary["protected"] += 1
                self._record(
                    AgingDecision(
                        fact_key=key,
                        subject=fact.subject,
                        predicate=fact.predicate,
                        obj=fact.obj,
                        confidence_before=fact.confidence,
                        confidence_after=fact.confidence,
                        action="protected",
                    )
                )
                continue

            # Cold-start safety: facts restored from persistent storage may
            # carry a created_at of 0 (unknown birth time). They must never
            # be aged billions of days — treat them as freshly restored and
            # let aging resume from the current clock going forward.
            anchor = fact.created_at if fact.created_at and fact.created_at > 0 else now
            days_old = (now - anchor) / 86400.0
            if days_old <= 0.0:
                # Nothing to decay yet — but a fact that was born below the
                # junk floor is garbage from the start and gets pruned.
                fact.accessed_at = now
                if fact.confidence < _JUNK_THRESHOLD:
                    semantic.remove_fact(key)
                    summary["pruned"] += 1
                    self._record(
                        AgingDecision(
                            fact_key=key,
                            subject=fact.subject,
                            predicate=fact.predicate,
                            obj=fact.obj,
                            confidence_before=fact.confidence,
                            confidence_after=fact.confidence,
                            action="pruned",
                        )
                    )
                    continue
                summary["refreshed"] += 1
                self._record(
                    AgingDecision(
                        fact_key=key,
                        subject=fact.subject,
                        predicate=fact.predicate,
                        obj=fact.obj,
                        confidence_before=fact.confidence,
                        confidence_after=fact.confidence,
                        action="refreshed",
                    )
                )
                continue

            after = self._decayed_confidence(fact.confidence, days_old)
            fact.accessed_at = now

            if after < _PRUNE_THRESHOLD or fact.confidence < _JUNK_THRESHOLD:
                semantic.remove_fact(key)
                summary["pruned"] += 1
                self._record(
                    AgingDecision(
                        fact_key=key,
                        subject=fact.subject,
                        predicate=fact.predicate,
                        obj=fact.obj,
                        confidence_before=fact.confidence,
                        confidence_after=after,
                        action="pruned",
                    )
                )
                continue

            if abs(after - fact.confidence) < 1e-9:
                summary["refreshed"] += 1
            else:
                summary["decayed"] += 1
            fact.confidence = after
            self._record(
                AgingDecision(
                    fact_key=key,
                    subject=fact.subject,
                    predicate=fact.predicate,
                    obj=fact.obj,
                    confidence_before=fact.confidence,
                    confidence_after=after,
                    action="decayed",
                )
            )

        return summary

    # ------------------------------------------------------------------
    # Inspection
    # ------------------------------------------------------------------

    @property
    def decisions(self) -> List[AgingDecision]:
        return list(self._decisions)

    def summary(self) -> Dict[str, Any]:
        """Bounded snapshot for the brain state API."""
        totals: Dict[str, int] = {}
        for decision in self._decisions:
            totals[decision.action] = totals.get(decision.action, 0) + 1
        return {
            "enabled": True,
            "total_decisions": len(self._decisions),
            "recent": [
                {
                    "fact_key": d.fact_key,
                    "subject": d.subject,
                    "action": d.action,
                    "confidence_before": d.confidence_before,
                    "confidence_after": d.confidence_after,
                }
                for d in self._decisions[-5:]
            ],
            "counts": totals,
            "config": {
                "half_life_days": _HALF_LIFE_DAYS,
                "prune_threshold": _PRUNE_THRESHOLD,
                "junk_threshold": _JUNK_THRESHOLD,
            },
        }
