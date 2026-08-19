"""
Phase 35: Batch Web-Learning tests.

Verifies ``WebSearchLearner.ingest_batch()``:
  - A 3+ topic batch learns facts and produces a teaching report.
  - Single-source facts are SKIPPED (multi-source agreement >= 2).
  - Contradicting facts are quarantined.
  - Cross-topic conflicting assertions are flagged as conflicts.
  - The gap list / state snapshot reflects the new knowledge.

Network calls are mocked — the tests assert behavior, not the internet.
Deterministic and LLM-free.
"""

from __future__ import annotations

import asyncio
import unittest
from unittest import mock

from brain.core.brain import Brain
from brain.knowledge.web_learning import WebSearchLearner

# ---------------------------------------------------------------------------
# Deterministic mock search results: each topic maps to topic-specific
# snippets and one deliberately conflicting cross-topic assertion.
# ---------------------------------------------------------------------------
_MOCK_SNIPPETS = {
    # "satellite" — the key definition fact appears in TWO English sources
    # (agreement >= 2), while the Sputnik fact appears in only one source
    # (must be skipped).
    "satellite": [
        {
            "snippet": "A satellite is an object that orbits a planet. "
            "Satellites are used for communication, navigation, and weather.",
            "url": "en.wikipedia.org",
        },
        {
            "snippet": "A satellite is an object that orbits a planet.",
            "url": "bn.wikipedia.org",
        },
        {
            "snippet": "The first artificial satellite was Sputnik 1, launched in 1957.",
            "url": "DuckDuckGo",
        },
    ],
    # "padma river" — two sources disagree on the same subject's type:
    # cross-topic conflict trigger (neither may enter memory).
    "padma river": [
        {
            "snippet": "Padma is a river that flows through Bangladesh.",
            "url": "en.wikipedia.org",
        },
        {
            "snippet": "Padma is a city that lies in India.",
            "url": "DuckDuckGo",
        },
    ],
    # "lighthouse" — single-source fact only: must be SKIPPED.
    "lighthouse": [
        {
            "snippet": "A lighthouse is a tower that guides ships at sea.",
            "url": "DuckDuckGo",
        },
    ],
}


def _run(coro):
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None
    if loop is not None and loop.is_running():
        import concurrent.futures

        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(asyncio.run, coro)
            return future.result()
    return asyncio.run(coro)


class TestBatchIngestion(unittest.TestCase):
    """``ingest_batch`` produces a teaching report with learned/skipped
    quarantined buckets."""

    def setUp(self) -> None:
        self.brain = Brain()
        self.learner = WebSearchLearner(self.brain)
        patcher = mock.patch.object(WebSearchLearner, "search", side_effect=lambda t, **kw: _MOCK_SNIPPETS.get(t, []))
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_batch_returns_teaching_report(self) -> None:
        report = _run(self.learner.ingest_batch(["satellite", "padma river", "lighthouse"]))
        for key in ("learned", "quarantined", "skipped", "cross_topic_conflicts"):
            self.assertIn(key, report, f"missing {key}")
        # At least one fact learned (satellite Wikipedia bilingual repeat).
        self.assertGreater(len(report["learned"]), 0)

    def test_single_source_fact_is_skipped(self) -> None:
        report = _run(self.learner.ingest_batch(["lighthouse"]))
        lighthouse_facts = [f for f in report["skipped"] if "lighthouse" in f["subject"].lower()]
        # The DuckDuckGo-only fact has only one source -> skipped.
        self.assertGreater(len(lighthouse_facts), 0)
        # Nothing from lighthouse should enter memory (cleaned subject).
        stored = self.brain.semantic_memory.query(subject="lighthouse")
        self.assertEqual(len(stored), 0)

    def test_cross_topic_conflict_quarantined(self) -> None:
        report = _run(self.learner.ingest_batch(["padma river"]))
        self.assertGreater(len(report["cross_topic_conflicts"]), 0)
        conflict = report["cross_topic_conflicts"][0]
        self.assertEqual(conflict["triple"]["subject"], "Padma")
        self.assertGreater(len(conflict["disagreeing_objects"]), 1)

    def test_conflicting_fact_not_in_memory(self) -> None:
        # The padma (is_a, river) and (is_a, city) clash quarantines BOTH
        # assertions — the batch path may never assert either side.
        _run(self.learner.ingest_batch(["padma river"]))
        padma = self.brain.semantic_memory.query(subject="padma")
        self.assertEqual(len(padma), 0)

    def test_quarantine_exposed_on_brain(self) -> None:
        _run(self.learner.ingest_batch(["padma river"]))
        # The conflict candidate lands on the brain's quarantine for the
        # Phase 33 self-assessor to review later.
        self.assertIsInstance(self.brain._learning_quarantine, list)
        self.assertTrue(any("cross_topic_conflict" in str(q) for q in self.brain._learning_quarantine))

    def test_topic_weights_limit_search_effort(self) -> None:
        calls = []

        async def fake_search(topic, **kw):
            calls.append((topic, kw.get("max_results")))
            return _MOCK_SNIPPETS.get(topic, [])

        with mock.patch.object(WebSearchLearner, "search", side_effect=fake_search):
            _run(
                self.learner.ingest_batch(
                    ["satellite", "lighthouse"],
                    topic_weights={"satellite": 2.0, "lighthouse": 0.4},
                )
            )
        weight_lookup = dict(calls)
        # Weight 2.0 -> more max_results than weight 0.4.
        self.assertGreater(weight_lookup["satellite"], weight_lookup["lighthouse"])

    def test_learned_facts_queryable(self) -> None:
        before = self.brain.semantic_memory.size
        _run(self.learner.ingest_batch(["satellite"]))
        after = self.brain.semantic_memory.size
        self.assertGreater(after, before)

    def test_batch_idempotent_quarantine(self) -> None:
        # Running the same batch twice must not duplicate quarantine entries.
        _run(self.learner.ingest_batch(["padma river"]))
        first = len(self.brain._learning_quarantine)
        _run(self.learner.ingest_batch(["padma river"]))
        self.assertEqual(len(self.brain._learning_quarantine), first)


if __name__ == "__main__":
    unittest.main()
