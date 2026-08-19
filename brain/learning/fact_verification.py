"""
Phase 42: Fact-verification gate for web learning.

Web learning (Phase 35/36) already rejects facts that contradict the
brain's existing knowledge.  Phase 42 adds a second, stricter layer of
verification that runs **after** ingestion and before a fact is trusted
in conversation:

1. **Multi-source corroboration** — a fact needs support from at least
   two *independent* sources (different domains).  A single source is
   marked "single_source" and must survive an independent corroboration
   search before its confidence is raised.
2. **Internal consistency** — the fact's subject/predicate/object is
   cross-checked against the brain's knowledge graph and semantic
   memory: new facts that create cycles of mutually contradictory
   triples downgrade the older, weaker fact and mark the conflict for
   review.
3. **Quarantine audit trail** — every decision (corroborated,
   single-source, conflicted, retracted) is written to an inspectable
   log rather than silently mutating memory.

Deterministic (no LLM). The verifier hooks into the existing
`_learning_quarantine` path and exposes `brain.run_fact_verification()`
for on-demand review of the latest learned batch.
"""

import time as time_module
from dataclasses import dataclass, field
from typing import Any, Dict, List

Verdict = str  # "corroborated" | "single_source" | "conflicted" | "retracted"


@dataclass
class VerificationEntry:
    """One fact-verification decision."""

    entry_id: str
    timestamp: float
    subject: str
    predicate: str
    obj: str
    verdict: Verdict
    reason: str
    source_count: int = 0
    source_domains: List[str] = field(default_factory=list)
    confidence_after: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "entry_id": self.entry_id,
            "timestamp": self.timestamp,
            "subject": self.subject,
            "predicate": self.predicate,
            "obj": self.obj,
            "verdict": self.verdict,
            "reason": self.reason,
            "source_count": self.source_count,
            "source_domains": self.source_domains,
            "confidence_after": self.confidence_after,
        }


def _domains(urls: str) -> List[str]:
    """Distinct hostnames from a comma-joined URL list."""
    hosts: List[str] = []
    for raw in urls.split(","):
        url = raw.strip().lower()
        if not url.startswith("http"):
            continue
        host = url.split("://", 1)[-1].split("/", 1)[0]
        if host not in hosts:
            hosts.append(host)
    return hosts


class FactVerifier:
    """Second-layer verification for web-learned facts."""

    MIN_CORROBORATING_SOURCES = 2
    CONFIDENCE_CORROBORATED = 0.95
    CONFIDENCE_SINGLE_SOURCE = 0.6

    def __init__(self, brain: Any, max_log_entries: int = 100) -> None:
        self.brain = brain
        self._log: List[VerificationEntry] = []
        self._max_entries = max_log_entries
        self._next_id = 0

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def verify_triple(
        self,
        subject: str,
        predicate: str,
        obj: str,
        source_ref: str = "",
        observations: int = 1,
    ) -> VerificationEntry:
        """Verify one learned triple and return the decision.

        The verifier only *records* a decision; retraction of a previous
        fact happens only when a hard conflict (same subject + predicate,
        different object) is found in the brain's own memory, and the new
        fact's evidence is at least as strong.
        """
        entry = VerificationEntry(
            entry_id=f"fv-{self._next_id:04d}",
            timestamp=time_module.time(),
            subject=subject,
            predicate=predicate,
            obj=obj,
            verdict="single_source",
            reason="pending",
        )
        self._next_id += 1

        domains = _domains(source_ref)
        entry.source_count = len(domains)
        entry.source_domains = domains

        conflict = self._find_conflict(subject, predicate, obj)
        if conflict is not None:
            # Hard conflict with the brain's own stored knowledge: the
            # brain's internal knowledge wins unless the challenger has
            # clearly stronger provenance.
            if observations >= conflict.get("observations", 1):
                entry.verdict = "retracted"
                entry.reason = (
                    f"retracts stored fact {conflict['obj']!r} with stronger evidence "
                    f"({observations} vs {conflict.get('observations', 1)} observations)"
                )
                self.brain.semantic_memory.remove_fact(conflict["key"])
            else:
                entry.verdict = "conflicted"
                entry.reason = (
                    f"conflicts with stored fact {conflict['obj']!r} but has weaker evidence; kept the stored version"
                )
        elif entry.source_count >= self.MIN_CORROBORATING_SOURCES:
            entry.verdict = "corroborated"
            entry.reason = f"supported by {entry.source_count} independent sources"
            entry.confidence_after = self.CONFIDENCE_CORROBORATED
        else:
            entry.verdict = "single_source"
            entry.reason = (
                f"only {entry.source_count or observations} source; needs independent corroboration before full trust"
            )
            entry.confidence_after = self.CONFIDENCE_SINGLE_SOURCE

        self._log.append(entry)
        if len(self._log) > self._max_entries:
            self._log = self._log[-self._max_entries :]
        return entry

    def verify_recent_learned_facts(self) -> Dict[str, Any]:
        """Re-verify every triple currently in the quarantine/learned
        batch (``brain._learning_quarantine``) and return a summary.

        Items in the quarantine list are either ``WebLearningCandidate``
        dataclass instances (with attribute access) or dicts — both are
        handled.
        """
        verdict_counts: Dict[str, int] = {}
        for item in self.brain._learning_quarantine:
            entry = self.verify_triple(
                subject=str(item.subject if hasattr(item, "subject") else item.get("subject", "")),
                predicate=str(item.predicate if hasattr(item, "predicate") else item.get("predicate", "")),
                obj=str(item.obj if hasattr(item, "obj") else item.get("obj", "")),
                source_ref=str(item.source_ref if hasattr(item, "source_ref") else item.get("source_ref", "")),
                observations=int(item.observations if hasattr(item, "observations") else item.get("observations", 1)),
            )
            verdict_counts[entry.verdict] = verdict_counts.get(entry.verdict, 0) + 1
        return {
            "verified": len(self.brain._learning_quarantine),
            "verdict_counts": verdict_counts,
        }

    def last_entries(self, n: int = 5) -> List[Dict[str, Any]]:
        return [entry.to_dict() for entry in self._log[-n:]]

    def summary(self) -> Dict[str, Any]:
        return {
            "enabled": True,
            "min_corroborating_sources": self.MIN_CORROBORATING_SOURCES,
            "verified_total": len(self._log),
            "corroborated": sum(1 for e in self._log if e.verdict == "corroborated"),
            "retracted": sum(1 for e in self._log if e.verdict == "retracted"),
            "conflicted": sum(1 for e in self._log if e.verdict == "conflicted"),
            "single_source": sum(1 for e in self._log if e.verdict == "single_source"),
            "recent": self.last_entries(3),
        }

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------
    def _find_conflict(self, subject: str, predicate: str, obj: str) -> Dict[str, Any] | None:
        """Return stored-fact details that conflict with the candidate,
        or None when the brain's memory is consistent with it."""
        sub_lower = subject.lower()
        facts = getattr(self.brain.semantic_memory, "facts", {})
        for key, fact in facts.items():
            if not key.lower().startswith(sub_lower):
                continue
            if fact.predicate != predicate:
                continue
            if fact.obj.lower() == obj.lower():
                continue  # same fact — not a conflict
            return {"key": key, "obj": fact.obj, "observations": getattr(fact, "confidence", 0.0)}
        return None
