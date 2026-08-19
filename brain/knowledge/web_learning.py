"""
Web-Search Learning Pipeline for MISTY.

Answers the question "Can Misty learn from the web?". Yes — but not with an
LLM sitting at runtime. Instead the pipeline is deterministic and
safety-gated:

1. ``WebSearchLearner.search(topic)`` collects trusted-source summaries:
   the DuckDuckGo Instant Answer API plus the Bengali and English Wikipedia
   summary APIs. These sources return structured abstracts, avoiding the
   bot-blocking that plagues generic HTML scraping.
2. ``WebSearchLearner.extract_facts(text)`` parses candidate sentences into
   (subject, predicate, object) triples using copula heuristics only. No
   external AI model is involved.
3. ``WebSearchLearner.ingest(topic, ...)`` filters every candidate through
   ``evaluate_learning()``: provenance is mandatory, contradicting facts
   are quarantined, and only facts above the confidence threshold enter
   the brain's semantic memory.

Because the pipeline is an agent-side ingestion tool (not the chat
runtime), a live chat message can never inject web content into the
brain — the chat path never calls this module.

Usage (designer-side training run):
    learner = WebSearchLearner(brain)
    result = await learner.ingest("satellite")
    print(result.facts_learned, result.decisions)
"""

from __future__ import annotations

import json
import re
import ssl
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from typing import Any, Dict, List, Sequence, Tuple

from brain.safety.policy import Decision, evaluate_learning

# Stop words that must not become triple heads or tails.
_EN_STOP = {
    "a",
    "an",
    "the",
    "is",
    "are",
    "was",
    "were",
    "be",
    "of",
    "in",
    "to",
    "for",
    "on",
    "and",
    "or",
    "it",
    "that",
    "this",
    "with",
    "from",
    "by",
    "as",
    "at",
    "which",
    "but",
    "not",
    "no",
    "so",
    "if",
    "then",
    "than",
}
_BN_STOP = {"এর", "র", "এ", "যে", "ও", "বা", "না", "নি"}

# Copula verbs that signal "X is Y" definitions.
_COPULAS = re.compile(r"\b(is|are|was|were|means|refers to)\b", re.IGNORECASE)

# Sentence enders (English "." and Bengali "।").
_SENT_END = re.compile(r"([.!])\s+")

_WIKI_USER_AGENT = "Misty-Web-Learner/1.0 (educational knowledge acquisition)"


@dataclass
class WebLearningCandidate:
    """A triple candidate harvested from a search result."""

    subject: str
    predicate: str
    obj: str
    confidence: float = 0.7
    observations: int = 1
    source_ref: str = ""
    contradicts_existing: bool = False


@dataclass
class WebLearningResult:
    """Aggregate result of a web-learning run."""

    topic: str
    queries_run: int = 0
    facts_learned: list = field(default_factory=list)
    decisions: list = field(default_factory=list)
    quarantined: list = field(default_factory=list)


class WebSearchLearner:
    """Deterministic web-search -> triple -> safety-gate learning pipeline."""

    def __init__(self, brain: Any, user_agent: str = _WIKI_USER_AGENT) -> None:
        self.brain = brain
        self._user_agent = user_agent
        # Phase 42: second-layer fact verification — every ALLOW'd candidate
        # is checked for multi-source corroboration and internal
        # consistency before it enters semantic memory.
        from brain.learning.fact_verification import FactVerifier

        self.fact_verifier = FactVerifier(brain)
        ctx = ssl.create_default_context()
        self._opener = urllib.request.build_opener(
            urllib.request.HTTPSHandler(context=ctx),
        )

    # ------------------------------------------------------------------
    # Search: trusted structured sources
    # ------------------------------------------------------------------

    async def search(self, topic: str, *, max_results: int = 6) -> list[dict[str, str]]:
        """Collect {snippet, url} pairs from trusted APIs.

        Uses DuckDuckGo Instant Answer (JSON) and Wikipedia REST summaries
        in both Bengali and English. Returns at most ``max_results`` unique
        snippets.
        """
        snippets: list[dict[str, str]] = []
        self._collect(snippets, await self._ddg_instant(topic))
        self._collect(snippets, await self._wiki_summary(topic, lang="bn"))
        self._collect(snippets, await self._wiki_summary(topic, lang="en"))
        return snippets[:max_results]

    def _collect(self, snippets: list[dict[str, str]], items: list[dict[str, str]]) -> None:
        for item in items:
            if (
                item["snippet"]
                and len(item["snippet"]) > 15
                and not any(item["snippet"] == existing["snippet"] for existing in snippets)
            ):
                snippets.append(item)

    async def _ddg_instant(self, query: str) -> list[dict[str, str]]:
        params = urllib.parse.urlencode({"q": query})
        url = f"https://api.duckduckgo.com/?{params}&format=json&no_html=1"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": self._user_agent})
            with self._opener.open(req, timeout=15) as response:
                data = json.loads(response.read().decode("utf-8", errors="replace"))
        except Exception:
            return []
        abstract = (data.get("Abstract") or "").strip()
        if not abstract:
            return []
        url = "DuckDuckGo"
        return [{"snippet": abstract, "url": url}]

    async def _wiki_summary(self, topic: str, lang: str) -> list[dict[str, str]]:
        url = f"https://{lang}.wikipedia.org/api/rest_v1/page/summary/{urllib.parse.quote(topic)}"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": self._user_agent})
            with self._opener.open(req, timeout=15) as response:
                data = json.loads(response.read().decode("utf-8", errors="replace"))
        except Exception:
            return []
        extract = (data.get("extract") or "").strip()
        if not extract:
            return []
        return [{"snippet": extract, "url": f"wikipedia.org ({lang})"}]

    # ------------------------------------------------------------------
    # Extraction: sentence -> triple
    # ------------------------------------------------------------------

    @staticmethod
    def extract_facts(text: str) -> list[dict[str, str]]:
        """Turn candidate sentences into (subject, predicate, object) triples.

        Only copula-defining sentences ("X is Y") produce triples; everything
        else is ignored rather than guessed.
        """
        triples: list[dict[str, str]] = []
        for sentence in _SENT_END.split(text):
            sentence = sentence.strip()
            if len(sentence) < 5:
                continue
            match = _COPULAS.search(sentence)
            if not match:
                continue
            subject = sentence[: match.start()].strip()
            obj = sentence[match.end() :].strip()
            subject, obj = WebSearchLearner._clean(subject), WebSearchLearner._clean(obj)
            if not subject or not obj:
                continue
            triples.append({"subject": WebSearchLearner._first_alternative(subject), "predicate": "is_a", "obj": obj})
        return triples

    @staticmethod
    def _clean(text: str) -> str:
        text = re.sub(r"\s+", " ", text).strip()
        if not text or text.lower() in _EN_STOP or text in _BN_STOP:
            return ""
        return text

    # ------------------------------------------------------------------
    # Helpers used inside extraction
    # ------------------------------------------------------------------

    @staticmethod
    def _first_alternative(subject: str) -> str:
        """ "A satellite or an artificial satellite" -> "A satellite".

        Copula definitions often repeat a near-synonym ("X or an artificial
        X is ..."); the shorter head phrase is the cleaner subject.
        """
        if " or " in subject:
            return subject.split(" or ", 1)[0].strip()
        return subject

    # ------------------------------------------------------------------
    # Contradiction check against the brain's existing knowledge
    # ------------------------------------------------------------------

    def _contradicts_existing(self, candidate: WebLearningCandidate) -> bool:
        facts = getattr(self.brain.semantic_memory, "facts", {})
        lower_obj = candidate.obj.lower()
        for key, fact in facts.items():
            if not key.lower().startswith(candidate.subject.lower()):
                continue
            if fact.predicate == candidate.predicate and fact.obj.lower() != lower_obj:
                return True
        return False

    # ------------------------------------------------------------------
    # Ingestion
    # ------------------------------------------------------------------

    async def ingest(self, topic: str, *, max_facts: int = 6) -> WebLearningResult:
        """Search for ``topic``, extract triples, gate them, and learn.

        Only candidates approved by ``evaluate_learning()`` (provenance,
        confidence threshold, no contradictions) enter semantic memory.
        """
        result = WebLearningResult(topic=topic)
        sources = await self.search(topic)
        result.queries_run = len(sources)

        # Two-pass ingestion: first collect every triple with the list of
        # supporting source URLs (multi-source agreement raises the
        # observations count so ``evaluate_learning`` allows it), then gate
        # and store.
        support: dict[tuple[str, str], dict[str, Any]] = {}
        for source in sources:
            seen_in_source: set[tuple[str, str]] = set()
            for triple in self.extract_facts(source["snippet"]):
                triple_key = (triple["subject"].lower(), triple["obj"].lower())
                if triple_key in seen_in_source:
                    continue
                seen_in_source.add(triple_key)
                entry = support.setdefault(
                    triple_key,
                    {"subject": triple["subject"], "predicate": triple["predicate"], "obj": triple["obj"], "urls": []},
                )
                if source.get("url") and source["url"] not in entry["urls"]:
                    entry["urls"].append(source["url"])

        for entry in support.values():
            if len(result.facts_learned) >= max_facts:
                break
            candidate = WebLearningCandidate(
                subject=entry["subject"],
                predicate=entry["predicate"],
                obj=entry["obj"],
                confidence=0.8,
                source_ref=", ".join(entry["urls"]),
                observations=len(entry["urls"]),
            )
            candidate.contradicts_existing = self._contradicts_existing(candidate)
            decision = evaluate_learning(
                {
                    "confidence": candidate.confidence,
                    "observations": candidate.observations,
                    "source_ref": candidate.source_ref,
                    "contradicts_existing": candidate.contradicts_existing,
                }
            )
            result.decisions.append(
                {
                    "triple": {
                        "subject": candidate.subject,
                        "predicate": candidate.predicate,
                        "obj": candidate.obj,
                    },
                    "decision": decision.decision.value,
                    "reason": decision.reason,
                }
            )
            if decision.decision is Decision.ALLOW:
                # Phase 42: verify before committing — corroboration and
                # conflict checks may retract older facts or lower the
                # confidence of a single-source candidate.
                if candidate.contradicts_existing:
                    verdict, _reason, confidence_after = self._verify_and_resolve(candidate)
                    if verdict == "retracted":
                        result.quarantined.append(candidate)
                        continue
                    candidate.confidence = confidence_after
                else:
                    _verdict, _reason, confidence_after = self._verify_and_resolve(candidate)
                    candidate.confidence = confidence_after
                self.brain.semantic_memory.store_fact(
                    subject=candidate.subject,
                    predicate=candidate.predicate,
                    obj=candidate.obj,
                    confidence=candidate.confidence,
                    source="web_learning",
                )
                result.facts_learned.append(candidate)
            else:
                result.quarantined.append(candidate)
        return result

    # ------------------------------------------------------------------
    # Phase 42: second-layer verification (corroboration + conflict)
    # ------------------------------------------------------------------

    def _verify_and_resolve(self, candidate: WebLearningCandidate) -> Tuple[str, str, float]:
        """Run the Phase 42 verifier on one candidate and resolve any
        conflict with the brain's own knowledge.

        Returns (verdict, reason, confidence_after).
        """
        entry = self.fact_verifier.verify_triple(
            subject=candidate.subject,
            predicate=candidate.predicate,
            obj=candidate.obj,
            source_ref=candidate.source_ref,
            observations=candidate.observations,
        )
        return entry.verdict, entry.reason, entry.confidence_after or candidate.confidence

    # ------------------------------------------------------------------
    # Phase 35: batch ingestion with topic weights and conflict detection
    # ------------------------------------------------------------------

    async def ingest_batch(
        self,
        topics: Sequence[str],
        topic_weights: Dict[str, float] | None = None,
        *,
        min_agreement_sources: int = 2,
        max_facts_per_topic: int = 6,
    ) -> Dict[str, Any]:
        """Learn several topics in one batch (Phase 35).

        * ``topics``: topics to learn. ``topic_weights`` (optional) scales
          the per-topic ``max_facts`` ceiling and search effort; a weight
          below 1.0 is treated as "browse, but keep it lean".
        * Stricter multi-source agreement: a fact now needs at least
          ``min_agreement_sources`` (default 2) independent sources
          before it may enter memory.
        * Cross-topic conflict detection: the same candidate seen across
          different topics with disagreeing objects is quarantined and
          flagged, even if each single topic saw one source.
        * Teaching report: returns a dict with ``learned``, ``quarantined``,
          and ``skipped`` per topic plus the aggregate conflict list.
        """
        if isinstance(min_agreement_sources, bool) or not isinstance(min_agreement_sources, int):
            raise TypeError("min_agreement_sources must be an integer")
        if min_agreement_sources < 1:
            raise ValueError("min_agreement_sources must be at least 1")
        normalized_topics = [topic.strip() for topic in topics if topic.strip()]
        weights = topic_weights or {}
        teaching_report: Dict[str, Any] = {
            "topics": normalized_topics,
            "cross_topic_conflicts": [],
            "assessment_config": {"min_agreement_sources": min_agreement_sources},
        }

        # Phase 1: collect (subject, predicate, object) -> list of urls
        # across ALL topics, grouped by (subject, predicate) so that
        # cross-topic conflicts (same subject+predicate, different objects)
        # and multi-source agreement (same subject+obj, >=2 urls) can both
        # be computed on the merged pool.
        support: Dict[Tuple[str, str], Dict[str, Any]] = {}
        for topic in normalized_topics:
            weight = max(float(weights.get(topic, 1.0)), 0.1)
            ceiling = max(1, int(max_facts_per_topic * weight))
            # Weight-aware search effort: high-weight topics consult more
            # sources; low-weight topics stay lean.
            sources = await self.search(topic, max_results=ceiling)
            seen_in_topic: set[tuple[str, str, str]] = set()
            for source in sources:
                for triple in self.extract_facts(source["snippet"]):
                    _obj_key = triple["obj"].lower().rstrip(". ,;:!?\u0964").strip()
                    triple_key = (
                        triple["subject"].lower(),
                        triple["predicate"].lower(),
                        _obj_key,
                    )
                    group_key = (triple["subject"].lower(), triple["predicate"].lower())
                    if group_key in support:
                        # Already tracked this (subject, predicate) from an
                        # earlier source — reuse the group and record the
                        # source url / topic for agreement counting.
                        entry = support[group_key]
                        entry["obj_by_key"].setdefault(_obj_key, triple["obj"])
                        if source.get("url") and source["url"] not in entry["urls"]:
                            entry["urls"].append(source["url"])
                        if topic not in entry["topics"]:
                            entry["topics"].append(topic)
                        continue
                    if triple_key in seen_in_topic:
                        continue
                    seen_in_topic.add(triple_key)
                    entry = support.setdefault(
                        group_key,
                        {
                            "subject": triple["subject"],
                            "predicate": triple["predicate"],
                            "obj_by_key": {},
                            "urls": [],
                            "topics": [],
                        },
                    )
                    entry["obj_by_key"].setdefault(_obj_key, triple["obj"])
                    if source.get("url") and source["url"] not in entry["urls"]:
                        entry["urls"].append(source["url"])
                    if topic not in entry["topics"]:
                        entry["topics"].append(topic)
        # Phase 2: cross-topic conflict gate, then multi-source agreement.
        learned: List[Dict[str, Any]] = []
        pending_commits: List[tuple[WebLearningCandidate, Dict[str, Any]]] = []
        quarantined: List[Dict[str, Any]] = []
        skipped: List[Dict[str, Any]] = []
        conflicts: List[Dict[str, Any]] = []
        for entry in support.values():
            base_triple = {
                "subject": entry["subject"],
                "predicate": entry["predicate"],
            }
            canonical_objs = list(entry["obj_by_key"].values())
            if len(canonical_objs) > 1:
                # Same (subject, predicate) asserted with different objects
                # across topics -> cross-topic conflict: NONE of the
                # competing assertions may enter memory.
                conflicts.append(
                    {
                        "triple": {**base_triple, "obj": canonical_objs[0]},
                        "disagreeing_objects": canonical_objs,
                        "topics": entry["topics"],
                        "urls": entry["urls"],
                    }
                )
                quarantined.extend(
                    {
                        **base_triple,
                        "obj": obj,
                        "confidence": 0.5,
                        "observations": 0,
                        "source_ref": "web_search",
                        "topics": entry["topics"],
                        "quarantine_reason": "cross_topic_conflict",
                    }
                    for obj in canonical_objs
                )
                continue
            obj = canonical_objs[0]
            triple = {**base_triple, "obj": obj}
            urls = entry["urls"]
            if len(urls) < min_agreement_sources:
                skipped.append(
                    {
                        **triple,
                        "observations": len(urls),
                        "required_agreement_sources": min_agreement_sources,
                        "topics": entry["topics"],
                        "skip_reason": "insufficient_source_agreement",
                    }
                )
                continue
            candidate = WebLearningCandidate(
                subject=entry["subject"],
                predicate=entry["predicate"],
                obj=obj,
                confidence=0.8,
                source_ref=", ".join(urls),
                observations=len(urls),
            )
            candidate.contradicts_existing = self._contradicts_existing(candidate)
            decision = evaluate_learning(
                {
                    "confidence": candidate.confidence,
                    "observations": candidate.observations,
                    "source_ref": candidate.source_ref,
                    "contradicts_existing": candidate.contradicts_existing,
                }
            )
            record = {
                **triple,
                "confidence": candidate.confidence,
                "observations": candidate.observations,
                "source_ref": candidate.source_ref,
                "topics": entry["topics"],
            }
            if decision.decision is Decision.ALLOW:
                pending_commits.append((candidate, record))
            else:
                record["quarantine_reason"] = decision.reason
                quarantined.append(record)

        # Phase 3: register quarantine on the brain for Phase 33 review.
        brain_quarantine = getattr(self.brain, "_learning_quarantine", None)
        if isinstance(brain_quarantine, list):
            for q in quarantined:
                triple_key = (q["subject"].lower(), q["obj"].lower())
                if not any(
                    (existing.get("subject", "").lower(), existing.get("obj", "").lower()) == triple_key
                    for existing in brain_quarantine
                ):
                    brain_quarantine.append(q)

        # Capture the matched baseline before the first candidate fact is
        # committed. Assessment failures never block the learning commit.
        assessor = getattr(self, "post_learning_assessor", None)
        prepared_assessment = None
        assessment_failed = False
        if assessor is not None and pending_commits:
            try:
                prepared_assessment = assessor.prepare_assessment(
                    normalized_topics,
                    min_agreement_sources=min_agreement_sources,
                )
            except Exception:
                assessment_failed = True

        for candidate, record in pending_commits:
            fact_key = f"{candidate.subject}:{candidate.predicate}:{candidate.obj}"
            if fact_key in self.brain.semantic_memory.facts:
                skipped.append({**record, "skip_reason": "already_present"})
                continue
            try:
                self.brain.semantic_memory.store_fact(
                    subject=candidate.subject,
                    predicate=candidate.predicate,
                    obj=candidate.obj,
                    confidence=candidate.confidence,
                    source="web_learning_batch",
                )
            except Exception:
                skipped.append({**record, "skip_reason": "commit_failed"})
                continue
            learned.append(record)

        teaching_report["learned"] = learned
        teaching_report["quarantined"] = quarantined
        teaching_report["skipped"] = skipped
        teaching_report["cross_topic_conflicts"] = conflicts
        teaching_report["committed_facts"] = len(learned)

        if assessor is not None:
            if not learned:
                teaching_report["post_learning_assessment"] = None
                teaching_report["assessment_status"] = "skipped_no_ingestion"
            elif assessment_failed or prepared_assessment is None:
                teaching_report["post_learning_assessment"] = None
                teaching_report["assessment_status"] = "baseline_failed"
            else:
                try:
                    teaching_report.update(
                        assessor.assess_after_learning(
                            normalized_topics,
                            min_agreement_sources=min_agreement_sources,
                            prepared=prepared_assessment,
                            committed_facts=len(learned),
                            committed_records=learned,
                        )
                    )
                    teaching_report["assessment_status"] = "completed"
                except Exception:  # assessment must never break learning
                    teaching_report["post_learning_assessment"] = None
                    teaching_report["assessment_status"] = "post_assessment_failed"
        return teaching_report
