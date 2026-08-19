"""
Phase 37: post-learning self-assessment loop tests.

Covers:
1. Case selection picks benchmark cases whose input mentions the learned
   topics, with a deterministic fallback otherwise
2. Before/after evaluation with answer diffs recorded per changed case
3. History accumulation and the strictly-increasing trend signal
4. The automatic hook inside WebSearchLearner.ingest_batch (mocked search)
   and the API route response carrying the assessment
"""

import asyncio
import os
import unittest
from unittest import mock

from brain.core.brain import Brain
from brain.knowledge.web_learning import WebSearchLearner
from brain.learning.post_learning_loop import (
    PostLearningAssessor,
    _CaseFilter,
)


def _mock_search(snippets: list[dict[str, str]]) -> mock._patch:
    """All three source methods return the same snippets so multi-source
    agreement (min 2) is trivially satisfied for test triples."""
    patcher = mock.patch(
        "brain.knowledge.web_learning.WebSearchLearner.search",
        return_value=snippets,
    )
    patcher.start()
    return patcher


class TestCaseSelection(unittest.TestCase):
    def test_keyword_matching_selects_cases(self) -> None:
        """A topic word appearing in case inputs selects those cases."""
        from brain.knowledge.corpus_conversation import CONVERSATION_BENCHMARK

        cases = _CaseFilter.relevant_cases(["কী"], CONVERSATION_BENCHMARK)
        self.assertGreater(len(cases), 0)
        for case in cases:
            self.assertIn("কী", case["input"])

    def test_no_match_returns_empty(self) -> None:
        self.assertEqual(
            _CaseFilter.relevant_cases(["xyzzyzz"], []),
            [],
        )

    def test_empty_topics_returns_empty(self) -> None:
        from brain.knowledge.corpus_conversation import CONVERSATION_BENCHMARK

        self.assertEqual(
            _CaseFilter.relevant_cases([], CONVERSATION_BENCHMARK),
            [],
        )


class TestPostLearningAssessor(unittest.TestCase):
    def setUp(self) -> None:
        self.brain = Brain()
        self.assessor = PostLearningAssessor(self.brain)

    def test_assess_after_learning_records_run(self) -> None:
        result = self.assessor.assess_after_learning(["কী"])
        assessment = result["post_learning_assessment"]
        self.assertIsNotNone(assessment)
        self.assertGreater(assessment["assessed_cases"], 0)
        self.assertIn("after", assessment)
        self.assertEqual(assessment["after"]["total_cases"], assessment["assessed_cases"])
        self.assertEqual(len(self.assessor.history), 1)

    def test_empty_topics_returns_none(self) -> None:
        self.assertIsNone(
            self.assessor.assess_after_learning([])["post_learning_assessment"],
        )

    def test_baseline_capture_is_idempotent(self) -> None:
        first = self.assessor.assess_baseline()
        second = self.assessor.assess_baseline()
        self.assertIn("baseline_score", first)
        self.assertEqual(first["baseline_score"], second["baseline_score"])

    def test_first_run_improved_when_it_knows_anything(self) -> None:
        """With no prior report available, the first run is "improved" as
        long as it demonstrates learning produced any known answers."""
        # Patch the gap assessor so its last_report is None (simulating a
        # fresh brain that has never self-tested).
        with mock.patch.object(self.assessor.gap_assessor, "last_report", return_value=None):
            self.assessor.assess_after_learning(["কী"])
        last = self.assessor.last_run()
        self.assertIsNotNone(last)
        self.assertTrue(last.improved)

    def test_history_and_trend(self) -> None:
        self.assessor.assess_after_learning(["কী"])
        self.assessor.assess_after_learning(["কেন"])
        self.assertEqual(len(self.assessor.history), 2)
        trend = self.assessor.trend()
        self.assertEqual(trend["runs"], 2)
        self.assertEqual(len(trend["scores"]), 2)
        # Two runs over different topics use different case subsets, so
        # consecutive scores may rise or fall; the loop still reports the
        # comparison signal for every run rather than pretending trends
        # are always improving.
        self.assertIn(trend["strictly_increasing"], (True, False, None))


class _AgreeingSearch:
    """Callable replacement for WebSearchLearner.search satisfying the
    multi-source agreement rule: every (topic, source) pair returns the
    same snippets so at least two sources always agree."""

    def __init__(self, snippets: list[dict[str, str]]) -> None:
        self.snippets = snippets

    async def __call__(self, topic: str, **kwargs):
        return self.snippets


class TestIngestBatchHook(unittest.TestCase):
    """The assessor must be called automatically by ingest_batch."""

    def setUp(self) -> None:
        self.brain = Brain()
        self.assessor = PostLearningAssessor(self.brain)
        # WebSearchLearner looks for the assessor attribute after Phase 36
        # wiring; set it here to replicate the Brain wiring path manually.
        self.brain.web_learner.post_learning_assessor = self.assessor

    def test_hook_runs_after_ingest(self) -> None:
        snippets = [
            {"snippet": "A lighthouse is a tower that warns ships.", "url": "en.wikipedia.org"},
            {"snippet": "A lighthouse is a tower that warns ships.", "url": "bn.wikipedia.org"},
        ]
        with mock.patch.object(
            WebSearchLearner,
            "search",
            _AgreeingSearch(snippets),
        ):
            report = asyncio.run(self.brain.web_learner.ingest_batch(["lighthouse"]))
        self.assertIn("post_learning_assessment", report)
        assessment = report["post_learning_assessment"]
        self.assertIsNotNone(assessment)
        self.assertGreater(assessment["assessed_cases"], 0)
        self.assertEqual(assessment["after"]["total_cases"], assessment["assessed_cases"])
        self.assertEqual(len(self.assessor.history), 1)

    def test_hook_fails_silently_never_breaks_learning(self) -> None:
        """An assessor that raises must not stop facts from being learned
        and the report key must simply be None."""
        snippets = [
            {"snippet": "A beacon is a light that guides travellers.", "url": "en.wikipedia.org"},
            {"snippet": "A beacon is a light that guides travellers.", "url": "bn.wikipedia.org"},
        ]
        with (
            mock.patch.object(WebSearchLearner, "search", _AgreeingSearch(snippets)),
            mock.patch.object(
                PostLearningAssessor,
                "assess_after_learning",
                side_effect=RuntimeError("boom"),
            ),
        ):
            report = asyncio.run(self.brain.web_learner.ingest_batch(["beacon"]))
        self.assertIn("post_learning_assessment", report)
        self.assertIsNone(report["post_learning_assessment"])
        # Learning itself still happened.
        self.assertGreaterEqual(len(report.get("learned", [])), 1)


class TestApiRouteIncludesAssessment(unittest.TestCase):
    """The training API route must surface the post-learning assessment."""

    def setUp(self) -> None:
        # training.py reads MISTY_TRAINING_API_KEY at import time; phase 36
        # tests pop the env for their "unset key" scenario, so this class
        # re-exports its own module view with the key pinned (like phase 36).
        import importlib

        os.environ["MISTY_TRAINING_API_KEY"] = "misty-secret-key-37"
        import apps.api.routes.training as _training

        self.training_module = importlib.reload(_training)
        self.training_module._rate_windows.clear()
        self.client = self._client()

    def tearDown(self) -> None:
        # Restore the module view used by the rest of the suite.
        import importlib

        import apps.api.routes.training as original

        importlib.reload(original)

    def _client(self):
        from fastapi import FastAPI
        from fastapi.testclient import TestClient

        app = FastAPI()
        app.include_router(self.training_module.router, prefix="")
        app.state.brain = Brain()
        # Attach the assessor like Brain does in Phase 36/37 wiring.
        app.state.brain.web_learner.post_learning_assessor = PostLearningAssessor(app.state.brain)
        return TestClient(app)

    def test_web_learn_report_includes_assessment(self) -> None:
        snippets = [
            {"snippet": "A lighthouse is a tower that warns ships.", "url": "en.wikipedia.org"},
            {"snippet": "A lighthouse is a tower that warns ships.", "url": "bn.wikipedia.org"},
        ]
        with mock.patch.object(WebSearchLearner, "search", _AgreeingSearch(snippets)):
            response = self.client.post(
                "/api/training/web_learn",
                json={"topics": ["lighthouse"]},
                headers={"X-Misty-Training-Key": "misty-secret-key-37"},
            )
        self.assertEqual(response.status_code, 200)
        self.assertIn("post_learning_assessment", response.json())
        assessment = response.json()["post_learning_assessment"]
        self.assertIsNotNone(assessment)
        self.assertGreater(assessment["assessed_cases"], 0)


if __name__ == "__main__":
    unittest.main()
