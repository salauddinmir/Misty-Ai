"""
Phase 45: Consolidation Sweep — rehearsal, quarantine cleanup and merge.

A nightly-sleep analogue for MISTY's semantic memory. Where Phase 44 (fact
aging) handles *decay*, this engine handles the other half of biological
memory consolidation:

1. REHEARSE — low-to-mid confidence facts that are not protected are briefly
   re-activated in the knowledge graph (their subject/object concepts are
   marked active). This is the deterministic equivalent of sleep rehearsal:
   memories that are rehearsed stay available; unattended ones fade.

2. CLEAN — facts sitting in quarantine (weaker claims already defeated by
   the Phase 42 fact verifier) are removed from memory, always with an audit
   log entry. Nothing disappears silently.

3. MERGE — duplicate web-learned facts (same subject and predicate) are
   collapsed into the single strongest claim. The weaker sibling is removed
   and its defeat is logged. Protected sources are never merged or removed.

Every decision lands in an inspectable, bounded audit log and surfaces in
the brain state under ``consolidation``. All of it is deterministic and
rule-based — no LLM.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Dict, List

from brain.graph.activation import SpreadingActivation

if TYPE_CHECKING:  # pragma: no cover
    from brain.core.brain import Brain

# Confidence window that rehearsal applies to: too weak = let it fade,
# too strong = already consolidated.
_REHEARSE_LOW: float = 0.35
_REHEARSE_HIGH: float = 0.85
# Sources protected from all consolidation damage — curated teaching data
# from every curriculum phase plus identity/user facts.
_PROTECTED_SOURCES: tuple = (
    "user_input",
    "curriculum",
    "training",
    "commonsense_layer",
    "misty-mathematics-phase29",
    "misty-physics-phase30",
    "misty-literature-phase31",
    "misty-culture-phase32",
    "conversation_corpus",
)
# Hard cap on the audit log.
_MAX_LOG_ENTRIES: int = 100


@dataclass
class SweepDecision:
    """One record in the consolidation audit log."""

    fact_key: str
    subject: str
    predicate: str
    obj: str
    action: str  # rehearsed | merged_winner | merged_loser | quarantine_removed | protected | skipped
    confidence: float = 0.0
    detail: str = ""


class ConsolidationEngine:
    """Runs bounded consolidation sweeps over semantic memory."""

    def __init__(self, brain: Brain) -> None:
        self.brain = brain
        self._decisions: List[SweepDecision] = []
        # Budget per sweep so a single pass cannot rewrite the brain.
        self.max_merged_per_sweep: int = 16
        self.max_rehearsed_per_sweep: int = 24

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _record(self, decision: SweepDecision) -> None:
        self._decisions.append(decision)
        if len(self._decisions) > _MAX_LOG_ENTRIES:
            self._decisions = self._decisions[-_MAX_LOG_ENTRIES:]

    def _rehearse(self, fact_key: str, decision: SweepDecision) -> None:
        """Re-activate the subject and object concepts of a fact.

        Marks the fact's endpoints active in the concept graph and gives
        working memory a durable anchor so the next recall pass scores it
        higher. This is the deterministic sleep-rehearsal step.
        """
        semantic = self.brain.semantic_memory
        fact = semantic.facts.get(fact_key)
        if fact is None:
            return
        # Sleep rehearsal: re-activate the fact's subject and object
        # concepts via spreading activation, so associated recall scores
        # them higher on the next cycle (deterministic rehearsal effect).
        graph = self.brain.concept_graph
        propagator = SpreadingActivation()
        for concept_id in (fact.subject, fact.obj):
            try:
                propagator.activate(graph, concept_id, initial_activation=0.4)
            except Exception:  # pragma: no cover - concept missing or graph variant
                pass
        # Working-memory anchor: keep the fact on the radar for recall.
        wm = self.brain.working_memory
        anchor = f"rehearsal:{fact_key}"
        if anchor not in wm.items:
            wm.store(anchor, {"subject": fact.subject, "predicate": fact.predicate, "obj": fact.obj})
        self._record(decision)

    # ------------------------------------------------------------------
    # The sweep
    # ------------------------------------------------------------------

    def consolidation_sweep(self) -> Dict[str, Any]:
        """One bounded consolidation pass.

        Returns a summary dict and logs every decision. Protected facts are
        only rehearsed-anchored; quarantined/weaker duplicates are removed
        with an audit trail.
        """
        semantic = self.brain.semantic_memory
        quarantine: Dict[str, Any] = getattr(self.brain, "_learning_quarantine", None) or {}
        quarantined_keys: set = set()
        for entry in quarantine if isinstance(quarantine, list) else []:
            key = (
                entry.get("fact_key") or f"{entry.get('subject')}:{entry.get('predicate')}:{entry.get('obj')}"
                if isinstance(entry, dict)
                else None
            )
            if key:
                quarantined_keys.add(key)

        summary: Dict[str, Any] = {
            "scanned": 0,
            "rehearsed": 0,
            "merged": 0,
            "removed": 0,
            "protected": 0,
        }

        # --- Clean: remove quarantined claims (Phase 42 losers). ----------
        for key, fact in list(semantic.facts.items()):
            summary["scanned"] += 1
            if key in quarantined_keys:
                semantic.remove_fact(key)
                summary["removed"] += 1
                self._record(
                    SweepDecision(
                        fact_key=key,
                        subject=fact.subject,
                        predicate=fact.predicate,
                        obj=fact.obj,
                        action="quarantine_removed",
                        confidence=fact.confidence,
                        detail="defeated by fact-verification gate",
                    )
                )

        # --- Merge duplicates (web-learned, same subject+predicate). -------
        groups: Dict[tuple[str, str], List[str]] = {}
        for key, fact in list(semantic.facts.items()):
            if fact.source in _PROTECTED_SOURCES:
                continue
            groups.setdefault((fact.subject, fact.predicate), []).append(key)

        merged_count = 0
        for (subject, predicate), keys in groups.items():
            if len(keys) < 2:
                continue
            keys_sorted = sorted(keys, key=lambda k: semantic.facts[k].confidence, reverse=True)
            winner = keys_sorted[0]
            for loser_key in keys_sorted[1:]:
                if merged_count >= self.max_merged_per_sweep:
                    break
                loser = semantic.facts[loser_key]
                semantic.remove_fact(loser_key)
                summary["removed"] += 1
                merged_count += 1
                self._record(
                    SweepDecision(
                        fact_key=loser_key,
                        subject=subject,
                        predicate=predicate,
                        obj=loser.obj,
                        action="merged_loser",
                        confidence=loser.confidence,
                        detail=f"weaker duplicate of {winner}; keep {semantic.facts[winner].obj}",
                    )
                )
            if summary["removed"] > 0 and (subject, predicate) in groups:
                self._record(
                    SweepDecision(
                        fact_key=winner,
                        subject=subject,
                        predicate=predicate,
                        obj=semantic.facts[winner].obj,
                        action="merged_winner",
                        confidence=semantic.facts[winner].confidence,
                        detail="strongest surviving claim",
                    )
                )
        summary["merged"] = merged_count

        # --- Rehearse low/mid confidence facts (sleep rehearsal). ----------
        rehearsed = 0
        for key, fact in list(semantic.facts.items()):
            if fact.source in _PROTECTED_SOURCES:
                summary["protected"] += 1
                continue
            if _REHEARSE_LOW <= fact.confidence < _REHEARSE_HIGH and rehearsed < self.max_rehearsed_per_sweep:
                rehearsed += 1
                self._rehearse(
                    key,
                    SweepDecision(
                        fact_key=key,
                        subject=fact.subject,
                        predicate=fact.predicate,
                        obj=fact.obj,
                        action="rehearsed",
                        confidence=fact.confidence,
                        detail="sleep-rehearsal: concepts re-activated",
                    ),
                )
        summary["rehearsed"] = rehearsed
        return summary

    # ------------------------------------------------------------------
    # Inspection
    # ------------------------------------------------------------------

    @property
    def decisions(self) -> List[SweepDecision]:
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
                    "action": d.action,
                    "confidence": d.confidence,
                    "detail": d.detail,
                }
                for d in self._decisions[-5:]
            ],
            "counts": totals,
            "config": {
                "rehearse_window": [_REHEARSE_LOW, _REHEARSE_HIGH],
                "max_merged_per_sweep": self.max_merged_per_sweep,
                "max_rehearsed_per_sweep": self.max_rehearsed_per_sweep,
            },
        }
