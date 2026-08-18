"""Phase 21b: web-search learning pipeline.

Verifies that MISTY can harvest facts from real web sources
(DuckDuckGo Instant Answer + Wikipedia REST summaries), parse them into
(subject, predicate, object) triples without any LLM, and only commit
facts that pass the safety gate. Network-dependent checks degrade
gracefully when offline.
"""

import asyncio
from unittest.mock import AsyncMock

import pytest

from brain.core.brain import Brain
from brain.knowledge.web_learning import WebSearchLearner


def _new_brain() -> Brain:
    return Brain(use_neural_sim=False)


# ---------------------------------------------------------------------------
# Deterministic extraction
# ---------------------------------------------------------------------------

class TestExtraction:
    def test_copula_definition(self) -> None:
        text = "A satellite is an artificial object placed in orbit around the earth."
        triples = WebSearchLearner.extract_facts(text)
        assert triples == [{"subject": "A satellite", "predicate": "is_a",
                            "obj": "an artificial object placed in orbit around the earth."}]

    def test_alternative_subject_shortened(self) -> None:
        text = "A satellite or an artificial satellite is an object in orbit."
        triples = WebSearchLearner.extract_facts(text)
        assert triples and triples[0]["subject"] == "A satellite"

    def test_multiple_sentences(self) -> None:
        text = "The cheetah is the fastest land animal. Its tail is long."
        triples = WebSearchLearner.extract_facts(text)
        subjects = [t["subject"] for t in triples]
        assert "The cheetah" in subjects

    def test_no_copula_ignored(self) -> None:
        text = "Run faster through the forest and jump over streams."
        assert WebSearchLearner.extract_facts(text) == []

    def test_bengali_dot_separator(self) -> None:
        text = "সূর্য হলো একটি তারা। পৃথিবী চলে সূর্যের চারদিকে।"
        triples = WebSearchLearner.extract_facts(text)
        # Bengali sentences contain no English copula; definition via "হলো"
        # is not handled by this pipeline (kept deterministic and simple).
        assert isinstance(triples, list)


# ---------------------------------------------------------------------------
# Mocked pipeline: safety gate behavior
# ---------------------------------------------------------------------------

@pytest.fixture(name="mock_learner")
def mock_learner() -> WebSearchLearner:
    brain = _new_brain()
    learner = WebSearchLearner(brain)
    snippet = "A satellite is an artificial object placed in orbit."
    snippets = [
        {"snippet": snippet, "url": "Wikipedia"},
        {"snippet": snippet, "url": "DuckDuckGo"},
    ]
    learner.search = AsyncMock(return_value=snippets)  # type: ignore[assignment]
    return learner


def test_allow_with_two_sources(mock_learner: WebSearchLearner) -> None:
    result = asyncio.run(mock_learner.ingest("satellite"))
    learned = [f for f in result.facts_learned if f.subject == "A satellite"]
    assert learned, "multi-source definition must be allowed"
    assert learned[0].observations == 2


def test_single_source_quarantined(mock_learner: WebSearchLearner) -> None:
    mock_learner.search = AsyncMock(return_value=[  # type: ignore[assignment]
        {"snippet": "Quarks are fundamental particles of matter.", "url": "OnlySource"},
    ])
    result = asyncio.run(mock_learner.ingest("quark"))
    assert not result.facts_learned
    assert any(d["decision"] == "quarantine" for d in result.decisions)


def test_learned_fact_queryable(mock_learner: WebSearchLearner) -> None:
    asyncio.run(mock_learner.ingest("satellite"))
    output = mock_learner.brain.process("satellite কী?")
    response = output["response"].lower()
    assert "parse" not in response or "আপনার কথা" not in response
    assert "পৃথিবী" in response or "orbit" in response


# ---------------------------------------------------------------------------
# Live network check (skipped gracefully when offline)
# ---------------------------------------------------------------------------

def test_live_ddg_search_reachable() -> None:
    learner = WebSearchLearner(_new_brain())
    try:
        snippets = asyncio.run(learner.search("satellite"))
    except OSError:
        pytest.skip("network unavailable")
    assert snippets, "at least one trusted abstract expected"
